from __future__ import print_function
import pandas as pd
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import queue
import threading
from .process_live_data import ProcessLiveData
import datetime
import pytz

class LiveNiftyData (threading.Thread):

    def __init__(self, threadID, name, historical_api):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.historical_api = historical_api
    
    def run(self):
        self.read_data_from_file("/Users/alice/Codes/trading/server/support/chart_server/api/live_nifty_data.xlsx")
        self.get_live_data()

    def read_data_from_file(self, file_name):
        self.df = pd.read_excel(file_name, parse_dates=True)
        self.df['timestamp'] = self.df["date"]
        local = pytz.timezone("Asia/Kolkata")
        #self.df.timestamp =  self.df.timestamp.apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
        self.df.timestamp = self.df.timestamp.apply(lambda x: local.localize(x, is_dst=None))
        self.df.timestamp = self.df.timestamp.apply(lambda x:  int(round(x.timestamp())))


        self.df['profit'] = 0
        self.df['final_signal'] = 0
        self.df['exit_point'] = 0
        self.df['signal'] = 0
        self.df['entry_point'] = 0
        self.df['entry_position'] = 0
        self.df['stop_loss'] = 0
        self.df['signal_type'] = 0
        self.df['entry_point_temp'] = 0
        self.df['stop_loss_temp'] = 0
        self.df['turn_to0'] = 0
        self.df['trade_type'] = 0
        self.df['exit_type'] = 0
        self.df['exit_position'] = 0
        #self.df['timestamp'] = 0

    
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
        token_list = [{"exchangeType": 2, "tokens": ["57920"]}]
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

    
    def get_live_data(self):
        print("Starting reading live data...")
        threadList = ["Thread-1"]
        self.queueLock = threading.Lock()
        self.workQueue = queue.Queue(10)
        threads = []
        threadID = 1

        # Create new threads
        for tName in threadList:
            thread = ProcessLiveData(threadID, tName, self, self.historical_api)
            thread.start()
            threads.append(thread)
            threadID += 1

        self.login()

    def login(self):

        otp_token = pyotp.TOTP("TYDDSO524WNIPNWULFYQHWTSIM").now()
        api_key = "AQNph3o7"
        user_id = "S51426088"
        pin = "2638"

        obj = SmartConnect(api_key)
        data = obj.generateSession(user_id, pin, otp_token)
        refreshToken = data['data']['refreshToken']
        feedToken = obj.getfeedToken()
        authToken = data['data']['jwtToken']
        userProfile = obj.getProfile(refreshToken)

        self.sws = SmartWebSocketV2(authToken, api_key, user_id, feedToken)
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close
        self.sws.connect()

            
    def get_data(self):
        return self.df



