## PPP
import json
import requests
import legodb

HEADER={'Accept': 'application/json','Authorization': 'key 3627574675ff94d3f186dc26e6d8a038'}
ldb=legodb.LegoDb()

def getdata(num):
    sett={}
    si=json.loads(requests.get('https://rebrickable.com/api/v3/lego/sets/'+num+'/',headers=HEADER).text)
    if 'detail' in si:
        #print('Set',num,':',si['detail'])
        return False
    else:
        sett['setid']=num
        sett['setname']=si['name']
        pp=json.loads(requests.get('https://rebrickable.com/api/v3/lego/sets/'+num+'/parts/',headers=HEADER).text)
        sett['nparts']=sum([x['quantity'] for x in pp['results'] if not x['is_spare']])
        sett['nspares']=sum([x['quantity'] for x in pp['results']])-sett['nparts']
        return sett

def ppp(num,price):
    pp=ldb.setInfo(num)
    base=price*100/pp[3]
    wspares=price*100/(pp[3]+pp[4])
    return [num,price,base,wspares,pp[2],pp[3]]

def d(num,price):
    if ldb.setInfo(num)==False:
        try:
            sd=getdata(num)
        except:
            return ["There's an error with the API connection.",]
        if sd==False:
            return ['Wrong id?',]
        else:
            ldb.addSet(sd['setid'],sd['setname'],sd['nparts'],sd['nspares'])
    p= ppp(num, price)
    return ['['+p[0]+'] '+p[4]+' - '+str(p[5])+'pcs',
            'for £{:.2f}'.format(p[1])+' is',
            '{:.2f}ppp'.format(p[2]),
            '{:.2f}ppp'.format(p[3])+' (with spares)']


## SPLTN
import splatdb
sdb=splatdb.SplatDb()

import ptimedb

##
## FLASK
import datetime
import glob
import markdown
import random
from flask import Flask, Markup, Response
from flask import render_template, send_from_directory, request, url_for
app = Flask(__name__)
app.config.from_object('config')


from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, IntegerField, DateField
from wtforms.validators import DataRequired

class PTForm(FlaskForm):
    #game=SelectField('Game',coerce=int, validators=[DataRequired()])
    game=StringField('Game', id='game_autocomplete', validators=[DataRequired()])
    platform=SelectField('Platform',coerce=int, validators=[DataRequired()])
    start = DateField('Start', format="%d/%m/%Y", validators=[DataRequired()])
    end = DateField('End', format="%d/%m/%Y", validators=[DataRequired()])
    ptime = IntegerField('PTime', validators=[DataRequired()])

class STForm(FlaskForm):
    sdate = DateField('Date', format="%d/%m/%Y", validators=[DataRequired()])
    stime = StringField('STime', validators=[DataRequired()])

class PTsForm(FlaskForm):
    game=SelectField('Game',coerce=int, validators=[DataRequired()])

class PPPForm(FlaskForm):
    setid = StringField('setid', validators=[DataRequired()])
    price = FloatField('price', validators=[DataRequired()])


@app.route("/", methods=['GET'])
def index():
    return render_template('index.html',
                           title='indexxx',
                           msg=[
                               'Hello, this is a test!',
                               ]
                           )


@app.route("/robots.txt", methods=['GET'])
def static_from_root():
    return send_from_directory('', 'robots.txt')


@app.route("/info", methods=['GET'])
def infopage():
    return json.dumps({'ip':request.environ.get('HTTP_X_REAL_IP', request.remote_addr)})


# ZZZZZ
#    Z
#   Z
#  Z
# ZZZZZ
@app.route("/zong", methods=['GET'])
@app.route("/zong/", methods=['GET'])
@app.route("/zongi", methods=['GET'])
@app.route("/zongi/", methods=['GET'])
def zongpage():
    z='CDEFGAB'
    zz=['left','right']
    zzz='12345'
    zongo=z[random.randint(0,6)]
    zongoo=zz[random.randint(0,1)]+' '+zzz[random.randint(0,4)]

    return render_template('zong.html',
                           zongo=zongo,
                           zongoo=zongoo
                           )


