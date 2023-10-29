import pandas as pd
import datetime
import threading
import pytz

from .strategy_implementation import StrategyImplementation

class ProcessLiveData (threading.Thread):
        def __init__(self, threadID, name, parent, historical_api):
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.name = name
            self.exitFlag = False
            self.parent = parent
            self.historical_api = historical_api

        def run(self):
            print("Starting " + self.name)
            self.process_data(self.name)
            print("Exiting " + self.name)

        def process_data(self, threadName):
            print(self)
            is_beginning = True
            open_price = None
            close_price = None
            high_price = -1
            low_price = 10000000000

            timestamp_five_mins = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            print(timestamp_five_mins)
            if timestamp_five_mins.minute >= 55:
                timestamp_five_mins = timestamp_five_mins.replace(minute=0, second = 0, hour = timestamp_five_mins.hour + 1)
            else:
                timestamp_five_mins = timestamp_five_mins.replace(minute=(timestamp_five_mins.minute//5 + 1)*5, second = 0, microsecond=0)
            
            strategy_impl = StrategyImplementation(self.parent.df)

            while not self.exitFlag:
                self.parent.acquire_lock()
                if not self.parent.getWorkQueue().empty():

                    messg = self.parent.getWorkQueue().get()
                    self.parent.release_lock()

                    data_dict = messg
                    if data_dict == b'\x00':
                        continue
                    #date = datetime.datetime.fromtimestamp(int(data_dict['exchange_timestamp'])/1000.0)
                    #print(str(date)+" "+str(datetime.datetime.now()))
                    ltp = int(data_dict['last_traded_price'])/100
                    if data_dict['exchange_timestamp']/1000.0 >= datetime.datetime.timestamp(timestamp_five_mins):
                        if is_beginning:
                            is_beginning = False
                        
                        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        i = len(self.parent.df)
                        
                        self.parent.df.loc[i, 'timestamp'] = datetime.datetime.timestamp(timestamp_five_mins)
                        self.parent.df.loc[i, 'date'] = timestamp_five_mins

                        p = 120 
                        q = 320
                        r = 120
                        s = 320
                        index = 1

                        self.parent.df = strategy_impl.calculate_heiken_values(self.parent.df)
                        self.parent.df = strategy_impl.ichimoku_cloud(self.parent.df, p, q, r, s, index)

                        #print(strategy_impl.get_df())

                        timestamp_five_mins = timestamp_five_mins + datetime.timedelta(minutes = 5)


                        open_price = ltp

                        high_price = open_price
                        low_price = open_price
                        close_price = open_price


                        self.parent.df.loc[i, 'open'] = open_price
                        self.parent.df.loc[i, 'close'] = close_price
                        self.parent.df.loc[i, 'high'] = high_price
                        self.parent.df.loc[i, 'low'] = low_price


                        ######################################################################
                        #STRATEGY IMPLEMENTATION
                        #...
                        ######################################################################
                        
                        print(self.parent.df[['date', 'h_open', 'h_high', 'h_low', 'final_signal']])

                        need_request = True


                    #print(str(pd.to_datetime(int(data_dict['exchange_timestamp'])/1000, unit='s').replace(microsecond=0, nanosecond=0)+datetime.timedelta(hours=5, minutes=30)) + " " + str(ltp))
                    close_price = ltp
                    low_price = min(low_price, ltp)
                    high_price = max(high_price, ltp)
                    if not is_beginning:
                        l = len(self.parent.df) - 1
                        self.parent.df.loc[l, 'close'] = close_price
                        self.parent.df.loc[l, 'high'] = high_price
                        self.parent.df.loc[l, 'low'] = low_price
                        self.parent.df.loc[l, 'timestamp'] = int(data_dict['exchange_timestamp'])/1000

                    #print("finished data")

                        if datetime.datetime.now(pytz.timezone("Asia/Kolkata")) - timestamp_five_mins > datetime.timedelta(seconds=2) and need_request == True:

                            need_request = False

                            todate = datetime.datetime.now(pytz.timezone("Asia/Kolkata")) + datetime.timedelta(minutes=1)
                            data = self.historical_api.get_historical_data(datetime.datetime.strptime(str(timestamp_five_mins.replace(second=0, microsecond=0))[:-6], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(minutes=5), todate)
                            print(data)

                            l = len(self.parent.df) - 2
                            ld = len(data) - 2

                            self.parent.df.loc[l, 'open'] = data.at[ld, 'open']
                            self.parent.df.loc[l, 'close'] = data.at[ld, 'close']
                            self.parent.df.loc[l, 'high'] = data.at[ld, 'high']
                            self.parent.df.loc[l, 'low'] = data.at[ld, 'low']

                            self.parent.df.loc[l + 1, 'open'] = data.at[ld + 1, 'open']

                        self.parent.df = strategy_impl.cj_strategy_base_line(self.parent.df, len(self.parent.df) - 2, index, ltp)






                else:
                    self.parent.release_lock()