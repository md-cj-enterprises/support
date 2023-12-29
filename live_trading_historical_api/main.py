import xlwings as xw
import os.path
import openpyxl
import historical_api
import datetime
import pytz
import pandas as pd
import strategy_implementation


token_list = [  "55317",
                "55318",
                "55513",
                "55463",
                "55429",
                "55396",
                "55373",
                "55337",
                "55388",
                "55498",
                "55437",
                "55325",
                "55417",
                "55338",
                "55360",
                "55394",
                "55397",
                "55480",
                "55504",
                "55392",
                "55419",
                "55519",
                "55400",
                "55474",
                "55486",
                "55332",
                "55361",
                "55458",
                "55423",
                "55401",
                "55428",
                "55426",
                "55354"]

names_list = [  "BANKNIFTY25JAN24FUT",
                "NIFTY25JAN24FUT",
                "ULTRACEMCO25JAN24FUT",
                "ONGC25JAN24FUT",
                "L&TFH25JAN24FUT",
                "HEROMOTOCO25JAN24FUT",
                "DIVISLAB25JAN24FUT",
                "AXISBANK25JAN24FUT",
                "GRASIM25JAN24FUT",
                "TATACONSUM25JAN24FUT",
                "M&M25JAN24FUT",
                "ADANIENT25JAN24FUT",
                "INDUSINDBK25JAN24FUT",
                "BAJAJ-AUTO25JAN24FUT",
                "CIPLA25JAN24FUT",
                "HDFCBANK25JAN24FUT",
                "HINDALCO25JAN24FUT",
                "RELIANCE25JAN24FUT",
                "TCS25JAN24FUT",
                "HCLTECH25JAN24FUT",
                "INFY25JAN24FUT",
                "WIPRO25JAN24FUT",
                "HINDUNILVR25JAN24FUT",
                "POWERGRID25JAN24FUT",
                "SBIN25JAN24FUT",
                "ASIANPAINT25JAN24FUT",
                "COALINDIA25JAN24FUT",
                "NESTLEIND25JAN24FUT",
                "ITC25JAN24FUT",
                "ICICIBANK25JAN24FUT",
                "KOTAKBANK25JAN24FUT",
                "JSWSTEEL25JAN24FUT",
                "BRITANNIA25JAN24FUT"]

if len(names_list) != len(token_list):
    print("!!!!!!!,!!!!!!!")

p = 120 
q = 320
r = 120
s = 320
index = 1


if not os.path.isfile("./historical_api_live_update.xlsx"):
    print("creating file")
    wb = openpyxl.Workbook()

    wb.save("./historical_api_live_update.xlsx")
    wb.close()


wb = xw.Book('historical_api_live_update.xlsx')
df_list = []
strategy_impl_list = []


historical_api = historical_api.HistoricalApi()
sheets = [s.name for s in wb.sheets]
print("sheets")
print(sheets)
for i in range(len(names_list)):
    if not names_list[i] in sheets:
        print(names_list[i])

        wb.sheets.add(names_list[i])
        print("???")
        
for i in range(len(names_list)):

    data = historical_api.get_historical_data_to_excel(token_list[i], wb.sheets(names_list[i]))
    data = data[:len(data) - 1]
    print(data)
    df_list.append(data)
    strategy_impl = strategy_implementation.StrategyImplementation(data)
    data = strategy_impl.calculate_heiken_values(data)
    data = strategy_impl.ichimoku_cloud(data, p, q, r, s, index)
    for k in range (3, len(data)):
        data = strategy_impl.cj_strategy_base_line(data, k, index)
    first_cols = ['date','open','high', 'low', 'close', 'h_open', 'h_high', 'h_low', 'h_close']
    last_cols = [col for col in data.columns if col not in first_cols]
    
    data = data[first_cols+last_cols]
    
    #if (len(df) == 0):
    startrow = 1
    #else:
        #startrow = self.len_df
    
    
    wb.sheets(names_list[i])["A"+str(startrow)].options(pd.DataFrame, header=True, index=False, expand='table').value = data


