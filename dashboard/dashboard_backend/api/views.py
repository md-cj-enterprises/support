from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import TradingScript

@csrf_exempt
def update_ltp(request):
    response = json.loads(request.body.decode('utf-8'))
    print(response)
    print(response["scripts"])

    for script in response['scripts']:
        TradingScript.objects.update_or_create(name=script['name'], defaults={'ltp': script['ltp']})
    print(TradingScript.objects.all())

    return HttpResponse("Success")

@csrf_exempt
def get_ltp(request, script_id):
    data = {
        'ltp': TradingScript.objects.get(id=script_id).ltp
    }
    return JsonResponse(data)


def dashboard(request):
    print("DASHBOARD REQUEST!")
    scripts = TradingScript.objects.all()

    context = {
        'scripts_list': scripts,
    }


    return render(request, 'api/dashboard.html', context)
    #return HttpResponse("Success1")

