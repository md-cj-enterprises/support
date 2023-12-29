import pandas as pd
import datetime
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import time
import pytz
import xlwings as xw
import threading


class HistoricalApi():

    def __init__(self):
        self.login()

        self.p = 120 
        self.q = 320
        self.r = 120
        self.s = 320
        self.index = 1
        self.queueLock = threading.Lock()


        self.last_call = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).timestamp()

    def concat_excel_and_api(self, excel_df, api_df):
        start_date = excel_df.at[len(excel_df) - 1, 'date']
        index_in_api_df_list = api_df.index[api_df['date'] == start_date].tolist()
        print(str(start_date))
        print(index_in_api_df_list)
        print(api_df)
        if len(index_in_api_df_list) != 0:
            index_in_api_df = index_in_api_df_list[0]
        else:
            index_in_api_df = -1
        return pd.concat([excel_df, api_df[index_in_api_df+1:]], ignore_index=True)

    def get_historical_data_to_excel(self, symboltoken, ws):

        fromdate = self.get_last_timestamp_from_file(ws).replace(tzinfo=pytz.timezone("Asia/Kolkata"))
        todate = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        data = self.get_historical_data(fromdate, todate, symboltoken)

        rng = ws.range('A1')
        len_df = 0
        if (rng.value == 'date'):
            df = ws['A1'].expand().options(pd.DataFrame, index = False).value
            len_df = len(df) - 3
            data = self.concat_excel_and_api(df, data)
            #data = pd.concat([df, data], ignore_index=True)
        else:
            data['profit'] = ""
            data['final_signal'] = ""
            data['exit_point'] = ""
            data['signal'] = ""
            data['entry_point'] = ""
            data['entry_position'] = ""
            data['stop_loss'] = ""
            data['signal_type'] = ""
            data['turn_to0'] = ""
            data['trade_time'] = ""
            data['ltp'] = ""
            data['p3_switch'] = ""


        return data


    def login(self):
        print("TRYING TO LOGIN")
        otp_token = pyotp.TOTP("TYDDSO524WNIPNWULFYQHWTSIM").now()
        api_key = "7CLGxF6D"
        self.user_id = "S51426088"
        pin = "2638"

        self.obj = SmartConnect(api_key)
        data = self.obj.generateSession(self.user_id, pin, otp_token)
        print("GENERATED SESSION")
        refreshToken = data['data']['refreshToken']
        feedToken = self.obj.getfeedToken()
        authToken = data['data']['jwtToken']
        userProfile = self.obj.getProfile(refreshToken)

        sws = SmartWebSocketV2(authToken, api_key, self.user_id, feedToken)


    def get_historical_data(self, fromdate, todate, symboltoken):
        self.queueLock.acquire()
        time.sleep(0.8)
        while datetime.datetime.now(pytz.timezone("Asia/Kolkata")).timestamp() - self.last_call < 0.4:
            continue


        data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])

        while todate > fromdate:
            print("New request. Token: " + str(symboltoken))
            #print("New request. End date: " + todate.strftime("%Y-%m-%d %H:%M"))
            try:
                historicParam={
                "exchange": "NFO",
                "symboltoken": symboltoken,
                "interval": "FIVE_MINUTE",
                "fromdate": str(fromdate)[:-9],
                "todate": todate.strftime("%Y-%m-%d %H:%M")
                }
                message = self.obj.getCandleData(historicParam)
                #print(message)
                if (message['data'] == None):
                    break
                data_piece = self.add_api_response_to_dataframe(message['data'])
                data = pd.concat([data_piece, data], ignore_index=True)

                todate = data.at[0, 'date'].replace(tzinfo=pytz.timezone("Asia/Kolkata")) - datetime.timedelta(minutes=5)
            except Exception as e:
                print("Historic Api failed: {}".format(e.message))
            time.sleep(0.4)
        self.last_call = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).timestamp()
        #print("Finished reading data")
        try:
            logout=self.obj.terminateSession(self.user_id)
            print("Logout Successfull")
        except Exception as e:
            print("Logout failed: {}".format(e.message))
        self.queueLock.release()


        return data


    def add_api_response_to_dataframe(self, message):
        data_piece = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])

        for i in message:
            index = len(data_piece)
            data_piece.loc[index, 'date'] = datetime.datetime.strptime(i[0].replace('T', ' ').replace('+05:30', '')[:-3], '%Y-%m-%d %H:%M')
            data_piece.loc[index, 'open'] = i[1]
            data_piece.loc[index, 'high'] = i[2]
            data_piece.loc[index, 'low'] = i[3]
            data_piece.loc[index, 'close'] = i[4]
        #print("PIECE")
        #print(data_piece)
        return data_piece


    def get_last_timestamp_from_file(self, ws):

        df = ws['A1'].expand().options(pd.DataFrame).value
        len_df = len(df)
                    
        if len_df == 0:
            len_df = 0
            return datetime.datetime.strptime("2023-12-15 09:15", '%Y-%m-%d %H:%M')

        last_timestamp = ws.range('A' + str(len_df)).value
        return last_timestamp
         





