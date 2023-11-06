import pandas as pd
import datetime
import threading
import pytz
import xlwings as xw

from .strategy_implementation import StrategyImplementation

class ProcessLiveData (threading.Thread):
        def __init__(self, threadID, name, parent, historical_api):
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.name = name
            self.exitFlag = False
            self.parent = parent
            self.historical_api = historical_api

            self.p = 120 
            self.q = 320
            self.r = 120
            self.s = 320
            self.index = 1


        def run(self):
            wb = xw.Book('historical_nifty_data_live_update.xlsx')
            worksheet = wb.sheets('Sheet')

            self.ws = worksheet

            print("Starting " + self.name)
            self.process_data(self.name)
            print("Exiting " + self.name)

        def process_data(self, threadName):

            is_beginning = True
            need_request = True
            open_price = None
            close_price = None
            is_written = False
            high_price = -1
            low_price = 10000000000

            timestamp_five_mins = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            print(timestamp_five_mins)
            if (timestamp_five_mins.hour < 9) or (timestamp_five_mins.hour == 9 and timestamp_five_mins.minute < 15):
                timestamp_five_mins.replace(hour=9, minute=15, second=0, microsecond=0)
                is_beginning = False
            else: 
                if timestamp_five_mins.minute >= 55:
                    timestamp_five_mins = timestamp_five_mins.replace(minute=0, second = 0, microsecond=0, hour = timestamp_five_mins.hour + 1)
                else:
                    timestamp_five_mins = timestamp_five_mins.replace(minute=(timestamp_five_mins.minute//5 + 1)*5, second = 0, microsecond=0)
            
            strategy_impl = StrategyImplementation(self.parent.df)

            while not self.exitFlag:
                self.parent.acquire_lock()
                if not self.parent.getWorkQueue().empty():

                    messg = self.parent.getWorkQueue().get()
                    self.parent.release_lock()
                    if (datetime.datetime.now(pytz.timezone("Asia/Kolkata")).hour < 9) or (datetime.datetime.now(pytz.timezone("Asia/Kolkata")).hour == 9 and datetime.datetime.now(pytz.timezone("Asia/Kolkata")).minute < 15):
                        continue
                    data_dict = messg
                    if data_dict == b'\x00':
                        continue
                    #date = datetime.datetime.fromtimestamp(int(data_dict['exchange_timestamp'])/1000.0)
                    #print(str(date)+" "+str(datetime.datetime.now()))
                    ltp = int(data_dict['last_traded_price'])/100
                    if data_dict['exchange_timestamp']/1000.0 >= datetime.datetime.timestamp(timestamp_five_mins):
                        if is_beginning:
                            is_beginning = False
                        
                        i = len(self.parent.df)
                        
                        self.parent.df.loc[i, 'timestamp'] = datetime.datetime.timestamp(timestamp_five_mins)
                        self.parent.df.loc[i, 'date'] = timestamp_five_mins.replace(tzinfo=None)

                        self.parent.df = strategy_impl.calculate_heiken_values(self.parent.df)
                        self.parent.df = strategy_impl.ichimoku_cloud(self.parent.df, self.p, self.q, self.r, self.s, self.index)

                        timestamp_five_mins = timestamp_five_mins + datetime.timedelta(minutes = 5)

                        open_price = ltp
                        high_price = open_price
                        low_price = open_price
                        close_price = open_price


                        self.parent.df.loc[i, 'open'] = open_price
                        self.parent.df.loc[i, 'close'] = close_price
                        self.parent.df.loc[i, 'high'] = high_price
                        self.parent.df.loc[i, 'low'] = low_price

                        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        print(self.parent.df[['date', 'h_open', 'h_high', 'h_low', 'final_signal']])

                        need_request = True

                    print(str(pd.to_datetime(int(data_dict['exchange_timestamp'])/1000, unit='s').replace(microsecond=0, nanosecond=0)+datetime.timedelta(hours=5, minutes=30)) + " " + str(ltp))
                    close_price = ltp
                    low_price = min(low_price, ltp)
                    high_price = max(high_price, ltp)

                    #if not is_beginning:
                    #l = len(self.parent.df) - 1
                    #self.parent.df.loc[l, 'close'] = close_price
                    #self.parent.df.loc[l, 'high'] = high_price
                    #self.parent.df.loc[l, 'low'] = low_price
                    #self.parent.df.loc[l, 'timestamp'] = int(data_dict['exchange_timestamp'])/1000

                #print("finished data")
                    if datetime.datetime.timestamp(timestamp_five_mins) - data_dict['exchange_timestamp']/1000.0 <= 298 and datetime.datetime.timestamp(timestamp_five_mins) - data_dict['exchange_timestamp']/1000.0 > 295 and need_request == True:

                        todate = datetime.datetime.now(pytz.timezone("Asia/Kolkata")) + datetime.timedelta(minutes=1)
                        data = self.historical_api.get_historical_data(timestamp_five_mins - datetime.timedelta(minutes=10), todate)
                        print("GOT HISORICAL CANDLES: ")
                        print(data)
                        need_request = False
                        l = len(self.parent.df) - 2

                        if (len(data) != 1):
                            
                            ld = len(data) - 2
                            #self.parent.df.loc[l + 1, 'open'] = data.at[ld + 1, 'open']
                        
                        else:
                            ld = len(data) - 1
                        
                        self.parent.df.loc[l, 'open'] = data.at[ld, 'open']
                        self.parent.df.loc[l, 'close'] = data.at[ld, 'close']
                        self.parent.df.loc[l, 'high'] = data.at[ld, 'high']
                        self.parent.df.loc[l, 'low'] = data.at[ld, 'low']

                        print("FINISHED")
                        print(self.parent.df)
                        print(self.parent.df[['date', 'open', 'high', 'low', 'close', 'profit', 'final_signal', 'exit_point', 'signal', 'entry_point', 'entry_position', 'stop_loss', 'signal_type', 'entry_point_temp', 'stop_loss_temp', 'turn_to0', 'trade_type', 'exit_type', 'exit_position']].iloc[[l]]
)
                        if not is_written:
                            startrow = len(self.parent.df)
                            is_written = True
                        else:
                            startrow = len(self.parent.df) + 1
                        
                        self.ws.range('A' + str(startrow)).options(expand='table', index = False, header = False).value = self.parent.df[['date', 'open', 'high', 'low', 'close', 'profit', 'final_signal', 'exit_point', 'signal', 'entry_point', 'entry_position', 'stop_loss', 'signal_type', 'entry_point_temp', 'stop_loss_temp', 'turn_to0', 'trade_type', 'exit_type', 'exit_position']].iloc[[l]]

                        print("WROTE TO FILE")

                    if not is_beginning:
                        self.parent.df = strategy_impl.cj_strategy_base_line(self.parent.df, len(self.parent.df) - 2, self.index, ltp)
                        self.parent.add_marks_ids_to_df(len(self.parent.df) - 2)

                else:
                    self.parent.release_lock()