# PPP  TTTTT I M   M EEEE
# P  P   T   I MM MM E
# PPP    T   I M M M EEE
# P      T   I M   M E
# P      T   I M   M EEEE
ptdb=ptimedb.PTimeDb()
GAMES=[x[0] for x in ptdb.list('game')]
ptdb.db.close()

@app.route("/autocomplete", methods=['GET'])
def autocomplete():
    search = request.args.get('term')
    return Response(json.dumps(GAMES), mimetype='application/json')


@app.route("/ptime", methods=['GET'])
@app.route("/ptime/", methods=['GET'])
def ptimepage():
    ptdb=ptimedb.PTimeDb()
    def m(m,l,tot=True):
        if len(l)>m:
            r=l[:m]
        else:
            r=l[:-1]
        if tot:
            r+=l[-1:]
        return r

    mtaim=ptdb.list('playtime',what2={'aggr':'monthly'})
    mpt=ptdb.monthly_table(mtaim)

    l1=m(20,ptdb.top(what2={'years':'0','gameperplatform':''}))
    l2=m(10,ptdb.top(what2={'months':'0','gameperplatform':''}))
    l3=m(10,ptdb.top(what='platform',what2={'years':'0'}),False)
    l4=m(10,ptdb.top(what='platform',what2={'months':'0'}),False)
    l5=m(25,ptdb.top(what2={}))
    l6=m(20,ptdb.top(what='platform',what2={}),False)
    l7=m(20,ptdb.top(what2={'impressions':''}),False)
    now=datetime.datetime.now()
    curryear=now.strftime('%Y')

    tops=[
        {'title':'Top '+str(len(l2)-1)+' games in '+now.strftime('%B')+' '+curryear, 'list': l2},
        {'title':'Top '+str(len(l4))+' platforms in '+now.strftime('%B')+' '+curryear, 'list': l4},
        {'title':'Top '+str(len(l1)-1)+' games in '+curryear, 'list': l1},
        {'title':'Top '+str(len(l3))+' platforms in '+curryear, 'list': l3},
        {'title':'Top '+str(len(l7))+' impressions of all time (well, 2017-)', 'list': l7},
        {'title':'Top '+str(len(l5)-1)+' games of all time (well, 2017-)', 'list': l5},
        {'title':'Top '+str(len(l6))+' platforms of all time (well, 2017-)', 'list': l6},
        ]

    tags=ptdb.toptags()
    ptdb.db.close()
    return render_template('ptime.html',
                           title='ptime',
                           mpt=mpt,
                           tops=tops,
                           tags=tags
                           )


@app.route("/ptime/tags", methods=['GET'])
@app.route("/ptime/tags/", methods=['GET'])
def tagspage():
    ptdb=ptimedb.PTimeDb()
    tmpt = []
    for tag in ptdb.list('tag'):
        ta=ptdb.tagged_as(tag[0])
        ttaim = {}
        for t in ta['game']:
            for tt in ptdb.list('playtime',what2={'game':t,'aggr':'monthly'}):
                if tt[1] in ttaim:
                    ttaim[tt[1]]+=tt[0]
                else:
                    ttaim[tt[1]]=tt[0]
            print(ptdb.nameof('game',t), flush=True)
        ttaim=[(ttaim[x],x) for x in ttaim.keys()]
        tmpt.append((tag[0],ptdb.monthly_table(ttaim)))

    ptdb.db.close()
    return render_template('ptimetags.html',
                           title='ptime tags',
                           tmpt=tmpt,
                           )


