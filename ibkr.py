from ib_insync import *

ib = IB() 
ib.connect('127.0.0.1', 7496)

#contract = Forex('USDCAD')
contract = Stock('AAPL', exchange='SMART', currency='USD')
bars = ib.reqHistoricalData(
    contract, endDateTime='', durationStr='30 D',
    barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True
)

df = util.df(bars)

print(df)