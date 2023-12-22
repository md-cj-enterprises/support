from django.shortcuts import render
from django.http import HttpResponse
import json
import datetime
import time
import pytz
import pandas as pd
from django.core.files.storage import FileSystemStorage
import copy
import xlwings as xw
import os.path
import openpyxl

from .historical_nifty_data import HistoricalNiftyData
from .models import Candle
from .live_nifty_data import LiveNiftyData


marks_visible = True
#token_list = ["63488", "63803", "63345"]
token_list = [  "63197",
                "61627",
                "63803",
                "63345",
                "63426",
                "63807",
                "63758",
                "63489",
                "63774",
                "63380",
                "63361",
                "63339",
                "63368",
                "63754",
                "63208",
                "63437",
                "63425",
                "63541",
                "63749",
                "63726",
                "63721",
                "63508",
                "63485",
                "63509",
                "63399",
                "63483",
                "63417",
                "63344",
                "63367",
                "63506",
                "63411",
                "63451",
                "63768"]

names_list = [  "Nifty",
                "BankNifty",
                "ULTRACEMCO28DEC23FUT",
                "BAJAJ-AUTO28DEC23FUT",
                "HINDALCO28DEC23FUT",
                "WIPRO28DEC23FUT",
                "SBIN28DEC23FUT",
                "ITC28DEC23FUT",
                "TCS28DEC23FUT",
                "DIVISLAB28DEC23FUT",
                "BRITANNIA28DEC23FUT",
                "ASIANPAINT28DEC23FUT",
                "COALINDIA28DEC23FUT",
                "RELIANCE28DEC23FUT",
                "ADANIENT28DEC23FUT",
                "HINDUNILVR28DEC23FUT",
                "HEROMOTOCO28DEC23FUT",
                "M&M28DEC23FUT",
                "POWERGRID28DEC23FUT",
                "ONGC28DEC23FUT",
                "NESTLEIND28DEC23FUT",
                "KOTAKBANK28DEC23FUT",
                "INFY28DEC23FUT",
                "L&TFH28DEC23FUT",
                "GRASIM28DEC23FUT",
                "INDUSINDBK28DEC23FUT",
                "HDFCBANK28DEC23FUT",
                "AXISBANK28DEC23FUT",
                "CIPLA28DEC23FUT",
                "JSWSTEEL28DEC23FUT",
                "HCLTECH28DEC23FUT",
                "ICICIBANK28DEC23FUT",
                "TATACONSUM28DEC23FUT"]

if not os.path.isfile("./historical_nifty_data_live_update.xlsx"):
    print("creating file")
    wb = openpyxl.Workbook()

    wb.save("./historical_nifty_data_live_update.xlsx")
    wb.close()


wb = xw.Book('historical_nifty_data_live_update.xlsx')

historical_nifty_data = HistoricalNiftyData()
sheets = [s.name for s in wb.sheets]

for i in range(len(names_list)):
    if not names_list[i] in sheets:
        wb.sheets.add(names_list[i])

    historical_nifty_data.get_historical_data_to_excel(token_list[i], wb.sheets(names_list[i]))
        
live_data_thread = LiveNiftyData(1, "Live thread", token_list, names_list, historical_nifty_data)
live_data_thread.start()

#wb.save()
#wb.close()
print("START")

def change_marks_visibility(request, template_name="templates/change_marks_visibility.html"):
    global marks_visible
    args = {}

    if request.method == 'POST':
        print(request.POST.get('marks_checkbox', True) )
        if request.POST.get('marks_checkbox', True) == True:
            marks_visible = False
        else:
            marks_visible = True
    args['marks_visible'] = marks_visible

    return render(request, 'change_marks_visibility.html', args)

def home(request):
    return render(request, 'home.html', {})

def config(request):
    response_data = {}
    response_data['supports_search'] = True
    response_data['supports_group_request'] = False
    response_data['supports_marks'] = True
    response_data['supports_timescale_marks'] = False
    response_data['supports_time'] = False
    response_data['has_ticks'] = False
    response_data['has_daily'] = False

    exchange1 = {}
    exchange1['value'] = ''
    exchange1['name'] = 'All Exchanges'
    exchange1['desc'] = ''
    
    
    exchange2 = {}
    exchange2['value'] = 'FIFTY'
    exchange2['name'] = 'FIFTY'
    exchange2['desc'] = 'FIFTY'
    


    response_data['exchanges'] = [exchange1, exchange2]
    
    type1 = {}
    type1['name'] = 'All types'
    type1['value'] = ''

    
    type3 = {}
    type3['name'] = 'Future'
    type3['value'] = 'future'
    
    response_data['symbols_types'] = [type1, type3]


    response_data['supported_resolutions'] = supported_resolutions = ["5"]


    return HttpResponse(json.dumps(response_data, separators=(',', ':')), 'application/json')

