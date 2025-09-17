from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from LMSapp.communication.models import Notification  # adjust if your model is elsewhere

User = get_user_model()

def index(request):
    return render(request,'login.html')

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']  # only actual fields from your User model

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # after register, go to login
    else:
        form = UserCreationForm()

    context = {"form": form}
    return render(request, "accounts/register.html", context)

def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.is_read = True
    notification.save()
    return redirect('notifications_view')  # or wherever you want to redirect

