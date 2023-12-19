import pandas as pd
import datetime
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import time
import pytz
import xlwings as xw

from api.strategy_implementation import StrategyImplementation

class HistoricalNiftyData:

    def __init__(self):
        self.login()

        self.p = 120 
        self.q = 320
        self.r = 120
        self.s = 320
        self.index = 1


    def get_historical_data_to_excel(self, symboltoken, ws):

        fromdate = self.get_last_timestamp_from_file(ws).replace(tzinfo=pytz.timezone("Asia/Kolkata"))
        todate = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        data = self.get_historical_data(fromdate, todate, symboltoken)

        strategy_impl = StrategyImplementation(data)
        data = strategy_impl.calculate_heiken_values(data)
        data = strategy_impl.ichimoku_cloud(data, self.p, self.q, self.r, self.s, self.index)
        for i in range (3, len(data)):
            data = strategy_impl.cj_strategy_base_line(data, i, self.index, False)


        print(data)
        if (self.len_df == 0):
            startrow = 2
        else:
            startrow = self.len_df

        ws["A"+str(startrow)].options(pd.DataFrame, header=False, index=False, expand='table').value = data


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
        

        data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])

        while todate > fromdate:
            print("New request. Token: " + str(symboltoken))
            print("New request. End date: " + todate.strftime("%Y-%m-%d %H:%M"))
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
            time.sleep(0.34)

        print("Finished reading data")
        try:
            logout=self.obj.terminateSession(self.user_id)
            print("Logout Successfull")
        except Exception as e:
            print("Logout failed: {}".format(e.message))
        
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
        return data_piece


    def get_last_timestamp_from_file(self, ws):

        df = ws['A1'].expand().options(pd.DataFrame).value
        print(df)
        self.len_df = len(df)
                    
        if self.len_df == 0:
            self.len_df = 0
            return datetime.datetime.strptime("2023-09-01 09:15", '%Y-%m-%d %H:%M')

        last_timestamp = ws.range('A' + str(self.len_df)).value
        print(last_timestamp)
        return last_timestamp
         




