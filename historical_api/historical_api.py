import pandas as pd
import datetime
import pyotp
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2



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


try:
    historicParam={
    "exchange": "NFO",
    "symboltoken": "35079",
    "interval": "FIVE_MINUTE",
    "fromdate": "2023-10-25 14:45",
    "todate": "2023-10-25 15:00"
    }
    print(obj.getCandleData(historicParam))
except Exception as e:
    print("Historic Api failed: {}".format(e.message))
#logout
try:
    logout=obj.terminateSession(user_id)
    print("Logout Successfull")
except Exception as e:
    print("Logout failed: {}".format(e.message))

