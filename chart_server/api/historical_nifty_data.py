import pandas as pd
import datetime
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import time
import pytz
import os

class HistoricalNiftyData:

    def __init__(self, file_name):
        self.file_name = file_name
        self.login()

    def get_historical_data_to_excel(self):

        fromdate = self.get_last_timestamp_from_file().replace(tzinfo=pytz.timezone("Asia/Kolkata"))
        todate = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        data = self.get_historical_data(fromdate, todate)


        print(data)
        if (self.len_df == 0):
            startrow = 1
        else:
            startrow = self.len_df
        with pd.ExcelWriter(self.file_name, mode="a", engine="openpyxl", if_sheet_exists="overlay") as writer:
            data.to_excel(writer, sheet_name="Sheet1", startrow=startrow, header=False, index=False)  


    def login(self):
        otp_token = pyotp.TOTP("TYDDSO524WNIPNWULFYQHWTSIM").now()
        api_key = "7CLGxF6D"
        self.user_id = "S51426088"
        pin = "2638"

        self.obj = SmartConnect(api_key)
        data = self.obj.generateSession(self.user_id, pin, otp_token)
        refreshToken = data['data']['refreshToken']
        feedToken = self.obj.getfeedToken()
        authToken = data['data']['jwtToken']
        userProfile = self.obj.getProfile(refreshToken)

        sws = SmartWebSocketV2(authToken, api_key, self.user_id, feedToken)


    def get_historical_data(self, fromdate, todate):
        time.sleep(1)

        data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])

        while todate > fromdate:
            print("New request. End date: " + todate.strftime("%Y-%m-%d %H:%M"))
            try:
                historicParam={
                "exchange": "NFO",
                "symboltoken": "57920",
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


    def get_last_timestamp_from_file(self):
        df = pd.read_excel(self.file_name, parse_dates=True)
        print(df)
        self.len_df = len(df)
        if self.len_df == 0:
            return datetime.datetime.strptime("2023-01-01 09:15", '%Y-%m-%d %H:%M')

        last_timestamp = df.at[len(df) - 1, 'date']
        print(last_timestamp)
        return last_timestamp
         




