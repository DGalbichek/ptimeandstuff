import datetime
import json
import sqlite3

class ZongDb():
    def __init__(self):
        self.db = sqlite3.connect('zongdb.sqlite')
        self.cursor = self.db.cursor()
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS zongusage( id INTEGER PRIMARY KEY,
                        date DATE, activity TEXT);
                ''')
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def dbInfo(self):
        return self.cursor.execute('''SELECT * FROM zongusage;''').fetchall()
        
    def dayInfo(self,day=datetime.datetime.now().date()):
        r=self.cursor.execute('''SELECT * FROM zongusage WHERE date=?;''',(day,)).fetchone()
        return r if r else False

    def zongg(self):
        dinf = self.dayInfo()
        if dinf:
            dinff=json.loads(dinf[2])
            hr=str(datetime.datetime.now().hour)
            if hr in dinff:
                dinff[hr]+=1
            else:
                dinff[hr]=1
            self.cursor.execute('''UPDATE zongusage SET activity=?
                                WHERE date=?;''', (json.dumps(dinff), datetime.datetime.now().date()))
        else:
            self.cursor.execute('''INSERT INTO zongusage(date,activity)
                                VALUES (?,?);''', (datetime.datetime.now().date(),json.dumps({datetime.datetime.now().hour:1})))
        self.db.commit()
        #print(self.dayInfo())


if __name__=='__main__':
    pass

    a=ZongDb()

    print(a.dbInfo())

    a.db.close()
