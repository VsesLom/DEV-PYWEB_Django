from django.shortcuts import render

from datetime import datetime
from django.views import View
from django.http import HttpResponse
from random import random


class CurrentDateView(View):
    def get(self, request):
        html = f'{datetime.now()}'
        return HttpResponse(html)


class RandomNumber(View):
    def get(self, request):
        html = f'{random()}'
        return HttpResponse(html)


class HelloWorld(View):
    def get(self, request):
        html = '<h1>Hello, World!</h1>'
        return HttpResponse(html)


class IndexView(View):
    def get(self, request):
        return render(request, 'other/index.html')
