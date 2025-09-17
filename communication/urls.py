from django.urls import path
from . import views

urlpatterns = [
    # Example
    path('inbox/', views.inbox, name='inbox'),
]