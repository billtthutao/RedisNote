
from django.http import HttpResponse
from django.shortcuts import render
import redis
 
def hello(request):
    context          = {}
    context['hello'] = 'Hello World!'
    return render(request, 'hello.html', context)

def index(request):
    return render(request, 'login.html')

def login(request):
    context          = {}
    context['username'] = request.POST['username']
    return render(request, 'welcome.html',context)
