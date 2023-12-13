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
#import pythoncom
#import win32com.client


class LiveNiftyData (threading.Thread):

    def __init__(self, threadID, name, historical_api):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.historical_api = historical_api
        self.max_mark_id = 0

    def run(self):
        wb = xw.Book('historical_nifty_data_live_update.xlsx')
        worksheet = wb.sheets('Sheet')

        self.ws = worksheet
        self.open_file_with_data("./historical_nifty_data.xlsx")


        self.read_data_from_file(self.file_name)
        for i in range(len(self.df)):
            self.add_marks_ids_to_df(i)
        
        self.get_live_data()

    def read_data_from_file(self, file_name):
        self.file_name = file_name
        self.df = self.ws['A1'].expand().options(pd.DataFrame, index = False).value
        print("from live")
        print(self.df)
        self.df['timestamp'] = self.df["date"]
        local = pytz.timezone("Asia/Kolkata")
        #self.df.timestamp =  self.df.timestamp.apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
        self.df.timestamp = self.df.timestamp.apply(lambda x: local.localize(x, is_dst=None))
        self.df.timestamp = self.df.timestamp.apply(lambda x:  int(round(x.timestamp())))
        self.df['marks_ids'] = -1
        self.df['marks_ids'] = self.df['marks_ids'].astype('object')



    def add_marks_ids_to_df(self, i):
        marks_list = []
        temp_mark = self.max_mark_id
        if self.df.at[i, 'final_signal'] != 0 and not pd.isnull(self.df.at[i, 'final_signal']):
            marks_list.append(temp_mark)
            temp_mark+=1
            if self.df.at[i, 'final_signal'] == 3 or self.df.at[i, 'final_signal'] == -3:
                marks_list.append(temp_mark)
                temp_mark+=1
        if self.df.at[i, 'exit_point'] != 0 and not pd.isnull(self.df.at[i, 'exit_point']):
            marks_list.append(temp_mark)
            temp_mark+=1
        if self.df.at[i, 'entry_position'] != 0 and not pd.isnull(self.df.at[i, 'entry_position']):
            marks_list.append(temp_mark)
            temp_mark+=1
        if self.df.at[i, 'stop_loss'] != 0 and not pd.isnull(self.df.at[i, 'stop_loss']):
            marks_list.append(temp_mark)
            temp_mark+=1
        if self.df.at[i, 'entry_point']  != 0 and not pd.isnull(self.df.at[i, 'entry_point']):
            marks_list.append(temp_mark)
            temp_mark+=1
        if self.df.at[i, 'turn_to0'] != 0 and not pd.isnull(self.df.at[i, 'turn_to0']):
            marks_list.append(temp_mark)
            temp_mark+=1

        if len(marks_list) == 0:
            self.df.at[i, 'marks_ids'] = -1
            return
        elif self.df.at[i, 'marks_ids'] == -1 or pd.isnull(self.df.at[i, 'marks_ids']):
            self.df.at[i, 'marks_ids'] = marks_list
            self.max_mark_id = temp_mark
            return
        elif len(self.df.at[i, 'marks_ids']) != len(marks_list):
            self.df.at[i, 'marks_ids'] = marks_list
            self.max_mark_id = temp_mark
            return

    def open_file_with_data(self, file_name):
        self.file_name = file_name

        rng = self.ws.range('A1')
        print(rng.value)
        if (rng.value == 'date'):
            self.read_data_from_file(file_name)
        else:
            self.df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])
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

            self.ws.range('A1').options(expand='table', index = False).value = self.df


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
        token_list = [{"exchangeType": 2, "tokens": ["63197"]}]
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

        self.queueLock = threading.Lock()
        self.workQueue = queue.Queue(10000)
        threadID = 1

        # Create new thread
        thread = ProcessLiveData(threadID, 'ProcessThread', self, self.historical_api)
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



