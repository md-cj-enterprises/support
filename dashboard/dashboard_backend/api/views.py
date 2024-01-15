from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

ltp = 0

@csrf_exempt
def update_ltp(request):
    global ltp
    response = json.loads(request.body.decode('utf-8'))
    print(response['ltp'])
    ltp =  response['ltp'],
    return HttpResponse("Success")

@csrf_exempt
def get_ltp(request):
    data = {
        'price': ltp,
    }
    return JsonResponse(data)


def dashboard(request):
    print("DASHBOARD REQUEST!")
    print(ltp)
    context = {
        'price': ltp,
    }

    return render(request, 'api/dashboard.html', context)
    #return HttpResponse("Success1")

