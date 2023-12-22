import pandas as pd
import datetime
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import time
import pytz
import xlwings as xw
import threading

from api.strategy_implementation import StrategyImplementation

class HistoricalNiftyData(threading.Thread):

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
        start_date = api_df.at[0, 'date']
        index_in_excel_df = excel_df.index[excel_df['date'] == str(start_date)].tolist()[0]
        return pd.concat([excel_df[0:index_in_excel_df], api_df], ignore_index=True)

    def get_historical_data_to_excel(self, symboltoken, ws):

        fromdate = self.get_last_timestamp_from_file(ws).replace(tzinfo=pytz.timezone("Asia/Kolkata"))
        todate = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        data = self.get_historical_data(fromdate, todate, symboltoken)

        rng = ws.range('A1')
        if (rng.value == 'date'):
            df = ws['A1'].expand().options(pd.DataFrame, index = False).value
            data = self.concat_excel_and_api(df, data)
            #data = pd.concat([df, data], ignore_index=True)
        else:
            data['profit'] = 0
            data['final_signal'] = 0
            data['exit_point'] = 0
            data['signal'] = 0
            data['entry_point'] = 0
            data['entry_position'] = 0
            data['stop_loss'] = 0
            data['signal_type'] = 0
            data['entry_point_temp'] = 0
            data['stop_loss_temp'] = 0
            data['turn_to0'] = 0
            data['trade_type'] = 0
            data['exit_type'] = 0
            data['exit_position'] = 0


        strategy_impl = StrategyImplementation(data, True)
        data = strategy_impl.calculate_heiken_values(data)
        data = strategy_impl.ichimoku_cloud(data, self.p, self.q, self.r, self.s, self.index)
        for i in range (3, len(data)):
            data = strategy_impl.cj_strategy_base_line(data, i, self.index, False)
        data = data.replace(0, "")

        print(data)
        #if (self.len_df == 0):
        startrow = 1
        #else:
            #startrow = self.len_df
        

        ws["A"+str(startrow)].options(pd.DataFrame, header=True, index=False, expand='table').value = data[['date', 'open', 'high', 'low', 'close', 'h_open', 'h_high', 'h_low', 'h_close', 'profit', 'final_signal', 'exit_point', 'signal', 'entry_point', 'entry_position', 'stop_loss', 'signal_type', 'entry_point_temp', 'stop_loss_temp', 'turn_to0', 'trade_type', 'exit_type', 'exit_position']]


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
        time.sleep(1)
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
        self.len_df = len(df)
                    
        if self.len_df == 0:
            self.len_df = 0
            return datetime.datetime.strptime("2023-11-21 09:15", '%Y-%m-%d %H:%M')

        last_timestamp = ws.range('A' + str(self.len_df)).value
        return last_timestamp
         




