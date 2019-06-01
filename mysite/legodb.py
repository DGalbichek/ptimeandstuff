import datetime
import sqlite3

class LegoDb():
    def __init__(self):
        self.db = sqlite3.connect('legodb.sqlite')
        self.cursor = self.db.cursor()
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS legosetcounts( id INTEGER PRIMARY KEY,
                        setid TEXT, setname TEXT,
                        npieces INTEGER, nspares INTEGER, dateadded TIMESTAMP);
                ''')
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def dbInfo(self):
        return self.cursor.execute('''SELECT * FROM legosetcounts;''').fetchall()
        
    def setInfo(self,setid):
        if self.cursor.execute('''SELECT * FROM legosetcounts WHERE setid=?;''',(setid,)).fetchone():
            return self.cursor.execute('''SELECT * FROM legosetcounts WHERE setid=?;''',(setid,)).fetchone()
        else:
            return False

    def addSet(self,setid,setname,npieces,nspares):
        if self.setInfo(setid):
            pass#print('added already')
        else:
            self.cursor.execute('''INSERT INTO legosetcounts(setid,setname,npieces,nspares,dateadded)
                                VALUES (?,?,?,?,?);''', (setid,setname,npieces,nspares,datetime.datetime.now()))
            self.db.commit()
            #return self.tc_done(standalone=standalone)


if __name__=='__main__':
    pass
    '''
    a=LegoDb()

    a.addSet('31045-1','Bla',12,3)
    print(a.setInfo('31045-1'))

    print(len(a.dbInfo()))
    print(a.dbInfo())

    a.db.close()
    '''