@app.route("/ptime/add", methods=['GET', 'POST'])
@app.route("/ptime/add/", methods=['GET', 'POST'])
def ptime_formadd(msg=[]):
    ptdb=ptimedb.PTimeDb()
    form = PTForm()
    #form.game.choices=[(x[2],x[0]) for x in ptdb.list('game')]
    #form.game.choices.insert(0, (0, '---'))
    form.platform.choices=[(x[2],x[0]) for x in ptdb.list('platform')]
    form.platform.choices.insert(0, (0, '---'))
    ptdb.db.close()

    if form.validate_on_submit():
        ptdb=ptimedb.PTimeDb()
        m=ptdb.addPTime(form.game.data,form.platform.data,
                        form.start.data.strftime('%d/%m/%y'),form.end.data.strftime('%d/%m/%y'),
                        form.ptime.data)
        ptdb.db.close()
        if 'duna' in m:
            msg="""<p class="larger">"""+m['duna']+"""</p><br><a href="/ptime/add">+</a>"""
            return msg
        else:
            msg=[m['error'],]
    return render_template('ptform.html',
                           title='add PTime',
                           msg=msg,
                           form=form)


@app.route('/ptime/add_stuff', methods=['POST'])
@app.route('/ptime/add_stuff/', methods=['POST'])
def ptime_jsonadd():
    ptdb=ptimedb.PTimeDb()
    content = request.json
    if 'davidsstuff' in content:
        if content['davidsstuff']=='game' or content['davidsstuff']=='platform' or content['davidsstuff']=='tag':
            if 'toadd' in content and 'name' in content['toadd']:
                r=json.dumps(ptdb.add(content['davidsstuff'],content['toadd']['name']))
            else:
                r='What is this stuff?'
        elif content['davidsstuff']=='tagging':
            if 'totag' in content and 'what' in content['totag'] and 'name' in content['totag'] and 'tag' in content['totag']:
                r=json.dumps(ptdb.tag(content['totag']['what'],content['totag']['name'],content['totag']['tag']))
            else:
                r='What is this stuff?'
        elif content['davidsstuff']=='ptime':
            try:
                ta=content['toadd']
                r=json.dumps(ptdb.addPTime(ta['game'],ta['platform'],ta['start'],ta['end'],ta['ptime']))
            except:
                r='What is this stuff?'
    else:
        #print('baka')
        r='What is this stuff?'
    ptdb.db.close()
    return r


@app.route("/ptime/info", methods=['GET'])
@app.route("/ptime/info/", methods=['GET'])
def ptimeinfopage():
    ptdb=ptimedb.PTimeDb()
    pt=[x[:-1] for x in ptdb.list('playtime')]
    games=[(x[2],x[0]) for x in ptdb.list('game')]
    platforms=[(x[2],x[0]) for x in ptdb.list('platform')]
    tags=[(x[2],x[0]) for x in ptdb.list('tag')]
    ptdb.db.close()
    return render_template('ptimeinfo.html',
                           title='ptime info',
                           pt=pt,
                           games=games,
                           platforms=platforms,
                           tags=tags
                           )


@app.route("/ptime/singl", methods=['GET', 'POST'])
@app.route("/ptime/singl/", methods=['GET', 'POST'])
def ptimesinglpage(msg=[]):
    ptdb=ptimedb.PTimeDb()
    form = PTsForm()
    form.game.choices=[(x[2],x[0]) for x in ptdb.list('game')]
    form.game.choices.insert(0, (0, '---'))
    ptdb.db.close()
    tot=[]
    mpt=''
    pt=[]

    if form.validate_on_submit():
        ptdb=ptimedb.PTimeDb()
        mtaim=ptdb.list('playtime',what2={'game':form.game.data,'aggr':'monthly'})
        mpt=ptdb.monthly_table(mtaim)

        taim=ptdb.list('playtime',what2={'game':form.game.data})
        taim.sort(key=lambda x:x[4], reverse=True)
        pt=[x[:-1] for x in taim]
        tot=ptdb.top(what='platform',what2={'game':form.game.data,'gameperplatform':''})
        ptdb.db.close()

    return render_template('ptsingl.html',
                           title='PTime singl',
                           msg=msg,
                           form=form,
                           tot=tot,
                           mpt=mpt,
                           pt=pt)


