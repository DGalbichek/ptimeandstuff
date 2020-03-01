from calendar import monthrange

import datetime
import itertools
import json
import os
import sqlite3


WHAT = {'game':'games','platform':'platforms','tag':'tags'}
BALANCERATIO = 0.5
DAILYMUSICTARGET = 30


class PTimeDb():
    def __init__(self,dbfile=''):
        self.DBFILE='ptimedb.sqlite'
        self.db = sqlite3.connect(self.DBFILE)
        self.cursor = self.db.cursor()
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS games( id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, dateadded TIMESTAMP);
                ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS platforms( id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, dateadded TIMESTAMP);
                ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags( id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, dateadded TIMESTAMP);
                ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tagassignments( id INTEGER PRIMARY KEY AUTOINCREMENT,
                game INTEGER, platform INTEGER, tag INTEGER NOT NULL,dateadded TIMESTAMP,
                FOREIGN KEY(game) REFERENCES games(id),
                FOREIGN KEY(platform) REFERENCES platforms(id),
                FOREIGN KEY(tag) REFERENCES tags(id));
                ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS playtime( id INTEGER PRIMARY KEY AUTOINCREMENT,
                        game INTEGER NOT NULL,
                        platform INTEGER NOT NULL,
                        t_start TIMESTAMP, t_end TIMESTAMP,
                        dateadded TIMESTAMP NOT NULL,
                        ptime INTEGER NOT NULL,
                        is_cumm BOOLEAN NOT NULL,
                        FOREIGN KEY(game) REFERENCES games(id),
                        FOREIGN KEY(platform) REFERENCES platforms(id));
                ''')
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sleeptime( id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sleepdate TIMESTAMP NOT NULL,
                        sleeptime INTEGER NOT NULL,
                        dateadded TIMESTAMP NOT NULL);
                ''')
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e


    def _value(self,t,sep=' ',timevalue=True):
        if timevalue:
            return ('-' if t<0 else '') + str(int(abs(t)/60))+'h'+sep+str(int(abs(t))%60)+'m'
        else:
            return str(t)


    def _iym(self,ym):
        if ym[-2:]=='12':
            return str(int(ym[:4])+1)+'-01'
        else:
            return ym[:5]+str(int(ym[-2:])+1).zfill(2)


    def monthly_table(self,mtaim,timedata=True,nototal=False):
        mtaim.sort(key=lambda x:x[1])
        if len(mtaim)>0:
            mt=[mtaim[0],]
            # fill holes with 0
            for mta in mtaim:
                if mta not in mt:
                    while self._iym(mt[-1][1])!=mta[1]:
                        mt.append((0,self._iym(mt[-1][1])))
                    mt.append(mta)
            currym=datetime.datetime.now().strftime('%Y-%m')
            # fill with 0 until current month
            while mt[-1][1]!=currym:
                mt.append((0,self._iym(mt[-1][1])))

            ## TABLE
            # header
            mpt="<table><tbody><tr><th></th>"+''.join(['<th>'+str(n)+'</th>' for n in range(1,13)])
            if not nototal:
                mpt+="<th>total</th>"
            mpt+="<th>avg</th></tr>"

            # blank year row(s)
            if mt[0][1][:4]!='2017':
                for y in range(2017,int(mt[0][1][:4])):
                    mpt+="<tr><td><b>"+str(y)+"</b></td>"+'<td style="background:grey;"></td>'*(13 if nototal else 14)

            # blank initial cells
            mpt+="<tr><td><b>"+mt[0][1][:4]+"</b></td>"
            for nn in range(1,int(mt[0][1][-2:])):
                mpt+='<td style="background:grey;"></td>'

            #yearly data
            #ydat=[x[0] for x in mt if x[1][:4]==mt[0][1][:4]]
            #ytot=sum(ydat)
            #yavg=int(sum(ydat)/len(ydat)) if ytot>0 else 0


            # months with data buildup
            for m in mt:
                # year before jan
                if m[1][-2:]=='01' and m[1]!=mt[0][1]:
                    mpt+="<tr><td><b>"+m[1][:4]+"</b></td>"

                #yearly data
                if m==mt[0] or (m[1][-2:]=='01' and m[1]!=mt[0][1]):
                    ydat=[x[0] for x in mt if x[1][:4]==m[1][:4] and x[0]>0]
                    ytot=sum(ydat)
                    yavg=int(sum(ydat)/len(ydat)) if ytot>0 else 0

                # month cell
                mpt+='<td align="right"'
                if m[0]==0:
                    mpt+=' style="background:lightgrey;"'
                elif m[0]>=yavg:
                    mpt+=' style="background:lightblue;"'
                mpt+='>'
                if m[0]>0:
                    mpt+=self._value(m[0],sep='<br>',timevalue=timedata)
                mpt+="</td>"

                # dec, total, avg
                if m[1][-2:]=='12':
                    if yavg>0:
                        if not nototal:
                            mpt+='<td align="right" style="background:lightgreen;">'+self._value(ytot,sep='<br>',timevalue=timedata)+'</td>'
                        mpt+='<td align="right" style="background:lightgreen;">'+self._value(yavg,sep='<br>',timevalue=timedata)
                    else:
                        mpt+='<td style="background:lightgrey;"><td style="background:lightgrey;">'
                    mpt+="</td></tr>"

            # blank cells for future months till end of year
            for nn in range(int(mt[-1][1][-2:])+1,13):
                mpt+="<td></td>"

            # incomplete year's total and avg
            if mpt[-5:]!="</tr>":
                if yavg>0:
                    if not nototal:
                        mpt+='<td align="right" style="background:lightgreen;">'+self._value(ytot,sep='<br>',timevalue=timedata)+'</td>'
                    mpt+='<td align="right" style="background:lightgreen;">'+self._value(yavg,sep='<br>',timevalue=timedata)
                else:
                    mpt+='<td style="background:lightgrey;"></td><td style="background:lightgrey;">'
                mpt+="</td></tr>"
            mpt+="</tbody></table>"
        else:
            mpt = ''
        return mpt


    def _balance_gather(self,bal_year='this year'):
        #print(bal_year)
        if bal_year=='this year':
            thismonth=datetime.datetime.now().strftime('%Y-%m')
            bal_year=thismonth[:4]
        else:
            bal_year=str(datetime.datetime.now().year-1)
            thismonth=bal_year+'-12'
        yearsback=datetime.datetime.now().year-int(bal_year)
    
        ymonths=[x for x in [bal_year+'-'+str(y).zfill(2) for y in range(1,13)] if x<=thismonth]

        music={x:0 for x in ymonths}
        for mg in self.tagged_as('Music')['game']:
            for gt in self.list('playtime',what2={'game':mg,'aggr':'monthly','years':yearsback}):
                if gt[1] in music.keys():
                    music[gt[1]]+=gt[0]

        boardgames={x[1]:x[0] for x in self.list('playtime',what2={'platform':'Board Game','aggr':'monthly','years':yearsback}) if bal_year in x[1]}
        learning={x[1]:x[0] for x in self.list('playtime',what2={'platform':'Learning','aggr':'monthly','years':yearsback}) if bal_year in x[1]}
        exercise={x[1]:x[0] for x in self.list('playtime',what2={'platform':'Exercise','aggr':'monthly','years':yearsback}) if bal_year in x[1]}

        allgames={x[1]:x[0] for x in self.list('playtime',what2={'aggr':'monthly','years':yearsback}) if bal_year in x[1]}
        entries={x[1]:x[0] for x in self.list('playtime',what2={'aggr':'monthly','count':'','years':yearsback}) if bal_year in x[1]}
        titles={x[1]:x[0] for x in self.list('playtime',what2={'aggr':'monthly','count':'titles','years':yearsback}) if bal_year in x[1]}
        titles['total']=[x[0] for x in self.list('playtime',what2={'aggr':'yearly','count':'titles','years':yearsback}) if bal_year in x[1]][0]


        return ymonths, music, boardgames, learning, exercise, allgames, entries, titles

        
    def balance(self):
        bal=''
        for bal_year in ['this year', 'last year',]:
            ymonths, music, boardgames, learning, exercise, allgames, entries, titles = self._balance_gather(bal_year=bal_year)

            ## TABLE
            # header
            bal+="<h1>"+bal_year+"</h1>"
            bal+='<table><tbody><tr><th></th>'+''.join(['<th>'+str(n)+'</th>' for n in range(1,13)])+"<th>total</th><th>avg</th></tr>"
            highlights={'month':{},'year':{}}

            # months with data buildup
            for m in ['balance','ratio','music','daily music','vg','bg','learn','daily learn','exercise','total','entries','titles']:
                # row title
                bal+="<tr>"
                if m=='entries':
                    bal+='<td>-</td></tr><tr>'
                bal+="<td><b>"+m+"</b></td>"

                ts=[]
                for ym in ymonths:
                    mus=music.get(ym,0)
                    boa=boardgames.get(ym,0)
                    lea=learning.get(ym,0)
                    exe=exercise.get(ym,0)
                    tot=allgames.get(ym,0)
                    vid=tot-mus-boa-lea-exe

                    if m=='balance':
                        ts.append((mus+lea+exe)/BALANCERATIO-vid)
                    elif m=='ratio':
                        if vid==0:
                            if mus+lea+exe > 0:
                                ts.append(2)
                            else:
                                ts.append(0)
                        else:
                            ts.append((mus+lea+exe)/vid)
                    elif m=='music':
                        ts.append(mus)
                    elif m=='daily music':
                        if bal_year=='this year' and ym==ymonths[-1]:
                            ts.append(mus/datetime.datetime.now().day)
                        else:
                            ts.append(mus/monthrange(int(ym[:4]),int(ym[-2:]))[1])
                    elif m=='vg':
                        ts.append(vid)
                    elif m=='bg':
                        ts.append(boa)
                    elif m=='learn':
                        ts.append(lea)
                    elif m=='daily learn':
                        if bal_year=='this year' and ym==ymonths[-1]:
                            ts.append(lea/datetime.datetime.now().day)
                        else:
                            ts.append(lea/monthrange(int(ym[:4]),int(ym[-2:]))[1])
                    elif m=='exercise':
                        ts.append(exe)
                    elif m=='total':
                        ts.append(tot)
                    elif m=='entries':
                        ts.append(entries.get(ym,0))
                    elif m=='titles':
                        ts.append(titles.get(ym,0))
                    else:
                        pass

                if m=='balance' or m=='ratio':
                    highlights['month'][m]=ts[-1]
                    if m=='ratio' and len(ts)>1:
                        rank=' #'+str(len([x for x in ts[:-1] if x>ts[-1]])+1)
                        highlights['month']['rank']=rank
                        if ts[-1]>=max(ts[:-1]):
                            highlights['month']['dynamics']=('yellow',':)')#highest
                        elif ts[-1]>ts[-2]:
                            highlights['month']['dynamics']=('green','++') #higher
                        elif ts[-1]<ts[-2]:
                            highlights['month']['dynamics']=('red','--') #lower
                        else:
                            highlights['month']['dynamics']=('lightgrey','==') #same

                ctot=sum(ts)
                cavg=ctot/len(ts)
                if m=='titles':
                    ctot=titles['total']

                #yearfill
                for a in range(12-len(ts)):
                    ts.append(0)

                if m=='ratio':
                    work=sum([music.get(ym,0) for ym in ymonths])+sum([learning.get(ym,0) for ym in ymonths])+sum([exercise.get(ym,0) for ym in ymonths])
                    try:
                        rr=work/(sum([allgames.get(ym,0) for ym in ymonths])-sum([boardgames.get(ym,0) for ym in ymonths])-work)
                    except:
                        rr=0
                    ts.append(rr)
                    highlights['year'][m]=ts[-1]
                elif m=='daily music':
                    if bal_year=='this year':
                        ts.append(sum([music.get(ym,0) for ym in ymonths])/datetime.datetime.now().timetuple().tm_yday)
                    else:
                        ts.append(sum([music.get(ym,0) for ym in ymonths])/365)
                elif m=='daily learn':
                    if bal_year=='this year':
                        ts.append(sum([learning.get(ym,0) for ym in ymonths])/datetime.datetime.now().timetuple().tm_yday)
                    else:
                        ts.append(sum([learning.get(ym,0) for ym in ymonths])/365)
                else:
                    ts.append(ctot)
                    if m=='balance':
                        highlights['year']['balance']=ts[-1]
                ts.append(cavg)

                # month cells
                for nn,t in enumerate(ts):
                    bal+='<td align="right"'
                    if (m=='balance' and t<0) or (m=='ratio' and t<BALANCERATIO and t>0) or (m=='daily music' and t<DAILYMUSICTARGET and t>0):
                        bal+=' style="background:red;"'
                    elif (m=='balance' and t>0) or (m=='ratio' and t>=BALANCERATIO) or (m=='daily music' and t>=DAILYMUSICTARGET):
                        bal+=' style="background:lightgreen;"'
                    elif ctot==0:
                        pass
                    elif nn<12 and t!=0 and t>=cavg:
                        bal+=' style="background:lightblue;"'
                    bal+='>'
                    if m=='ratio' and t>0:
                        bal+="{0:.2f}".format(t)
                    elif (m=='entries' or m=='titles') and t>0:
                        bal+=str(int(t))
                    elif (m=='daily music' or m=='daily learn') and t>0:
                        bal+=str(int(t))+'m'
                    elif t!=0:
                        bal+=self._value(t,sep='<br>')
                    bal+="</td>"
                bal+='</tr>'
            bal+='</tbody></table>'

            if bal_year == 'this year':
                high='<h1>curr month: <font style="background:'
                high+='red' if highlights['month']['ratio']<BALANCERATIO else 'lightgreen'
                high+=';">'+self._value(highlights['month']['balance'], sep=' ')
                high+=' ('+"{0:.2f}".format(highlights['month']['ratio'])+')</font>'
                if 'dynamics' in highlights['month']:
                    high+='<font style="background:'+highlights['month']['dynamics'][0]+';"> '
                    high+=highlights['month']['dynamics'][1]
                    if 'rank' in highlights['month']:
                        high+=highlights['month']['rank']
                    high+='</font>'
                high+='</h1><h1>this year: <font style="background:'
                high+='red' if highlights['year']['ratio']<BALANCERATIO else 'lightgreen'
                high+=';">'+self._value(highlights['year']['balance'], sep=' ')
                high+=' ('+"{0:.2f}".format(highlights['year']['ratio'])+')</font></h1>'
                high+='<h1>target ratio: '+"{0:.2f}".format(BALANCERATIO)+'</h1>'
                high+='<h1>daily music target: ' + str(DAILYMUSICTARGET) + 'm </h1><hr>'

        return high+bal


    def idof(self,what,name):
        try:
            r=int(name)
        except:
            try:
                r=self.cursor.execute('''SELECT id FROM '''+WHAT[what]+''' WHERE name="'''+name+'''";''').fetchone()[0]
            except:
                raise ValueError('No such '+what+' in db. ('+name+')')
        return r


    def nameof(self,what,id):
        return self.cursor.execute('''SELECT name FROM '''+WHAT[what]+''' WHERE id='''+str(id)+''';''').fetchone()[0]


    def add(self,what,name):
        self.cursor.execute('''
            INSERT INTO '''+WHAT[what]+'''( name, dateadded ) VALUES (?,?);''',
                        (name,datetime.datetime.now()))
        self.db.commit()
        return {'duna':'Done.'}


    def tag(self,what,name,tag):
        if what=='game':
            ga=self.idof('game',name)
            pl=None
        elif what=='platform':
            ga=None
            pl=self.idof('platform',name)
        tag=self.idof('tag',tag)

        self.cursor.execute('''
            INSERT INTO tagassignments ( game, platform, tag, dateadded ) VALUES (?,?,?,?);''',
                        (ga,pl,tag,datetime.datetime.now()))
        self.db.commit()
        return {'duna':'Done.'}


    def tagged_as(self,tag):
        tag=self.idof('tag',tag)
        return {
            'game':[x[0] for x in self.cursor.execute('''SELECT game FROM tagassignments WHERE tag='''+str(tag)+''' AND game NOT NULL;''').fetchall()],
            'platform':[x[0] for x in self.cursor.execute('''SELECT platform FROM tagassignments WHERE tag='''+str(tag)+''' AND platform NOT NULL;''').fetchall()]
            }


    def addPTime(self,game,platform,start,end,ptime,is_cumm=False):
        def last_day_of_month(any_day):
            next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
            return next_month - datetime.timedelta(days=next_month.day)

        game=self.idof('game',game)
        platform=self.idof('platform',platform)

        if start and not isinstance(start,datetime.datetime):
            try:
                start=datetime.datetime.strptime(start,'%d/%m/%y')
            except:
                return {'error':'Start date in wrong format? (dd/mm/yy)'}
        if end and not isinstance(end,datetime.datetime):
            try:
                end=datetime.datetime.strptime(end,'%d/%m/%y')
            except:
                return {'error':'End date in wrong format? (dd/mm/yy)'}

        if not is_cumm:
            if start>end:
                return {'error':'Start comes after end?'}
            l=self.list('playtime',{'game':game})
            if [x for x in l if (start<=datetime.datetime.strptime(x[3][:10],'%Y-%m-%d') and datetime.datetime.strptime(x[3][:10],'%Y-%m-%d')<=end) or (start<=datetime.datetime.strptime(x[4][:10],'%Y-%m-%d') and datetime.datetime.strptime(x[4][:10],'%Y-%m-%d')<=end)]:
                return {'error':'Collides with previous entry.'}
        if is_cumm or start.month==end.month:
            self.cursor.execute('''
                INSERT INTO playtime( game, platform, t_start, t_end,
                            dateadded, ptime, is_cumm) VALUES (?,?,?,?,?,?,?);''',
                                (game,platform,start,end,datetime.datetime.now(),ptime,is_cumm))
            self.db.commit()
        else:
            u=ptime/((end-start).days+1)
            ms={start.month:[start,last_day_of_month(start),0],
                end.month:[end.replace(day=1),end,0]}
            for x in range(start.month+1,end.month):
                n=start.replace(month=x,day=1)
                ms[x]=[n,last_day_of_month(n),0]
            for m in range(start.month,end.month+1):
                ms[m][2]=((ms[m][1]-ms[m][0]).days+1)*u
                self.addPTime(game,platform,ms[m][0],ms[m][1],int(ms[m][2]),False)
        return {'duna':str(ptime)+' added for '+self.nameof('game',game)+'.'}


    def addSTime(self,sleepdate,sleeptime):
        if sleepdate and not isinstance(sleepdate,datetime.datetime):
            try:
                sleepdate=datetime.datetime.strptime(sleepdate,'%d/%m/%y')
            except:
                return {'error':'Sleep date in wrong format? (dd/mm/yy)'}
        if sleeptime and not isinstance(sleeptime,int):
            try:
                if ':' in sleeptime:
                    sleeptime=60*int(sleeptime.split(':')[0])+int(sleeptime.split(':')[1])
                else:
                    sleeptime=int(sleeptime)
            except:
                return {'error':'Sleep time in wrong format? (h:mm or mmm)'}

        l=self.list('sleeptime')
        if sleepdate in [datetime.datetime.strptime(x[1][:10],'%Y-%m-%d') for x in l]:
            return {'error':'Collides with previous entry.'}
        if sleepdate and sleeptime:
            if sleepdate<datetime.datetime.now()-datetime.timedelta(days=99):
                return {'error':'Too far back in the past.'}
            self.cursor.execute('''
                INSERT INTO sleeptime(sleepdate, sleeptime, dateadded) VALUES (?,?,?);''',
                                (sleepdate,sleeptime,datetime.datetime.now()))
            self.db.commit()
        return {'duna':str(sleeptime)+' added for '+sleepdate.strftime('%d/%m/%y')+'.'}
                

    def list(self,what,what2={}):
        if what=='playtime':
            if not what2:
                return self.cursor.execute('''SELECT * FROM playtime ORDER BY id DESC LIMIT 20;''').fetchall()
            else:
                aaa=False
                if 'aggr' in what2:
                    sql='SELECT '
                    if 'count' in what2:
                        if what2['count']=='titles':
                            sql+='COUNT(DISTINCT game)'
                        else:
                            sql+='COUNT(ptime)'
                    else:
                        sql+='SUM(ptime)'
                    if what2['aggr']=='yearly':
                        sql+=' AS mptime, strftime("%Y", t_start) AS yrmth '
                    else:
                        sql+=' AS mptime, strftime("%Y-%m", t_start) AS yrmth '
                else:
                    sql='''SELECT * '''
                sql+='''FROM playtime '''
                if [x for x in ['game','platform','days','months','years'] if x in what2]:
                    sql+='WHERE '
                if 'game' in what2:
                    sql+='game='+str(self.idof('game',what2['game']))
                    aaa=True
                if aaa and 'platform' in what2:
                    sql+=' AND '
                    aaa=False
                if 'platform' in what2:
                    sql+='platform='+str(self.idof('platform',what2['platform']))
                    aaa=True
                if aaa and [x for x in ['days', 'months', 'years', 'ym', 'y'] if x in what2]:
                    sql+=' AND '
                    aaa=False
                if 'days' in what2:
                    #WHERE date >= date('now','start of month','-1 month')
                    #AND date < date('now','start of month')
                    sql+='''t_end>= date('now','-'''+str(what2['days'])+''' days')'''
                elif 'months' in what2:
                    sql+='''t_end>= date('now','start of month','-'''+str(what2['months'])+''' month')'''
                elif 'years' in what2:
                    sql+='''t_end>= date('now','start of year','-'''+str(what2['years'])+''' year')'''
                elif 'ym' in what2:
                    sql+='''strftime('%Y-%m', t_end) = \'''' + what2['ym'] + '\''
                elif 'y' in what2:
                    sql+='''strftime('%Y', t_end) = \'''' + what2['y'] + '\''
                if 'aggr' in what2:
                    if what2['aggr']=='yearly':
                        sql+=''' GROUP BY strftime("%Y", t_start);'''
                    else:
                        sql+=''' GROUP BY strftime("%Y-%m", t_start);'''
                else:
                    sql+=';'
                #print(sql)
                return self.cursor.execute(sql).fetchall()
        elif what=='sleeptime':
            return self.cursor.execute('''SELECT * FROM sleeptime ORDER BY id DESC LIMIT 100;''').fetchall()
        else:
            return self.cursor.execute('''SELECT name, dateadded,id FROM '''+WHAT[what]+''' ORDER BY name ASC;''').fetchall()


    def top(self,what='game',what2={'years':'0'}):
        items=[x[0] for x in self.list(what,{'game':what2['game']} if 'game' in what2 else {})]
        if what=='game' and 'gameperplatform' in what2:
            allplatforms=[x[0] for x in self.list('platform')]
        else:
            allplatforms=[]
        itemswtimes=[]
        for item in items:
            wh=what2
            wh[what]=item
            ipts=[]
            if allplatforms:
                for p in allplatforms:
                    wh['platform']=p
                    ipts.append([p,self.list('playtime',wh)])
            else:
                ipts.append(['',self.list('playtime',wh)])

            if 'impressions' in what2:
                def consecu(x):
                    aa=[int(y) for y in x[0].split('-')]
                    bb=[int(y) for y in x[1].split('-')]
                    if aa[0]>bb[0] or (aa[0]==bb[0] and aa[1]>bb[1]):
                        cc=list(bb)
                        bb=list(aa)
                        aa=list(cc)
                    if (aa[0]==bb[0] and bb[1]-aa[1]==1) or (aa[0]+1==bb[0] and aa[1]==12 and bb[1]==1):
                        return ['-'.join([str(a).zfill(2) for a in aa]), '-'.join([str(b).zfill(2) for b in bb])]
                    else:
                        return []
                for ipt in ipts:
                    t={}
                    for i in ipt[1]:
                        ym=i[3][:7]
                        if ym in t:
                            t[ym]+=i[6]
                        else:
                            t[ym]=i[6]
                    if t:
                        tt={}
                        monthpot = list(t.keys())
                        while monthpot:
                            pairs = [consecu(x) for x in itertools.combinations(monthpot, 2) if consecu(x)]
                            if pairs:
                                times = [t[x[0]]+t[x[1]] for x in pairs]
                                maksz = times.index(max(times))
                                tt['+'.join(pairs[maksz])] = times[maksz]
                                for x in pairs[maksz]:
                                    monthpot.pop(monthpot.index(x))
                            else:
                                for x in monthpot:
                                    itemswtimes.append([item,t[x],x])
                                break
                        for k in tt.keys():
                            itemswtimes.append([item,tt[k],k])
                #print(itemswtimes, flush=True)
            else:
                for ipt in ipts:
                    t=0
                    for i in ipt[1]:
                        if i[7]==1:
                            pass
                            #sp=self.cursor.execute('SELECT startofplay FROM games WHERE id=(?);',(str(i[1]))).fetchone()[0]
                            #print(sp)
                            #t+=0
                        else:
                            t+=i[6]
                #t=ipt
                #print([x,t])
                    if t>0:
                        if allplatforms:
                            itemswtimes.append([item+' ('+ipt[0]+')',t])
                        else:
                            itemswtimes.append([item,t])

        itemswtimes.sort(key=lambda x:x[1], reverse=True)
        tt=sum([x[1] for x in itemswtimes])
        if 'impressions' in what2:
            r=[{'rank':str(n+1),'name':x[0],'time':str(int(x[1]/60))+'h '+str(x[1]%60)+'m','yearmonth':x[2]} for n,x in enumerate(itemswtimes)]
        else:
            r=[{'rank':str(n+1),'name':x[0],'time':str(int(x[1]/60))+'h '+str(x[1]%60)+'m','perc':'('+str(int(x[1]/tt*100))+'%)'} for n,x in enumerate(itemswtimes)]
        r.append({'rank':'Total','name':'','time':str(int(tt/60))+'h '+str(tt%60)+'m','perc':''})
        return r


    def toptags(self):
        tagtimes=[]
        for x in self.list('tag'):
            #print(x[0],end=': ')
            ta=self.tagged_as(x[0])
            for t in ta:
                if ta[t]:
                    #print(', '.join([ptdb.nameof(t,ti) for ti in ta[t]]), end='; ')
                    taim=[(self.nameof(t,ti),self.list('playtime',what2={t:ti,})) for ti in ta[t]]
                    titles=[]
                    tot=0
                    for n,tai in enumerate(taim):
                        tittot=sum([x[-2] for x in tai[1]])
                        tot+=tittot
                        titles.append({'name':tai[0],'time':tittot})
                    titles.sort(key=lambda x: x['time'],reverse=True)
                    for n in range(len(titles)):
                        titles[n]['time']=str(int(titles[n]['time']/60))+'h '+str(titles[n]['time']%60)+'m'
                    tagtimes.append((x[0],tot,titles))
        tagtimes.sort(key=lambda x: x[1],reverse=True)
        r=[]
        for n,tt in enumerate(tagtimes):
            timstr=str(int(tt[1]/60))+'h '+str(tt[1]%60)+'m'
            r.append({'rank':str(n+1),'name':tt[0],'time':timstr,'titles':tt[2]})
        return r

    def deleteLatest(self,what):
        self.cursor.execute('DELETE FROM '+what+' WHERE id=(?);',
                            (self.cursor.execute('SELECT * FROM '+what+' ORDER BY id DESC LIMIT 1;').fetchone()[0],))
        self.db.commit()


