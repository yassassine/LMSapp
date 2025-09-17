from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

# Create your models here.
# communication/models.py

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='direct_messages', null=True, blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver}: {self.subject}- {self.sender}"


    User = get_user_model()
    ROLE_CHOICES = [
        ('parent', 'Parent'),
        ('teacher', 'Enseignant'),
        ('admin', 'Administrateur'),
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name='group_messages',blank=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    important = models.BooleanField(default=False)
    parent = models.ForeignKey("self",on_delete=models.CASCADE,related_name="replies",null=True, blank=True) 
                                    #,on_delete=models.SET_NULL, 
    sender_role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        default='parent'
    )

    class Meta:
        ordering = ['-sent_at']
        
    def __str__(self):
        return f"{self.subject}- {self.sender}"

class Attachment(models.Model):
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='messages/attachments/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

# communication/models.py
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('SYSTEM', 'Système'),
        ('ACADEMIC', 'Pédagogique'),
        ('EVENT', 'Événement'),
        ('MESSAGE', 'Message')
    )
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='SYSTEM'
    )
    url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user}"

# communication/models.py
class Announcement(models.Model):
    CATEGORY_CHOICES = (
        ('info', 'Informations générales'),
        ('event', 'Événements'),
        ('academic', 'Pédagogie'),
        ('emergency', 'Urgences'),
        ('maintenance', 'Maintenance'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='info')
    is_urgent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
