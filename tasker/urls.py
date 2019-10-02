from django.urls import path

from . import views

urlpatterns = [
    path('', views.tmp),
    path('create_board/', views.tmp),
]
