import main as m
import pandas as pd

data = m.get_data('EURUSD','1wk','1m')
data.index = pd.to_datetime(data.index)
data = data.sort_index(ascending=True)
data = m.diff_strategy_making(data)
data = m.trd_strategy_making(data)
print(data)
balance = 10000
position = 0
direction = 'notset'
data['balance'] = 0
for i in range(len(data)):
    if data['signal'].iloc[i] == 'Buy' and direction != 'Buy' and data['trd_signal'].iloc[i] == 'Buy':
        direction = 'Buy'
        #close short position
        balance = balance + abs(position*data['Close'].iloc[i])
        #data[balance] = balance
        data['balance'].iloc[i] = balance
        print('balance: ' + str(balance))
        position = balance/data['Close'].iloc[i]
        balance = 0
    elif data['signal'].iloc[i] == 'Sell' and direction != 'Sell' and data['trd_signal'].iloc[i] == 'Sell':
        direction = 'Sell'
        balance = balance + abs(position*data['Close'].iloc[i])
        data['balance'].iloc[i] = balance
        print('balance: ' + str(balance))
        position = (balance/data['Close'].iloc[i])*-1
        balance = 0
    # elif data['signal'].iloc[i] != data['trd_signal'].iloc[i] and direction != 'Hold':
    #     direction = 'Hold'
    #     balance = balance + abs((position*data['Close'].iloc[i]))
    #     #data['balance'].iloc[i] = balance
    #     print('balance: ' + str(balance))
    #     position = 0
 #output data to excel
data.to_excel('output.xlsx')
if balance == 0:
    balance = abs((position*data['Close'].iloc[-1])*1)
print('balance: ' + str(balance))