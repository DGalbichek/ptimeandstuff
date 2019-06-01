import operator

class Good:
    def __init__(self,name,perish,baseprice):
        self.name=name
        self.perish=perish
        self.baseprice=baseprice
    def __repr__(self):
        return self.name

GOODS = {'food':Good('food',perish=6,baseprice=10)
         , 'water':Good('water',perish=1000,baseprice=5)
         , 'fuel':Good('fuel',perish=10000,baseprice=100)
         }
timelapselist=[]

class Settlement:
    def __init__(self,name,pop,prod,cons,budg,storg=[],markets=[]):
        self.name=name
        self.pop=pop
        self.prod=prod
        self.cons=cons
        self.budg=budg
        self.storg=storg ## storg list of dict {good, qty, bb}
        self.markets=markets
        global timelapselist
        timelapselist.append(self)

    @property
    def demand(self):
        demand={}
        for co in self.cons:
            pr = self.prod.get(co, None)
            p,c=pr,self.cons[co]
            instorage=sum([x['qty'] for x in self.storg if x['good']==co])
            if p-c<0 and 2*(p-c)+instorage<0:
                demand[co]=2*(p-c)+instorage
        return demand

    @property
    def supply(self):
        supply=[]
        for s in self.storg:
            if s['good'] not in self.demand:
                supply.append(s)
        return supply

    def nextperiod(self):
        print('\nNEXT PERIOD')
        ## prod
        for p in self.prod:
            self.storg.append({'good':p,'qty':self.prod[p],'bb':p.perish})
        print('past prod\n',self.storg)

        ## cons
        tstorg=self.storg[::]
        self.storg=[]
        for c in self.cons:
            li=[x for x in tstorg if x['good']==c]
            li.sort(key=operator.itemgetter('bb'))
            print('consumption', c, self.cons[c])
            #print(li)
            con=self.cons[c]
            for l in li:
                if con>0:
                    if con-l['qty']>0:
                        con-=l['qty']
                    else:
                        l['qty']-=con
                        con=0
                        self.storg.append(l)
                else:
                    self.storg.append(l)
        for t in tstorg:
            if t['good'] not in self.cons:
                self.storg.append(t)

        print('past cons\n',self.storg)

        ## perishables perish
        tstorg=self.storg[::]
        self.storg=[]
        for s in tstorg:
            if s['bb']-1>0:
                self.storg.append({'good':s['good'],'qty':s['qty'],'bb':s['bb']-1})

        print('past perish\n',self.storg)


class Merchant:
    def __init__(self,name,supply,demand,funds,storage=None,fix={}):
        self.name=name
        self.supp=supply
        self.dem=demand
        self.funds=funds
        self.storage=storage
        self.fix=fix
        #global timelapselist
        #timelapselist.append(self)

    @property
    def demand(self):
        if self.storage:
            return self.storage.demand
        else:
            return self.dem

    @property
    def supply(self):
        if self.storage:
            return self.storage.supply
        else:
            return self.supp

    def nextperiod(self):
        if fix:
            self.supp=fix['supp']
            self.dem=fix['dem']

    '''
    def sell(self,good,qty):
        if qty==0:
            return {}
        li=[x for x in self.supply if x['good']==good]
        if qty>=sum([x['qty'] for x in li]):
            li.sort(key=operator.itemgetter('bb'), reverse=True)
            gc=0
            while gc<qty:
                
            goods={}
            return goods
        else:
            return self.sell(good,qty-1)

    def buy(self,omerch,good,qty,where):
        p=where.priceof(good)['buy']
        if self.funds-p>=0:
            if self.storage:
                pass
            else:
                self.dem[good]+=qty
            if omerch.storage:
                pass
            else:
                pass#omerch.dem[good]+=qty
            self.funds-=p
            omerch.funds+=p
        else:
            self.buy(omerch,good,qty-1,where)
    '''

class Market:
    def __init__(self,name,settlement,mtype,merchants=[]):
        self.name=name
        self.settlement=settlement
        self.mtype=mtype
        self.merchants=merchants
        global timelapselist
        timelapselist.append(self)

    @property
    def demand(self):
        demand={}
        for m in self.merchants:
            for d in m.demand:
                if d in demand:
                    demand[d]+=m.dem[d]
                else:
                    demand[d]=m.dem[d]
        return demand

    @property
    def supply(self):
        supply={}
        for m in self.merchants:
            for s in m.supply:
                if s['good'] in supply:
                    supply[s['good']]+=s['qty']
                else:
                    supply[s['good']]=s['qty']
        return supply

    def pricetable(self,supp,dem):
        comms=set()
        for sd in [supp,dem]:
            for c in sd:
                comms.add(c)
        comms=list(comms)
        prices={}
        for c in comms:
            s=supp.get(c,0)
            d=dem.get(c,0)
            #supp and dem
            if s>0 and d<0:
                if s+d<0:
                    p=max([(abs(d/s)*0.1+1),2])*c.baseprice
                else:
                    p=max([(1-abs(s/d)*0.01),0.4])*c.baseprice
                buy=round(p,2)
                sell=round(p,2)
            # supp no dem
            elif s>0 and d==0:
                p=0.8*c.baseprice
                buy=round(p,2)
                sell=0
            # no supp but dem
            elif s==0 and d<0:
                p=max([(abs(d/s)*0.1+1),2])*c.baseprice
                buy=0
                sell=round(p,2)
            # no supp no dem
            #elif s==0 and d==0:
            #    buy=0
            #    sell=0
            prices[c]={'buy':buy,'sell':sell}
        return prices

    def priceof(self,c):
        return self.pricetable(self.supply, self.demand)[c]

    def info(self):
        print(self.name,'@',self.settlement.name)
        if self.mtype=='fixed':
            print('This market operates with fixed prices for each period.')

        self.pricetable(self.supply, self.demand)

    def nextperiod(self):
        #merchants trade
        for m in self.merchants:
            m.nextperiod()
        pass


if __name__=='__main__':

    a=Settlement('Paszlake',pop=12000
                 ,prod={
                     GOODS['food']:17000,
                     GOODS['water']:10000
                     }
                 ,cons={
                     GOODS['food']:15000,
                     GOODS['water']:15000
                     }
                 ,budg=1500000
                 ,storg=[
                     {'good':GOODS['food'],'qty':2000,'bb':2},
                     ]
                 )

    a.markets.append(Market(a.name+' market',settlement=a,mtype='fixed'))

    a.markets[0].merchants.append(Merchant('Trade Representative of '+a.name,
                                           supply=a.supply,
                                           demand=a.demand,
                                           storage=a,
                                           funds=6000000))

    a.markets[0].merchants.append(Merchant('Merchant from Oceania',
                                           supply=[{'good':GOODS['water'],'qty':1000,'bb':2},],
                                           demand={GOODS['food']:-1000, GOODS['fuel']:-10},
                                           funds=10000,
                                           fix={
                                               'supp':{'good':GOODS['water'],'qty':1000,'bb':2},
                                               'dem':{GOODS['food']:-1000, GOODS['fuel']:-10}
                                               }
                                           ))

    a.markets[0].merchants.append(Merchant('Fuel vendor',
                                           supply=[{'good':GOODS['fuel'],'qty':100,'bb':10000},],
                                           demand={},
                                           funds=100000,
                                           fix={
                                               'supp':{'good':GOODS['fuel'],'qty':100,'bb':10000},
                                               'dem':{}
                                               }
                                           ))
    
    print('Goods:',[(GOODS[g].name,GOODS[g].baseprice) for g in GOODS])

    print('Initial storg\n',a.storg)

    a.nextperiod()