@app.route("/ptime/balance", methods=['GET'])
@app.route("/ptime/balance/", methods=['GET'])
def ptimebalancepage():
    ptdb=ptimedb.PTimeDb()
    bal=ptdb.balance()
    ptdb.db.close()

    return render_template('ptimebalance.html',
                           title='ptime balance',
                           bal=bal,
                           )


@app.route("/stime/add", methods=['GET', 'POST'])
@app.route("/stime/add/", methods=['GET', 'POST'])
def stime_formadd(msg=[]):
    form = STForm()
    if form.validate_on_submit():
        ptdb=ptimedb.PTimeDb()
        m=ptdb.addSTime(form.sdate.data.strftime('%d/%m/%y'),
                        form.stime.data)
        ptdb.db.close()
        if 'duna' in m:
            msg="""<p class="larger">"""+m['duna']+"""</p><br><a href="/ptime/add">+</a>"""
            return msg
        else:
            msg=[m['error'],]
    return render_template('stform.html',
                           title='add STime',
                           msg=msg,
                           form=form)


# PPP   PPP   PPP
# P  P  P  P  P  P
# PPP   PPP   PPP
# P     P     P
# P     P     P
@app.route("/ppp", methods=['GET', 'POST'])
def ppppage(msg=[]):
    form = PPPForm()
    if form.validate_on_submit():
        msg=d(form.setid.data,form.price.data)
    return render_template('form.html',
                           title='ppp',
                           msg=msg,
                           form=form)


#  SSS  PPP   L    TTTTT N   N
# S     P  P  L      T   NN  N
#  SS   PPP   L      T   N N N
#    S  P     L      T   N  NN
# SSS   P     LLLL   T   N   N
@app.route("/spltn", methods=['GET'])
def splatoonpage():
    i=sdb.dbInfo()
    return render_template('spltn.html',
                           title='spltn',
                           general=i['general'],
                           battles=i['battles'],
                           queries=i['queries'])

@app.route('/spltn/add_stuff/', methods=['POST'])
def splat_add():
    content = request.json
    if 'davidsstuff' in content:
        if content['davidsstuff']=='query':
            content.pop('davidsstuff')
            return json.dumps(sdb.addSplatQuery(content))
        elif content['davidsstuff']=='battle':
            content.pop('davidsstuff')
            return json.dumps(sdb.addSplatBattle(content))
        else:
            return 'What is this stuff?'
    else:
        #print('baka')
        return 'What is this stuff?'


#  00
# 0  0
# 0  0
# 0  0
#  00
def zro_paging(page,fs):
    if int(page)==0:
        prevp=''
    else:
        prevp=int(page)-1
        prevp=request.url_root[:-1]+url_for("zro")+(5-len(str(prevp)))*'0'+str(prevp)
    if int(page)+1==len(fs):
        nextp=''
    else:
        nextp=int(page)+1
        nextp=request.url_root[:-1]+url_for("zro")+(5-len(str(nextp)))*'0'+str(nextp)
    return [prevp,nextp]


@app.route("/zro/00002", methods=['GET'])
def zro_00002():
    page='00002'
    content=Markup(markdown.markdown(
        '''
        Trade
        ***
        I think I'm seeing a town up ahead. A bustling market town it is indeed.

        What better place to get to know this place and avoid feeling too weird or awkward for not knowing how the locals roll.

        
        '''
        ))
    fs=glob.glob('zro/*.txt')
    prevp,nextp = zro_paging(page,fs)
    return render_template('zro.html',
                           title='(0)',
                           content=content,
                           prevp=prevp,
                           nextp=nextp)


@app.route("/zro/", methods=['GET'])
@app.route("/zro/<page>", methods=['GET'])
def zro(page='00000'):
    import codecs
    fs=glob.glob('zro/*.txt')
    f=codecs.open([x for x in fs if page in x][0], 'r', 'utf-8')
    content = Markup(markdown.markdown(f.read()))
    prevp,nextp = zro_paging(page,fs)

    return render_template('zro.html',
                           title='(0)',
                           content=content,
                           prevp=prevp,
                           nextp=nextp)


if __name__ == "__main__":
        app.run()
