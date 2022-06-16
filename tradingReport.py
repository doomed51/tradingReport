"""
Uses IBKR to print out a report on trading activity 
"""

from ib_insync import *
from rich import print 

import numpy as np
import pandas as pd 
import seaborn as sns
import matplotlib.pyplot as plt

"""
Global vars
"""
queryID_trades = '690177' # flex report ID from IBKR 

""" 
1. setup token

"""
# get flexreport token 
with open("token.txt") as f:
    tkn = f.read().strip()

"""
2. connect to ibkr
"""

ibkr = IB()
ibkr.connect('127.0.0.1', 7496, clientId=10)

""" 
3. Download the flex report 
"""
report = FlexReport(token = tkn, queryId = queryID_trades)

"""
4. Setup [dataframe]trades for processing
"""
trades = report.df('Trade')
trades.replace('', np.nan, inplace=True)
trades.dropna(subset=['strike'], inplace=True)
print('\n')

""" 
Define some stats for later consumption
---
[dataframe] -> trades, closedTrades, closedTrades_groupedByWeek
"""
trades['orderTime'] = pd.to_datetime(trades['orderTime'])
numPositiveTrades = trades.loc[trades['fifoPnlRealized'] > 0]['ibOrderID'].count()
periodStart = trades['orderTime'].min().strftime('%Y-%m-%d')
periodEnd = trades['orderTime'].max().strftime('%Y-%m-%d')
totalFeesPaid = trades['ibCommission'].abs().sum()
totalTrades = trades['ibOrderID'].count()
totalContracts = trades['quantity'].abs().sum()

# create a dataframe of closed trades only  
closedTrades = trades.loc[trades['fifoPnlRealized'] != 0].sort_values('dateTime').copy()
closedTrades['initialCapital'] = closedTrades['netCash'] - closedTrades['fifoPnlRealized']
closedTrades['pctReturn'] = (closedTrades['fifoPnlRealized'] / 
    (closedTrades['netCash'] - closedTrades['fifoPnlRealized'] ) ) *100
averageReturnPerTrade = closedTrades['pctReturn'].mean()

# closed trades stats grouped by week
closedTradeStats_groupedByWeek = closedTrades.groupby( 
    [pd.Grouper(key='orderTime', freq='W-FRI')]).agg(
        {'pctReturn':'mean', 
        'symbol':'count', 
        'fifoPnlRealized':'sum', 
        'initialCapital':'sum'}
    ).reset_index().sort_values('orderTime')
#rename columns to reflect stats
closedTradeStats_groupedByWeek.rename(columns={
    'orderTime':'weekEnded',
    'symbol':'numTrades',
    'fifoPnlRealized': 'pnlRealized',
    'pctReturn': 'avgReturn'
}, inplace=True)

"""
Print a simple trading report to console consisting of:
    period covered
    total trades
    total $s traded
    average return per trade
    absolute $ return
    total fees 
"""
# time period covered
print(f"[underline]Trading report for: {periodStart:s} - {periodEnd:s} ({np.busday_count(periodStart, periodEnd):.0f} days) [/underline]\n")

# total # trades (% +ve)
print(' Total Trades: %s (%.2f%% positive)'%(closedTrades['ibOrderID'].count(), 
    (numPositiveTrades/closedTrades['ibOrderID'].count())*100))
    
# Total $ val traded 
print(f" Total K traded: ${closedTrades['initialCapital'].sum():,.2f}")

# avg. return % per trade 
print(' Avg. return/trade: %.2f%%'%(averageReturnPerTrade))

# absolute return
print(f" Net income: ${closedTrades['fifoPnlRealized'].sum():,.2f}")

# total fees paid, # avg fee per trade, avg fee per contract 
print('')
print(f" Total Fees Paid: ${totalFeesPaid:,.2f}")
print(f"   Total contracts traded: {totalContracts:.0f}")
print(f"   Avg. fee per contract: ${totalFeesPaid/totalContracts:,.2f}")
print('\n')
print(closedTradeStats_groupedByWeek)

""" 
Plot % return of trades over time 
--
Params: 
closedTrades: [dataframe]
period: [int] # days to plot (default to entire timeperiod in closedTrades)
"""
def plotTradingReturns(closedTrades, period=0):
    sns.set()
    fig, axes = plt.subplots(2, 2, figsize=(20,10))
    title = (f"Trading report for: {periodStart:s} - {periodEnd:s} ({np.busday_count(periodStart, periodEnd):.0f} days)")
    fig.suptitle(title)

    if period == 0:
        print('plot all time periods')
        closedTrades['dateTime'] = pd.to_datetime(closedTrades['dateTime']).dt.strftime('%y-%m-%d')
        
        ## plot returns over time
        sns.barplot(
            x = 'dateTime', 
            y = 'pctReturn',
            data = closedTrades,
            ax=axes[0,0]
        )
        axes[0,0].set_title('% return per trade')
        
        ## plot histogram of returns 
        sns.histplot(data=closedTrades, x='pctReturn', ax=axes[0,1])
        axes[0,1].set_title('Distribution - % return')
        
        ## plot weekly returns
        sns.pointplot(data = closedTradeStats_groupedByWeek, y='avgReturn', x='weekEnded', ax=axes[1,0]) 
        axes[1,0].set_title('Average Weekly Returns')

        ## Num trades
        sns.barplot(data = closedTradeStats_groupedByWeek, y='numTrades', x='weekEnded', ax=axes[1,0])
            
    else: 
        print('Plot last %s days'%(period))
    plt.show()


plotTradingReturns(closedTrades)
