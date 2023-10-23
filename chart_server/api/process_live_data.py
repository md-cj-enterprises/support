
import datetime
import threading

class ProcessLiveData (threading.Thread):
        def __init__(self, threadID, name, parent):
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.name = name
            self.exitFlag = False
            self.parent = parent

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
                    date = datetime.datetime.fromtimestamp(int(data_dict['exchange_timestamp'])/1000.0)
                    #print(str(date)+" "+str(datetime.datetime.now()))
                    if is_beginning:
                        open_price = data_dict['last_traded_price']
                        is_beginning = False
                    if data_dict['exchange_timestamp']/1000.0 > datetime.datetime.timestamp(timestamp_five_mins):
                        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        i = len(self.parent.df)
                        self.parent.df.loc[i, 'date'] = timestamp_five_mins
                        self.parent.df.loc[i, 'timestamp'] = datetime.datetime.timestamp(timestamp_five_mins)
                        self.parent.df.loc[i, 'open'] = open_price
                        self.parent.df.loc[i, 'close'] = close_price
                        self.parent.df.loc[i, 'high'] = high_price
                        self.parent.df.loc[i, 'low'] = low_price


                        ######################################################################
                        #STRATEGY IMPLEMENTATION
                        #...
                        ######################################################################
                        
                        print(self.parent.df[['date', 'open', 'high', 'low', 'close']])
                        timestamp_five_mins = timestamp_five_mins + datetime.timedelta(minutes = 5)
                        open_price = data_dict['last_traded_price']
                        high_price = open_price
                        low_price = open_price

                    close_price = data_dict['last_traded_price']
                    low_price = min(low_price, data_dict['last_traded_price'])
                    high_price = max(high_price, data_dict['last_traded_price'])
                    #print("finished data")


                else:
                    self.parent.release_lock()