def symbols(request):
    response_data = {}
    response_data["name"] = "NIFTY50"
    response_data["exchange-traded"] = "NSE"
    response_data["exchange-listed"] =  "NSE"
    response_data["timezone"] = "Asia/Kolkata"
    response_data["minmov"] = 1
    response_data["minmov2"] = 0
    response_data["pointvalue"] = 1
    response_data["session"] = "0915-1530"
    response_data["has_intraday"] = True
    response_data["visible_plots_set"] = "ohlcv"
    response_data["description"] = "NIFTY Futures"
    response_data["type"] = "future"
    response_data["supported_resolutions"] = ["5"]
    response_data["pricescale"] = 100
    response_data["logo_urls"] = ["https://s3-symbol-logo.tradingview.com/apple.svg"]
    
    return HttpResponse(json.dumps(response_data), 'application/json')

def get_time(request):
    presentDate = datetime.datetime.now()
    return HttpResponse(int(time.mktime(presentDate.timetuple())))

def history(request):
    global live_data_thread

    fr = int(request.GET.get("from"))
    to = int(request.GET.get("to"))

    #number of bars (higher priority than from) starting with to. If countback is set, from should be ignored
    countback = request.GET.get("countback")
    response_data = {}
    
    values = live_data_thread.get_data()

    dates = values[(values['timestamp'] >= fr) & (values['timestamp'] < to)]

    if len(dates) == 0:
        #print("NO DATES")
        response_data['s'] = 'no_data'
        #next_time = list(set(Candle.objects.filter(date__lt=to).order_by('-date').values_list('date', flat=True)[:1]))
        next_time = values[values['timestamp'] < to]
        if len(next_time) != 0:
            next_time_val = next_time.at[len(next_time) - 1, 'timestamp']
            response_data['nextTime'] = int(next_time_val)

    else:
        response_data['s'] = 'ok'
        response_data['t'] = dates['timestamp'].tolist()
        response_data['c'] = dates['close'].tolist()
        response_data['h'] = dates['high'].tolist()
        response_data['l'] = dates['low'].tolist()
        response_data['o'] = dates['open'].tolist()

        #response_data['v'] = (dates['low']*0.01).tolist()
    #print(response_data)
    return HttpResponse(json.dumps(response_data), 'application/json')
    
