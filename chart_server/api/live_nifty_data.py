from __future__ import print_function
import pandas as pd
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import queue
import threading
from .process_live_data import ProcessLiveData
import pytz
import xlwings as xw
import numpy as np

class LiveNiftyData (threading.Thread):

    def __init__(self, threadID, name, tokens, names, historical_api):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.tokens = tokens
        self.names = names
        self.historical_api = historical_api
        #self.max_mark_id = 0

    def run(self):
        wb = xw.Book('historical_nifty_data_live_update.xlsx')

        self.df_list = []
        for k in range (len(self.names)):
            worksheet = wb.sheets(self.names[k])
            self.df_list.append(self.read_data_from_file(worksheet))
        self.get_live_data()

    def read_data_from_file(self, ws):
        df_i = ws['A1'].expand().options(pd.DataFrame, index = False, header = True).value
        df_i['timestamp'] = df_i["date"]
        local = pytz.timezone("Asia/Kolkata")
        df_i.timestamp = df_i.timestamp.apply(lambda x: local.localize(x, is_dst=None))
        df_i.timestamp = df_i.timestamp.apply(lambda x:  int(round(x.timestamp())))
        return df_i

    def parse(self, msg):   
        self.queueLock.acquire()
        self.workQueue.put(msg)
        self.queueLock.release()

    def on_data(self, wsapp, message):  
        #print("Ticks")
        self.parse(message)

    def on_open(self, wsapp):
        print("on open")
        correlation_id = "test"
        mode = 1
        token_list = [{"exchangeType": 2, "tokens": self.tokens}]
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
        print(self.names)

        self.queueLock = threading.Lock()
        self.workQueue = queue.Queue(10000)

        # Create new thread
        for t in range(len(self.tokens)):
            thread = ProcessLiveData(self.threadID, self.tokens[t], self.names[t], self, self.historical_api, self.df_list[t])
            thread.start()
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
        print("login")
        while True:
            self.sws.connect()

    def get_data(self):
        return self.df