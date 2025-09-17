from django.db import models
from django.contrib.auth.models import User
from LMSapp.lms.models import *
from LMSapp.core.models import Event
from django.contrib.auth.models import AbstractUser
from LMSapp.accounts.models import *

# Create your models here.

class ParentDashboard(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="parent_dashboards")
    favorite_events = models.ManyToManyField(Event, blank=True)
    preferred_view = models.CharField(max_length=20, default='default')

    def __str__(self):
        return f"Tableau de bord de {self.parent}"    

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('PRESENT', 'Présent'),
        ('ABSENT', 'Absent'),
        ('LATE', 'En retard'),
    )
    
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True)
    
class ChildDashboard(models.Model):
    child = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="child_dashboards")
    theme = models.CharField(max_length=20, default='default', choices=[
        ('default', 'Thème Par Défaut'),
        ('space', 'Thème Spatial'),
        ('nature', 'Thème Nature'),
        ('animals', 'Thème Animaux')
    ])
    
    def __str__(self):
        return f"Tableau de bord de {self.child.name}"
