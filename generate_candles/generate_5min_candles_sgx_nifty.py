import pandas as pd
import datetime

#search for two candles with the same timings
def search():
    
    one_min_all = pd.read_csv("sgx_nifty.csv", parse_dates=True,header=None)
    prev_date = one_min_all.iat[0,0]
    prev_time = one_min_all.iat[0,1]
    print(prev_time)
    for i in range(2, len(one_min_all)):
       if one_min_all.iat[i,0] == prev_date and one_min_all.iat[i,1] == prev_time:
           print("OMG!!!")
           print(prev_date)
           print(prev_time)
       prev_date = one_min_all.iat[i,0]
       prev_time = one_min_all.iat[i,1]


def generate_5min_candles():
    
    one_min_all = pd.read_csv("sgx_nifty.csv", parse_dates=True, header=None, dtype=str)
    five_mins = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'name'])
    
    open_price = float(one_min_all.at[0, 2])
    timestamp_five_mins = datetime.datetime.strptime(str(one_min_all.iat[0,0]) + " " + str(one_min_all.iat[0,1]), '%Y%m%d %H%M') + datetime.timedelta(minutes=1)
    print(str(timestamp_five_mins))
    close_price = None
    high_price = -1
    low_price = 1000000
    name = one_min_all.iat[0,7]
    volume_5mins = 0

    for i in range(len(one_min_all)):
        curr_datetime = datetime.datetime.strptime(str(one_min_all.iat[i,0]) + " " + str(one_min_all.iat[i,1]), '%Y%m%d %H%M')
        if curr_datetime >= timestamp_five_mins:

             five_mins.loc[len(five_mins)] = [timestamp_five_mins - datetime.timedelta(minutes = 5), open_price, high_price, low_price, close_price, volume_5mins, name]
             volume_5mins = 0
    
             open_price = float(one_min_all.at[i, 2])
             high_price = -1
             low_price = 10000000
             name = one_min_all.at[i, 7]
             timestamp_five_mins = curr_datetime.replace(minute=curr_datetime.minute - curr_datetime.minute%5)  + datetime.timedelta(minutes=5)

        low_price = min(low_price, float(one_min_all.at[i, 4]))
        high_price = max(high_price, float(one_min_all.at[i, 3]))
        close_price = float(one_min_all.iat[i, 5])
        volume_5mins += float(one_min_all.at[i, 6])
        if one_min_all.at[i, 7] != name:
            print("different names for one candle:")
            print(one_min_all.at[i, 0] + " " + one_min_all.at[i, 1])
        if (i % 5000 == 0):
            print(i);
    print(len(five_mins))
    five_mins.to_excel('nifty.xlsx')
    print("finish");

    
generate_5min_candles()
