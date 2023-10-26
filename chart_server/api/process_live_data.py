import pandas as pd
import datetime
import threading

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

            timestamp_five_mins = datetime.datetime.now()
            if timestamp_five_mins.minute >= 55:
                timestamp_five_mins = timestamp_five_mins.replace(minute=0, hour = timestamp_five_mins.hour + 1)
            else:
                timestamp_five_mins = timestamp_five_mins.replace(minute=(timestamp_five_mins.minute//5 + 1)*5, second = 0, microsecond=0)


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
                        
                        print(self.parent.df[['date', 'open', 'high', 'low', 'close']])


                    print(str(pd.to_datetime(int(data_dict['exchange_timestamp'])/1000, unit='s').replace(microsecond=0, nanosecond=0)) + " " + str(ltp))
                    close_price = ltp
                    low_price = min(low_price, ltp)
                    high_price = max(high_price, ltp)
                    if not is_beginning:
                        l = len(self.parent.df) - 1
                        self.parent.df.loc[l, 'close'] = close_price
                        self.parent.df.loc[l, 'high'] = high_price
                        self.parent.df.loc[l, 'low'] = low_price
                        self.parent.df.loc[l, 'timestamp'] = int(data_dict['exchange_timestamp'])/1000
                    ltp_prev = ltp

                    #print("finished data")


                else:
                    self.parent.release_lock()