if __name__=='__main__':
    ptdb=PTimeDb()

    #prepop
    '''
    ptdb.add('game','Carcassonne')
    ptdb.add('game','Dragon Quest Builders Demo')
    ptdb.add('game','The Flame in the Flood')
    ptdb.add('game','Forma.8 Demo')
    ptdb.add('game','Gonner')
    ptdb.add('game','Implosion Demo')
    ptdb.add('game','Mario+Rabbids: Kingdom Battle')
    ptdb.add('game','Mr Jack in New York')
    ptdb.add('game','NBA Playgrounds')
    ptdb.add('game','Snipperclips')
    ptdb.add('game','Splatoon 2')
    ptdb.add('game','Thimbleweed Park')
    ptdb.add('platform','iOS')
    ptdb.add('platform','Switch')
    ptdb.add('platform','DS')
    ptdb.add('platform','Board Game')

    ptdb.add('tag','Mario games')
    ptdb.tag('game','Mario+Rabbids: Kingdom Battle','Mario games')

    ptdb.addPTime('Mario+Rabbids: Kingdom Battle','Switch','05/01/18','05/01/18',145)
    ptdb.addPTime('Mario+Rabbids: Kingdom Battle','Switch','08/01/18','08/01/18',40)
    ptdb.addPTime('Mario+Rabbids: Kingdom Battle','Switch','09/01/18','09/01/18',60)
    ptdb.addPTime('Gonner','Switch','09/01/18','09/01/18',10)
    ptdb.addPTime('NBA Playgrounds','Switch','10/01/18','10/01/18',100)
    ptdb.addPTime('NBA Playgrounds','Switch','11/01/18','11/01/18',40)
    ptdb.addPTime('Dragon Quest Builders Demo','Switch','11/01/18','11/01/18',45)
    ptdb.addPTime('Forma.8 Demo','Switch','12/01/18','12/01/18',35)
    ptdb.addPTime('Dragon Quest Builders Demo','Switch','12/01/18','12/01/18',90)
    ptdb.addPTime('Splatoon 2','Switch','12/01/18','12/01/18',70)
    ptdb.addPTime('Splatoon 2','Switch','13/01/18','13/01/18',145)
    ptdb.addPTime('Splatoon 2','Switch','14/01/18','14/01/18',45)
    ptdb.addPTime('Implosion Demo','Switch','14/01/18','14/01/18',45)
    ptdb.addPTime('The Flame in the Flood','Switch','15/01/18','15/01/18',40)
    ptdb.addPTime('Snipperclips','Switch','15/01/18','15/01/18',5)
    ptdb.addPTime('The Flame in the Flood','Switch','16/01/18','16/01/18',30)
    ptdb.addPTime('NBA Playgrounds','Switch','17/01/18','17/01/18',25)
    ptdb.addPTime('NBA Playgrounds','Switch','19/01/18','19/01/18',15)
    ptdb.addPTime('Thimbleweed Park','Switch','19/01/18','19/01/18',35)
    ptdb.addPTime('Thimbleweed Park','Switch','20/01/18','20/01/18',215)
    ptdb.addPTime('Thimbleweed Park','Switch','22/01/18','22/01/18',40)
    ptdb.addPTime('Thimbleweed Park','Switch','23/01/18','23/01/18',80)
    ptdb.addPTime('Thimbleweed Park','Switch','31/01/18','31/01/18',75)
    ptdb.addPTime('Thimbleweed Park','Switch','01/02/18','01/02/18',60)
    ptdb.addPTime('Thimbleweed Park','Switch','02/02/18','02/02/18',105)
    ptdb.addPTime('Thimbleweed Park','Switch','03/02/18','03/02/18',65)
    ptdb.addPTime('Thimbleweed Park','Switch','04/02/18','04/02/18',215)
    ptdb.addPTime('Carcassonne','iOS','27/01/18','02/02/18',114)
    ptdb.addPTime('Mr Jack in New York','Board Game','02/02/18','02/02/18',75)
    #ptdb.addPTime('Thimbleweed Park','Switch',None,'04/02/18',320,True) #for test
    '''


    print('Games:',[x[0] for x in ptdb.list('game')])
    #print('Platforms:',[x[0] for x in ptdb.list('platform')])
    print('*** Tags ***')
    tagtimes=[]
    for x in ptdb.list('tag'):
        #print(x[0],end=': ')
        ta=ptdb.tagged_as(x[0])
        for t in ta:
            if ta[t]:
                #print(', '.join([ptdb.nameof(t,ti) for ti in ta[t]]), end='; ')
                taim=[ptdb.list('playtime',what2={t:ti,}) for ti in ta[t]]
                tot=0
                for tai in taim:
                    tot+=sum([x[-2] for x in tai])
                tagtimes.append((x[0],tot))
    tagtimes.sort(key=lambda x: x[1],reverse=True)
    for n,tt in enumerate(tagtimes):
        timstr='['+str(int(tt[1]/60))+'h '+str(tt[1]%60)+'m] '
        timstr=' '*(12-len(timstr))+timstr
        print(' '*(8-len(str(n+1)))+str(n+1)+timstr+tt[0]+' '*(40-len(tt[0])))
    print()

    #if ptdb.list('playtime'):
    #    print('--- last 10 PTs:')
    #    for x in ptdb.list('playtime')[:10]:
    #        print(x)


    #print(ptdb.list('playtime',{'game':'Carcassonne','platform':'iOS','years':'1'}))
    '''
    for x in ptdb.top():
        print(x)
    '''
    #ptdb.db.close()
