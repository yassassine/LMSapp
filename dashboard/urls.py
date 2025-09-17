from django.urls import path
from . import views

urlpatterns = [
    # Example route
    path('', views.dashboard_home, name='dashboard_home'),
]