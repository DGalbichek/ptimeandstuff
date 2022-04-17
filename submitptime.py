import requests

DBHOST = 'http://blabla.pythonanywhere.com/'
#DBHOST = 'http://127.0.0.1:5000/'

#game
#'''
payload={
    'davidsstuff':'game',
    'toadd':{
        'name':"Deep Rock Galactic"
        }
    }
#'''

'''
payload={
    'davidsstuff':'tagging',
    'totag':{
        'what':'game',
        'name':'Legends of Runeterra',
        'tag':"Riot"
        }
    }
'''

#ptime
'''
payload={
    'davidsstuff':'ptime',
    'toadd':{
        'game':'Defense Grid: The Awakening',
        'platform':'PC',
        'start':'19/08/21',
        'end':'19/08/21',
        'ptime':25
        }
    }
'''

#rules
'''
payload={
    'davidsstuff':'rules',
    'rules':{
        "ym": "2021-11",
        "BALANCERATIOTARGET": 0.75,
        "DAILYMUSICTARGET": 20,
        "DAILYLEARNTARGET": 0,
        "DAILYEXERCISETARGET": 30
        }
    }
'''

r=requests.post(DBHOST+'ptime/add_stuff/',json=payload)
print(r,'-',r.text)
