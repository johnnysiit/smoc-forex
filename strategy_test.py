import main as m
import pandas as pd
import matplotlib.pyplot as plt
import price_list as pl
ticker = 'IQ'
interval = '1h'
period = 360
data = pl.get_table(ticker,interval,period)
data.index = pd.to_datetime(data.index)
data = data.sort_index(ascending=True)
data = m.diff_strategy_making(data)
data = m.trd_strategy_making(data)
balance = data['Close'].iloc[0]
position = 0
direction = 'notset'
data['balance'] = 0
data['posit'] = 0
open_price = 0
data['open_price'] = 0
data['value'] = 0
#open_price = data['Close'].iloc[0]
for i in range(len(data)):
    if data['signal'].iloc[i] == 'Buy' and direction != 'Buy' and data['trd_signal'].iloc[i] == 'Buy':
        direction = 'Buy'
        balance = balance + (position*open_price*(-1)) + (position*(-1)*(open_price - data['Close'].iloc[i]))
        position = balance/data['Close'].iloc[i]
        data['posit'].iloc[i] = position
        balance = 0
        open_price = float(data['Close'].iloc[i])
        data['open_price'].iloc[i] = open_price

    elif data['signal'].iloc[i] == 'Sell' and direction != 'Sell' and data['trd_signal'].iloc[i] == 'Sell':
        direction = 'Sell'
        #get the balance from the position and last oepn price
        balance = balance + position*open_price + position*(data['Close'].iloc[i] - open_price)
        position = balance/data['Close'].iloc[i]*-1
        data['posit'].iloc[i] = position
        balance = 0
        open_price = float(data['Close'].iloc[i])
        data['open_price'].iloc[i] = open_price

    elif data['signal'].iloc[i] != data['trd_signal'].iloc[i] and direction != 'Hold':
        direction = 'Hold'
        if data['posit'].iloc[i-1] > 0:
            balance = balance + position*open_price + position*(data['Close'].iloc[i] - open_price)
        elif data['posit'].iloc[i-1] < 0:
            balance = (balance + position*open_price*-1) + (position*(open_price - data['Close'].iloc[i])*-1)
        
        data['balance'].iloc[i] = balance
        position = 0
        data['posit'].iloc[i] = position
        open_price = 0
        data['open_price'].iloc[i] = open_price
    else:
        data['posit'].iloc[i] = position
        data['balance'].iloc[i] = balance
        data['open_price'].iloc[i] = open_price



 #output data to excel
for i in range(len(data)):
    balance = data['balance'].iloc[i]
    position = data['posit'].iloc[i]
    open_price = data['open_price'].iloc[i]
    if data['posit'].iloc[i] > 0:
        data['value'].iloc[i] = balance + position*open_price + position*(data['Close'].iloc[i] - open_price)
    elif data['posit'].iloc[i] < 0:
        data['value'].iloc[i] = balance + (position*open_price*-1) + (position*(open_price - data['Close'].iloc[i])*-1)
    else:
        data['value'].iloc[i] = balance
data.index = data.index.tz_localize(None)

subset = data[['Close','value']]
subset.to_excel('output.xlsx')

#subset 2 = Datetime, Close, signal, trd_signal, balance, posit, open_price, value
subset2 = data[['Close','signal','trd_signal','balance','posit','open_price','value']]
subset2.to_excel('output2.xlsx')

#plot the data
plt.plot(subset)
#legend 
plt.legend(['Close','Value'])
plt.title(ticker+" Interval: "+interval+" Period: "+str(period))
#save the plot
plt.savefig('plot.png')
plt.show()