from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import TradingScript, DashboardInfo

#delete all scripts when starting the server. maybe this is not required 
TradingScript.objects.all().delete()

dashboard_info = DashboardInfo()

@csrf_exempt
def update_ltp(request):
    response = json.loads(request.body.decode('utf-8'))
    for script in response['scripts']:
        TradingScript.objects.update_or_create(name=script['name'], defaults={'ltp': script['ltp']})
    print(TradingScript.objects.all())
    return HttpResponse("Success")

@csrf_exempt
def update_dashboard_info(request):

    response = json.loads(request.body.decode('utf-8'))
    if 'net_exposure' in response:
        dashboard_info.net_exposure = response['net_exposure']
    if 'm2m' in response:
        dashboard_info.m2m = response['m2m']
    if 'exit_profit' in response:
        dashboard_info.exit_profit = response['exit_profit']
    if 'total_position' in response:
        dashboard_info.total_position = response['total_position']
    if 'volatility_risk' in response:
        dashboard_info.volatility_risk = response['volatility_risk']
    return HttpResponse("Success")


@csrf_exempt
def get_ltp(request, script_id):
    data = {
        'ltp': TradingScript.objects.get(id=script_id).ltp
    }
    return JsonResponse(data)

def get_dashboard_info(request):
    data = {
        'net_exposure': dashboard_info.net_exposure,
        'm2m': dashboard_info.m2m,
        'volatility_risk': dashboard_info.volatility_risk,
        'total_position': dashboard_info.total_position,
        'exit_profit': dashboard_info.exit_profit,


    }
    return JsonResponse(data)


@login_required
def dashboard(request):
    print("DASHBOARD REQUEST!")

    context = {
        'scripts_list': TradingScript.objects.all(),
        'dashboard_info': dashboard_info,
    }


    return render(request, 'api/dashboard.html', context)
    #return HttpResponse("Success1")

