from __future__ import print_function
import pandas as pd
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import datetime
import queue
import threading

class LiveNiftyData:
    def __init__(self):
        print("Hello")

    def read_data_from_file(self, file_name):
        self.df = pd.read_excel(file_name, parse_dates=True)
        self.df['signal'] = 0
        self.df['final_signal'] = 0
        self.df['entry_point'] = 0
        self.df['exit_point'] = 0
        self.df['stop_loss'] = 0
        self.df['profit'] = 0
    
    def parse(self, msg):   
        self.queueLock.acquire()
        self.workQueue.put(msg)
        self.queueLock.release()

    def on_data(self, wsapp, message):  
        #print("Ticks: {}".format(message))
        self.parse(message)

    def on_open(self, wsapp):
        print("on open")
        correlation_id = "test"
        mode = 1
        token_list = [{"exchangeType": 13, "tokens": ["5"]}]
        self.sws.subscribe(correlation_id, mode, token_list)

    def on_error(wsapp, error):
        print(error)


    def on_close(wsapp):
        print("Close")
    
    def acquire_lock(self):
        self.queueLock.acquire()

    def release_lock(self):
        self.queueLock.release()

    def getWorkQueue(self):
        return self.workQueue


    
    class myThread (threading.Thread):
        def __init__(self, threadID, name, q, parent):
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.name = name
            self.q = q
            self.exitFlag = False
            self.parent = parent

        def run(self):
            print("Starting " + self.name)
            self.process_data(self.name, self.q)
            print("Exiting " + self.name)

        def process_data(self, threadName, q):
            print(self)
            is_beginning = True
            open_price = None
            close_price = None
            high_price = -1
            low_price = 10000000

            timestamp_five_mins = datetime.datetime.now()
            if timestamp_five_mins.minute >= 55:
                timestamp_five_mins = timestamp_five_mins.replace(minute=0, hour = timestamp_five_mins.hour + 1)
            else:
                timestamp_five_mins = timestamp_five_mins.replace(minute=(timestamp_five_mins.minute//5 + 1)*5, second = 0, microsecond=0)


            while not self.exitFlag:
                self.parent.acquire_lock()
                if not self.parent.getWorkQueue().empty():

                    messg = q.get()
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

    
    def get_live_data(self):
        print("Starting reading live data...")
        threadList = ["Thread-1"]
        self.queueLock = threading.Lock()
        self.workQueue = queue.Queue(10)
        threads = []
        threadID = 1

        # Create new threads
        for tName in threadList:
            print("Creating thread")
            thread = self.myThread(threadID, tName, self.workQueue, self)
            thread.start()
            threads.append(thread)
            threadID += 1

        otp_token = pyotp.TOTP("TYDDSO524WNIPNWULFYQHWTSIM").now()
        api_key = "AQNph3o7"
        user_id = "S51426088"
        pin = "2638"




        obj = SmartConnect(api_key)
        data = obj.generateSession(user_id, pin, otp_token)
        #print(data)
        refreshToken = data['data']['refreshToken']
        feedToken = obj.getfeedToken()
        authToken = data['data']['jwtToken']
        #print(feedToken)
        userProfile = obj.getProfile(refreshToken)
        # #print(userProfile)
        AUTH_TOKEN = authToken
        API_KEY = api_key
        CLIENT_CODE = user_id
        FEED_TOKEN = feedToken
        self.sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, FEED_TOKEN)

        ##############################################################################
            

        # Assign the callbacks.
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close

        self.sws.connect()
            
    def get_data(self):
        return self.df