timestamp_five_mins = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))

if (timestamp_five_mins.hour < 9) or (timestamp_five_mins.hour == 9 and timestamp_five_mins.minute < 15):
    timestamp_five_mins = timestamp_five_mins.replace(hour=9, minute=15, second=0, microsecond=0)
    is_beginning = False
else: 
    if timestamp_five_mins.minute >= 55:
        timestamp_five_mins = timestamp_five_mins.replace(minute=0, second = 0, microsecond=0, hour = timestamp_five_mins.hour + 1)
    else:
        timestamp_five_mins = timestamp_five_mins.replace(minute=(timestamp_five_mins.minute//5 + 1)*5, second = 0, microsecond=0)

print(timestamp_five_mins)
while True:
    if datetime.datetime.now(pytz.timezone("Asia/Kolkata")) - timestamp_five_mins > datetime.timedelta(minutes=1, seconds=30):
        print("STARTING READING DATA")
        for i in range(len(names_list)):
            todate = datetime.datetime.now(pytz.timezone("Asia/Kolkata")) + datetime.timedelta(minutes=1)
            data = historical_api.get_historical_data(timestamp_five_mins - datetime.timedelta(minutes=10), todate, token_list[i])
            print(data)
            
            l = len(df_list[i])

            if (len(data) != 1):
                
                ld = len(data) - 2
            
            else:
                ld = len(data) - 1
            if timestamp_five_mins.replace(tzinfo=None) - df_list[i].at[len(df_list[i]) - 1, 'date'] > datetime.timedelta(minutes = 9):
                df_list[i].loc[l, 'timestamp'] = datetime.datetime.timestamp(timestamp_five_mins - datetime.timedelta(minutes = 10))
                df_list[i].loc[l, 'date'] = timestamp_five_mins.replace(tzinfo=None) - datetime.timedelta(minutes = 10)
                df_list[i].loc[l, 'open'] = data.at[ld - 1, 'open']
                df_list[i].loc[l, 'close'] = data.at[ld - 1, 'close']
                df_list[i].loc[l, 'high'] = data.at[ld - 1, 'high']
                df_list[i].loc[l, 'low'] = data.at[ld - 1, 'low']
                df_list[i] = strategy_impl.calculate_heiken_values(df_list[i])
                df_list[i] = strategy_impl.ichimoku_cloud(df_list[i], p, q, r, s, index)
                df_list[i] = strategy_impl.cj_strategy_base_line(df_list[i], len(df_list[i]) - 1, index)
                wb.sheets(names_list[i]).range('A' + str(len(df_list[i]))).options(expand='table', index = False, header = False).value = df_list[i].iloc[[l]]
                l+=1

                
            df_list[i].loc[l, 'timestamp'] = datetime.datetime.timestamp(timestamp_five_mins)
            df_list[i].loc[l, 'date'] = timestamp_five_mins.replace(tzinfo=None) - datetime.timedelta(minutes = 5)

            df_list[i].loc[l, 'open'] = data.at[ld, 'open']
            df_list[i].loc[l, 'close'] = data.at[ld, 'close']
            df_list[i].loc[l, 'high'] = data.at[ld, 'high']
            df_list[i].loc[l, 'low'] = data.at[ld, 'low']
            df_list[i] = strategy_impl.calculate_heiken_values(df_list[i])
            df_list[i] = strategy_impl.ichimoku_cloud(df_list[i], p, q, r, s, index)
            df_list[i] = strategy_impl.cj_strategy_base_line(df_list[i], len(df_list[i]) - 1, index)
            print(df_list[i])
            
            wb.sheets(names_list[i]).range('A' + str(len(df_list[i]))).options(expand='table', index = False, header = False).value = df_list[i].iloc[[l]]

        timestamp_five_mins = timestamp_five_mins + datetime.timedelta(minutes = 5)





#def add_data_to_dataframe(data, i):
    