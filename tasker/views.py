from django.shortcuts import render
from django.http import HttpResponse

def tmp(request):
    return HttpResponse("hello")
