import yfinance as yf
import pandas as pd
import requests
import datetime
import os
import time
import matplotlib.pyplot as plt

def get_data(pair,period,interval):
    data = yf.download(tickers = (pair+'=X') ,period =period, interval = interval)
    data.index = pd.to_datetime(data.index)
    data = data.sort_index(ascending=True)
    return data


def diff_strategy_making(data):
    ##DIFF
    data = data.sort_index(ascending=True)
    data['year_line'] = data['Close'].ewm(span=90, adjust=False).mean()
    data['long'] = data['Close'].ewm(span=2, adjust=False).mean()
    data['short'] = data['year_line'] - (data['long'] - data['year_line'])
    data['dif'] = data['long'] - data['short']
    data['avg1'] = data['dif'].rolling(9).mean()
    data['linep'] = data['dif'].ewm(span=250, adjust=False).mean()
    data['linen'] = data['linep']* -1
    data = data.drop(['linep'], axis=1)
    # if data['avg1'] > data['linen'], signal = 'buy'
    data['signal'] = data.apply(lambda x: 'Buy' if x['avg1'] > x['linen'] else 'Sell', axis=1)
    return data

def trd_strategy_making(data):
    #TRD
    #(2*CLOSE+HIGH+LOW)/4;
    # data['gup6'] = (2*data['Close']+data['High']+data['Low'])/4
    # #get lowest close in 34 rows
    # data['gup8'] = data['Low'].rolling(34).min()
    # data['gup11'] = data['High'].rolling(34).max()
    # #gup 12 = EMA((GUP6-GUP8)/(GUP11-GUP8)*100,13)
    # data['gup12'] = ((data['gup6']-data['gup8'])/(data['gup11']-data['gup8'])*100).ewm(span=13, adjust=False).mean()
    # #gup13_ref = gup12 from the row above
    # data['gup13_ref'] = data['gup12'].shift(1)
    # #GUP13:=EMA(0.667*REF(GUP12,1)+0.333*GUP12,2);
    # data['gup13'] = (0.667 * data['gup13_ref']+ 0.333 * data['gup12']).ewm(span=2, adjust=False).mean()
    # data['aa'] = data['gup13'].ewm(span=1, adjust=False).mean()

    #GUP21:=(2*CLOSE+HIGH+LOW)/4;
    data['gup21'] = (2*data['Close']+data['High']+data['Low'])/4
    #GUP23:=LLV(LOW,34);
    data['gup23'] = data['Low'].rolling(34).min()
    #GUP26:=HHV(HIGH,34);
    data['gup26'] = data['High'].rolling(34).max()
    #GUP27:=EMA((GUP21-GUP23)/(GUP26-GUP23)*100,8);
    data['gup27'] = ((data['gup21']-data['gup23'])/(data['gup26']-data['gup23'])*100).ewm(span=8, adjust=False).mean()
    #BB:EMA(GUP27,5)
    data['bb'] = data['gup27'].ewm(span=5, adjust=False).mean()
    data['trd_signal'] = data.apply(lambda x: 'Buy' if x['gup27'] > x['bb'] else 'Sell', axis=1)

    return data

def diff_graph(data):
    #clean the plt
    plt.plot(data.index, data['avg1'], label='Upper')
    plt.plot(data.index, data['linen'], label='Lower')
    plt.legend()
    #limit to 5 hours data
    plt.xlim(data.index[-300], data.index[-1])
    #get current time
    file_name = "graphs/"+str(datetime.datetime.now())+'_diff.png'
    #save graph
    if not os.path.exists("graphs"):
        os.mkdir("graphs")
    plt.savefig(file_name)
    plt.close()
    return file_name

def trd_graph(data):
    plt.plot(data.index, data['gup27'], label='Upper')
    plt.plot(data.index, data['bb'], label='Lower')
    plt.legend()
    #limit to 5 hours data
    plt.xlim(data.index[-60], data.index[-1])
    #get current time
    file_name = "graphs/"+str(datetime.datetime.now())+'_trd.png'
    #save graph
    if not os.path.exists("graphs"):
        os.mkdir("graphs")
    plt.savefig(file_name)
    plt.close()
    return file_name

def sender(text,graph,api_key):
    chat_id = '-1001829636788'
    
    #######Send Graph and text
    # file = open(graph, 'rb')
    # api_url = f"https://api.telegram.org/bot{api_key}/"
    # method = "sendPhoto"
    # params = {'chat_id': chat_id}
    # files = {'photo': file}
    # caption = text
    # resp = requests.post(api_url + method, params=params, files=files, data={'caption': caption})
    # print(resp)

    #####send text
    url = "https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={text}"
    url = url.format(api_key=api_key, chat_id=chat_id, text=text)
    resp = requests.get(url)
    print(resp)

