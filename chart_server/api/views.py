from django.shortcuts import render
from django.http import HttpResponse
import json
import datetime
import time
import pytz
import pandas as pd
import os
from django.core.files.storage import FileSystemStorage
from .models import Candle

print("HEKK")
marks_visible = True

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
    #response_data["ticker"] = "AAPL"
    response_data["logo_urls"] = ["https://s3-symbol-logo.tradingview.com/apple.svg"]
    
    return HttpResponse(json.dumps(response_data), 'application/json')

def get_time(request):
    presentDate = datetime.datetime.now()
    return HttpResponse(int(time.mktime(presentDate.timetuple())))

def history(request):
    symbol = request.GET.get("symbol")
    fr = request.GET.get("from")
    to = request.GET.get("to")
    resolution = request.GET.get("resolution")
    #number of bars (higher priority than from) starting with to. If countback is set, from should be ignored
    countback = request.GET.get("countback")
    response_data = {}
    
    #if countback:
    #    dates = list(Candle.objects.filter(date__lte=to).order_by('-date').values_list('date', flat=True)[:int(countback)])
    #else:
    dates = list(Candle.objects.filter(date__gte=fr, date__lt=to).values_list('date', flat=True))
        #print("DATES!!!!!!!!!!")
    #print((dates))

    if not dates:
        print("NO DATES")
        response_data['s'] = 'no_data'
        next_time = list(set(Candle.objects.filter(date__lt=to).order_by('-date').values_list('date', flat=True)[:1]))
        if len(next_time) != 0:
            next_time_val = next_time[0]
            response_data['nextTime'] = next_time_val

    else:
        response_data['s'] = 'ok'
        #if countback:
            #obj = Candle.objects.filter(date__lte=to).order_by('-date')[:int(countback)]
        #else:
        obj = Candle.objects.filter(date__gte=fr, date__lt=to)
            
        vals = obj.values()

        vals = sorted(vals, key=lambda d: d['date'])
        
        print("ENDING: "+str(datetime.datetime.fromtimestamp(vals[0]['date']) + datetime.timedelta(hours=5, minutes=30)))
        print("STARTING: "+str(datetime.datetime.fromtimestamp(vals[len(vals) - 1]['date']) + datetime.timedelta(hours=5, minutes=30)))
        print("LENGTH: "+str(len(vals)))

        dats = [d['date'] for d in vals]
        #print(dats)
        response_data['t'] = [int(d['date']) for d in vals]
        response_data['c'] = [d['close'] for d in vals]
        response_data['h'] = [d['high'] for d in vals]
        response_data['l'] = [d['low'] for d in vals]
        response_data['o'] = [d['open'] for d in vals]
        response_data['v'] = [d['volume'] for d in vals]

    return HttpResponse(json.dumps(response_data), 'application/json')
    
def marks(request):
    global marks_visible
    symbol = request.GET.get("symbol")
    fr = int(request.GET.get("from"))
    to = int(request.GET.get("to"))
    resolution = request.GET.get("resolution")
    
    response_data = {}
    response_data['id'] = []
    response_data['time'] = []
    response_data['color'] = []
    response_data['text'] = []
    response_data['label'] = []
    response_data['labelFontColor'] = []
    response_data['minSize'] = []
    
    obj = Candle.objects.filter(date__gte=fr).filter(date__lt=to)
    vals = obj.values()
    vals = sorted(vals, key=lambda d: d['date'], reverse=True)
    jsonDec = json.decoder.JSONDecoder()

    for v in vals:
        marks_list = jsonDec.decode(v['mark_index'])
        
        if v['signal'] != 0:
            if v['signal'] == 1 and marks_visible:
                response_data = add_mark(response_data, marks_list[0], int(v['date']), 'green', 'long signal', 'S', 'black', 25)
                marks_list.pop(0)
            elif v['signal'] == -1 and marks_visible:
                response_data = add_mark(response_data, marks_list[0], int(v['date']), 'red', 'short signal', 'S', 'black', 25)
                marks_list.pop(0)
            elif v['signal'] == 2:
                text = 'trade'
                if v['profit'] != 0:
                    text += ', profit: ' + str(round(v['profit'], 2))
                if v['entry_point'] != 0:
                    text += ', entry point: ' + str(round(v['entry_point'], 2))
                if v['stop_loss'] != 0:
                    text += ', stop loss: ' + str(round(v['stop_loss'], 2))
                response_data = add_mark(response_data, marks_list[0], int(v['date']), 'green', text, 'T', 'black', 25)
                marks_list.pop(0)
            elif v['signal'] == -2:
                text = 'trade'
                if v['profit'] != 0:
                    text += ', profit: ' + str(round(v['profit'], 2))
                if v['entry_point'] != 0:
                    text += ', entry point: ' + str(round(v['entry_point'], 2))
                if v['stop_loss'] != 0:
                    text += ', stop loss: ' + str(round(v['stop_loss'], 2))
                response_data = add_mark(response_data, marks_list[0], int(v['date']), 'red', text, 'T', 'black', 25)
                marks_list.pop(0)
            elif v['signal'] == 3:
                response_data = add_mark(response_data, marks_list[0], int(v['date']), 'yellow', 'exit long trade ' + str(round(v['profit'], 2)), 'E', 'black', 25)
                marks_list.pop(0)
            elif v['signal'] == -3:
                response_data = add_mark(response_data, marks_list[0], int(v['date']), 'yellow', 'exit short trade ' + str(round(v['profit'], 2)), 'E', 'black', 25)
                marks_list.pop(0)
        if (v['signal'] == 1 or v['signal'] == -1) and v['entry_point'] != 0 and marks_visible:
            color = 'green'
            if v['signal'] == -1:
                color = 'red'
            response_data = add_mark(response_data, marks_list[0], int(v['date']), color, 'entry point: ' + str(round(v['entry_point'], 2)), 'E', 'black', 20)
            marks_list.pop(0)
        if v['exit_point'] != 0 and marks_visible:
            response_data = add_mark(response_data, marks_list[0], int(v['date']), 'orange', 'exit point: ' + str(round(v['exit_point'], 2)), 'E', 'yellow', 15)
            marks_list.pop(0)
        if v['entry_position'] != 0 and marks_visible:
            response_data = add_mark(response_data, marks_list[0], int(v['date']), 'red', 'entry position: ' + str(round(v['entry_position'], 2)), 'E', 'black', 20)
            marks_list.pop(0)
        if (v['signal'] == 1 or v['signal'] == -1) and v['stop_loss'] != 0 and marks_visible:
            color = 'green'
            if v['signal'] == -1:
                color = 'red'
            response_data = add_mark(response_data, marks_list[0], int(v['date']), color, 'stop loss: ' + str(round(v['stop_loss'], 2)), 'S', 'white', 20)
            marks_list.pop(0)
        if v['turn_to0'] != 0 and marks_visible:
            response_data = add_mark(response_data, marks_list[0], int(v['date']), 'green', 'signal turns to 0', '0', 'white', 20)
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
    if request.method == 'POST' and request.FILES['myfile']:
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
