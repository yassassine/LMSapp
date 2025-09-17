from django.urls import path
from . import views

urlpatterns = [
    # Homepage of the core app
    path('', views.index, name='core-home'),
]
