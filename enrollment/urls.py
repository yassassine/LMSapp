from django.urls import path
from . import views

urlpatterns = [
    path('', views.enrollment_view, name='enrollment-home'),

]