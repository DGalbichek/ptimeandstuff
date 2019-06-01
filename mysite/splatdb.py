import datetime
import json
import os
import sqlite3

class SplatDb():
    def __init__(self,dbfile=''):
        if dbfile:
            self.DBFILE=dbfile
        else:
            self.DBFILE='splatdb.sqlite'
        self.db = sqlite3.connect(self.DBFILE)
        self.cursor = self.db.cursor()
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS splatqueries( id INTEGER PRIMARY KEY,
                        content TEXT, dateadded TIMESTAMP, gotresults BOOLEAN);
                ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS splatbattles( id INTEGER PRIMARY KEY,
                        bid TEXT, start TIMESTAMP, victory BOOLEAN,
                        paint INTEGER, kill INTEGER, assist INTEGER, death INTEGER, special INTEGER,
                        content TEXT, dateadded TIMESTAMP);
                ''')
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e


    def dblen(self,db):
        return self.cursor.execute('''SELECT COUNT(*) FROM '''+db+';').fetchone()[0]


    def dbInfo(self,nq=10):
        dbinf={'general':[],'queries':[],'battles':[]}
        dbinf['general'].append('SplatDB size: {:.2f}MB'.format(os.path.getsize(self.DBFILE)/1024**2))
        dbinf['general'].append('no of queries: '+str(self.dblen('splatqueries')))
        dbinf['general'].append('no of battles: '+str(self.dblen('splatbattles')))
        lastq=self.cursor.execute('''SELECT id,dateadded,content FROM splatqueries ORDER BY id DESC LIMIT '''+str(nq)+';').fetchall()
        for x in lastq:
            q={'id':x[0],'date':x[1].split(' ')[0]}
            xx=json.loads(x[2])
            if 'battles' in xx:
                q['nbattles']=len(xx['battles'])
                if len(xx['battles'])>1:
                    q['summ']=xx['battles'][-1]+'-'+xx['battles'][0]
                elif len(xx['battles'])==1:
                    q['summ']=xx['battles'][0]
                else:
                    q['summ']='no new battles'
            else:
                q['nbattles']=0
                q['summ']='error?'
            dbinf['queries'].append(q)
        nb=10
        lastb=self.cursor.execute('''SELECT * FROM splatbattles ORDER BY id DESC LIMIT '''+str(nb)+';').fetchall()
        for x in lastb:
            dbinf['battles'].append(x[1:-2])

        return dbinf


    def addSplatQuery(self,content):
        gotresults='results' in content
        if gotresults:
            battlenumbers=[x['battle_number'] for x in content['results']]
            battlesalreadygot=[x[0] for x in self.cursor.execute('''SELECT bid FROM splatbattles;''').fetchall()]
            print(battlesalreadygot)
            newbattlenumbers=[x for x in battlenumbers if x not in battlesalreadygot]
            print(newbattlenumbers)
            content={'battles':newbattlenumbers}
        self.cursor.execute('''INSERT INTO splatqueries(content,dateadded,gotresults)
                        VALUES (?,?,?);''',(json.dumps(content),datetime.datetime.now(),gotresults))
        self.db.commit()
        return {'nb':newbattlenumbers}


    def newBattles(self):
        bb=json.loads(self.cursor.execute('''SELECT content FROM splatqueries ORDER BY id DESC LIMIT 1;''').fetchone()[0])
        if 'battles' in bb:
            r=bb['battles']
            r.sort()
            return r
        else:
            return []


    def addSplatBattle(self,content):
        def noImg(j):
            if type(j)==type({}):
                return {k:noImg(j[k]) for k in j.keys() if 'image' not in k and 'thumbnail' not in k}
            elif type(j)==type([]):
                return [noImg(k) for k in j]
            else:
                return j

        content=noImg(content)
        pr=content['player_result']
        self.cursor.execute('''
            INSERT INTO splatbattles( bid, start, victory, paint, kill, assist, death, special,
                    content, dateadded) VALUES (?,?,?,?,?,?,?,?,?,?);''',
                            (content['battle_number'], datetime.datetime.fromtimestamp(content['start_time']),
                             content['my_team_result']['key']=='victory',pr['game_paint_point'],
                             pr['kill_count'],pr['assist_count'],pr['death_count'],pr['special_count'],
                             json.dumps(content),datetime.datetime.now()))
        self.db.commit()
        return {'duna':'Done.'}


    def deleteLatest(self,what):
        w={'battle':'splatbattles','query':'splatqueries'}
        self.cursor.execute('DELETE FROM '+w[what]+' WHERE id=(?);', (str(self.dblen(w[what])),))
        self.db.commit()


if __name__=='__main__':
    sdb=SplatDb()
    i=sdb.dbInfo()
    print(i['general'])
    for x in i['queries']:
        print(x)
    for x in i['battles']:
        print(x)
    #print(sdb.newBattles())
