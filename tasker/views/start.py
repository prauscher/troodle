from django.http import HttpResponse
from django.shortcuts import render


def start(request):
    return render(request, 'tasker/start.html')


def tmp(request, **kwargs):
    return HttpResponse("hello")