def diff_sender(data,graph,pairs,api_key):
    #create a file if not exist
    if not os.path.exists("diff_direction.config"):
        config = open("diff_direction.config", "w")
        config.write(pairs + ":notset\n")
        config.close()

    config = open("diff_direction.config", 'r')
    config_dict = {}
    config_lines = config.readlines()
    for line in config_lines:
        key, value = line.strip().split(':')
        config_dict[key] = value
    config.close()

    if not pairs in config_dict:
        config_dict[pairs] = 'notset'

    #if data['signal'] in last two rows are different, print('buy')
    if data['signal'].iloc[-1] != config_dict[pairs]:
        signal = ('[' + pairs + '] DIFF Signal changed to '+ data['signal'].iloc[-1])
        print(signal)
        sender(signal,graph,api_key)

        config_dict[pairs] = data['signal'].iloc[-1]
        config = open("diff_direction.config", "w")
        config.truncate(0)
        for key, value in config_dict.items():
            config.write(key + ":" + value + "\n")
        config.close()


def trd_sender(data,graph,pairs,api_key):
    #create a file if not exist
    pair_signal_name = pairs + "_signal"
    pair_position = pairs+'_position'
    if not os.path.exists("trd_direction.config"):
        config = open("trd_direction.config", "w")
        config.write(pair_signal_name + ":notset\n")
        config.close()
    
    config = open("trd_direction.config", 'r')
    config_dict = {}
    config_lines = config.readlines()
    for line in config_lines:
        key, value = line.strip().split(':')
        config_dict[key] = str(value)
    config.close()

    if not pair_signal_name in config_dict:
        config_dict[pair_signal_name] = 'notset'
    if not pair_position in config_dict:
        config_dict[pair_position] = 'notset'

    ###########gup###############
    if data['bb'].iloc[-1] < 25 and config_dict[pair_position] != 'low':
        position = 'low'
        text = ('[' + pairs + '] TRD Drop below 25')
        sender(text,graph,api_key)
    elif data['gup27'].iloc[-1] > 75 and config_dict[pair_position] != 'high':
        position = 'high'
        text = ('[' + pairs + '] TRD Rise above 75')
        sender(text,graph,api_key)
    elif data['bb'].iloc[-1] > 25 and data['gup27'].iloc[-1] < 75 and config_dict[pair_position] != 'mid':
        position = 'mid'
    else:
        position = config_dict[pair_position]
      
    config_dict[pair_position] = position
    config = open("trd_direction.config", "w")
    config.truncate(0)
    for key, value in config_dict.items():
      config.write(key + ":" + value + "\n")
    config.close()
    #############################

def double_sender(data,graph,pairs,api_key):
    # if trd_signal = buy, and diff_signal = buy, set b_signal to buy
    data['b_signal'] = data.apply(lambda x: 'Buy' if x['trd_signal'] == 'Buy' and x['signal'] == 'Buy' else 'Sell' if x['trd_signal'] == 'Sell' and x['signal'] == 'Sell' else 'notset', axis=1)
    #create a file if not exist
    pair_signal_name = pairs + "_signal"
    pair_position = pairs+'_position'
    if not os.path.exists("both_direction.config"):
        config = open("both_direction.config", "w")
        config.write(pair_signal_name + ":notset\n")
        config.close()
    
    config = open("both_direction.config", 'r')
    config_dict = {}
    config_lines = config.readlines()
    for line in config_lines:
        key, value = line.strip().split(':')
        config_dict[key] = str(value)
    config.close()

    if not pair_signal_name in config_dict:
        config_dict[pair_signal_name] = 'notset'
    
    #########signal
    if (data['b_signal'].iloc[-1] != config_dict[pair_signal_name]) and (data['b_signal'].iloc[-1] != 'notset'):
        trd_average = round(data['bb'].iloc[-1] + data['gup27'].iloc[-1])/2
        signal = ('[' + pairs + '] BOTH Signal changed to '+ data['b_signal'].iloc[-1] + '\nCurrent TRD Position: '+ str(trd_average))
        sender(signal,graph,api_key)
    config_dict[pair_signal_name] = data['b_signal'].iloc[-1]
    config = open("both_direction.config", "w")
    config.truncate(0)
    for key, value in config_dict.items():
        config.write(key + ":" + value + "\n")
    config.close()


def trade():
    pass

if __name__ == '__main__':
    api = ''
    # while True:
    #pairs_list = ['USDJPY','USDCAD','AUDUSD','EURUSD']
    pairs_list = ['EURUSD','AUDUSD']
    for pairs in pairs_list:
        print('start scraping ' + pairs)
        try:
            fx_data = get_data(pairs,'2d','1m')
            print('Data collection success')
        except:
            print('Data collection error')
            continue
        try:
            fx_data = diff_strategy_making(fx_data)
            fx_data = trd_strategy_making(fx_data)
            print(fx_data)
        except:
            print('data process failed')
        try:
            diff_graph_file = diff_graph(fx_data)
            trd_graph_file = trd_graph(fx_data)
            print('Graph creation success')
        except:
            print('Graph creation error')
            continue
        try:
            diff_sender(fx_data,diff_graph_file,pairs,api)
            #trd_sender(fx_data,trd_graph_file,pairs,api)
            double_sender(fx_data,trd_graph_file,pairs,api)
            print('Telegram message success')
        except:
            print('Telegram message error')
            continue
        time.sleep(10)
    #delete graphs folder
        os.system('rm -rf graphs')
        # time.sleep(50)
