from . import views
from django.conf.urls import url
from django.urls import path

urlpatterns = [
    url(r'^$', views.request_testcase),
    url(r'^500$', views.exception_testcase),
    path('api/v1/log', views.logging, name='logging')
]
