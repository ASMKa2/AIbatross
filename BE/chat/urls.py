from django.urls import path, include
from .views import helloAPI, chatAnswer

urlpatterns = [
    path("hello/", helloAPI),
    path("", chatAnswer)
]