def marks(request):
    global marks_visible
    symbol = request.GET.get("symbol")
    fr = int(request.GET.get("from"))
    to = int(request.GET.get("to"))
    
    response_data = {}
    response_data['id'] = []
    response_data['time'] = []
    response_data['color'] = []
    response_data['text'] = []
    response_data['label'] = []
    response_data['labelFontColor'] = []
    response_data['minSize'] = []
    

    values = live_data_thread.get_data()
    vals = values[(values['timestamp'] >= fr) & (values['timestamp'] <= to)]

    for v in vals.itertuples():
        if v.marks_ids == -1 and not pd.isnull(v.marks_ids):
            continue
        marks_list = copy.copy(v.marks_ids)

        if v.final_signal != 0:
            if v.final_signal == 1 and marks_visible:
                response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'green', 'long signal', 'S', 'black', 25)
                marks_list.pop(0)
            elif v.final_signal == -1 and marks_visible:
                print(v)
                response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'red', 'short signal', 'S', 'black', 25)
                marks_list.pop(0)
            elif v.final_signal == 2:
                text = 'trade'
                if v.profit != 0:
                    text += ', profit: ' + str(round(v.profit, 2))
                if v.entry_point != 0:
                    text += ', entry point: ' + str(round(v.entry_point, 2))
                if v.stop_loss != 0:
                    text += ', stop loss: ' + str(round(v.stop_loss, 2))
                response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'green', text, 'T', 'black', 25)
                marks_list.pop(0)
            elif v.final_signal == -2:
                text = 'trade'
                if v.profit != 0:
                    text += ', profit: ' + str(round(v.profit, 2))
                if v.entry_point != 0:
                    text += ', entry point: ' + str(round(v.entry_point, 2))
                if v.stop_loss != 0:
                    text += ', stop loss: ' + str(round(v.stop_loss, 2))
                response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'red', text, 'T', 'black', 25)
                marks_list.pop(0)
            elif v.final_signal == 3:
                response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'yellow', 'exit long trade ' + str(round(v.profit, 2)), 'E', 'black', 25)
                marks_list.pop(0)
            elif v.final_signal == -3:
                response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'yellow', 'exit short trade ' + str(round(v.profit, 2)), 'E', 'black', 25)
                marks_list.pop(0)
        if (v.final_signal == 1 or v.final_signal == -1) and v.entry_point != 0 and not pd.isnull(v.entry_point) and marks_visible:
            color = 'green'
            if v.final_signal == -1:
                color = 'red'
            response_data = add_mark(response_data, marks_list[0], int(v.timestamp), color, 'entry point: ' + str(round(v.entry_point, 2)), 'E', 'black', 20)
            marks_list.pop(0)
        if v.exit_point != 0 and not pd.isnull(v.exit_point) and marks_visible:
            response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'orange', 'exit point: ' + str(round(v.exit_point, 2)), 'E', 'yellow', 15)
            marks_list.pop(0)
        if v.entry_position != 0 and not pd.isnull(v.entry_position) and marks_visible:
            response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'red', 'entry position: ' + str(round(v.entry_position, 2)), 'E', 'black', 20)
            marks_list.pop(0)
        if (v.final_signal == 1 or v.final_signal == -1) and v.stop_loss != 0 and not pd.isnull(v.stop_loss) and marks_visible:
            color = 'green'
            if v.final_signal == -1:
                color = 'red'
            response_data = add_mark(response_data, marks_list[0], int(v.timestamp), color, 'stop loss: ' + str(round(v.stop_loss, 2)), 'S', 'white', 20)
            marks_list.pop(0)
        if v.turn_to0 != 0 and not pd.isnull(v.turn_to0)  and marks_visible:
            response_data = add_mark(response_data, marks_list[0], int(v.timestamp), 'green', 'signal turns to 0', '0', 'white', 20)
            marks_list.pop(0)
        
    return HttpResponse(json.dumps(response_data), 'application/json')

def add_mark(response, id, time, color, text, label, labelFontColor, minSize):
    response['id'].append(id)
    response['time'].append(time)
    response['color'].append(color)
    response['text'].append(text)
    response['label'].append(label)
    response['labelFontColor'].append(labelFontColor)
    response['minSize'].append(minSize),

    return response
    

def import_excel_pandas(request):
    if request.method == 'POST'  and request.FILES['myfile']:
        Candle.objects.all().delete()

        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        empexceldata = pd.read_excel(filename)
        dbframe = empexceldata
        dbframe.date = dbframe.date.apply(lambda x: x.replace('T', ' '))
        dbframe.date = dbframe.date.apply(lambda x: x.replace('+05:30', ''))
        dbframe.date = dbframe.date.apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
        local = pytz.timezone("Asia/Kolkata")
        dbframe.date = dbframe.date.apply(lambda x: local.localize(x, is_dst=None))
        dbframe.date = dbframe.date.apply(lambda x: x.astimezone(pytz.utc))
        dbframe.date = dbframe.date.apply(lambda x:  int(round(x.timestamp())))

        
        id = 0
        for dbframe in dbframe.itertuples():
            marks_list = []
            if dbframe.final_signal != 0:
                marks_list.append(id)
                id+=1
                if dbframe.final_signal == 3 or dbframe.final_signal == -3:
                    marks_list.append(id)
                    id+=1
            if dbframe.exit_point != 0:
                marks_list.append(id)
                id+=1
            if dbframe.entry_position != 0:
                marks_list.append(id)
                id+=1
            if dbframe.stop_loss != 0:
                marks_list.append(id)
                id+=1
            if dbframe.entry_point != 0:
                marks_list.append(id)
                id+=1
            if dbframe.turn_to0 != 0:
                marks_list.append(id)
                id+=1

            obj = Candle.objects.create(date=dbframe.date, open=dbframe.open,
                                            high=dbframe.high, close=dbframe.close, low=dbframe.low, volume=dbframe.volume,
                                            signal=dbframe.final_signal, mark_index=json.dumps(marks_list),
                                            entry_point=dbframe.entry_point, exit_point=dbframe.exit_point,
                                            entry_position=dbframe.entry_position, stop_loss=dbframe.stop_loss,
                                            profit=dbframe.profit, turn_to0=dbframe.turn_to0)
            obj.save()
        
        print(Candle.objects.all().count())
        return render(request, 'import_excel_db.html', {
            'uploaded_file_url': uploaded_file_url
        })
    return render(request, 'import_excel_db.html',{})
