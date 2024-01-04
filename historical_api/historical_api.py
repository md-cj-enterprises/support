import pandas as pd
import datetime
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import time

def add_api_response_to_dataframe(message):
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


otp_token = pyotp.TOTP("TYDDSO524WNIPNWULFYQHWTSIM").now()
api_key = "7CLGxF6D"
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
sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, FEED_TOKEN)


data = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close'])
todate = datetime.datetime.strptime("2023-12-25 14:45", '%Y-%m-%d %H:%M')
fromdate = datetime.datetime.strptime("2022-9-25 14:45", '%Y-%m-%d %H:%M')
symboltoken = "55317"
print(fromdate)

while todate > fromdate:
    print("New request. Token: " + str(symboltoken))
    #print("New request. End date: " + todate.strftime("%Y-%m-%d %H:%M"))
    try:
        historicParam={
        "exchange": "NFO",
        "symboltoken": symboltoken,
        "interval": "FIVE_MINUTE",
        "fromdate": str(fromdate)[:-3],
        "todate": str(todate)[:-3]
        }
        message = obj.getCandleData(historicParam)
        print(message)
        if (message['data'] == None):
            break
        data_piece = add_api_response_to_dataframe(message['data'])
        data = pd.concat([data_piece, data], ignore_index=True)

        todate = data.at[0, 'date'] - datetime.timedelta(minutes=5)
    except Exception as e:
        print("Historic Api failed: {}".format(e.message))
    time.sleep(0.5)
print("Finished reading data")

data.to_excel("data.xlsx", index = False)
try:
    logout=obj.terminateSession(user_id)
    print("Logout Successfull")
except Exception as e:
    print("Logout failed: {}".format(e.message))
