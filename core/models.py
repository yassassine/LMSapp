from django.db import models
from django.utils import timezone
from LMSapp.accounts.models import User
from django.conf import settings
# Create your models here.

class News(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    CATEGORY_CHOICES = (
        ('general', 'Actualités générales'),
        ('pedagogy', 'Pédagogie'),
        ('event', 'Événements'),
        ('activity', 'Activités'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    image = models.ImageField(upload_to='news/')
    published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Event(models.Model):
    TYPE_CHOICES = (
        ('workshop', 'Atelier'),
        ('celebration', 'Célébration'),
        ('meeting', 'Réunion parents'),
        ('trip', 'Sortie'),
        ('show', 'Spectacle'),
        ('holiday', 'Vacances'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    
    def get_type_color(self):
        colors = {
            'workshop': 'info',
            'celebration': 'success',
            'meeting': 'primary',
            'trip': 'warning',
            'show': 'danger',
        }
        return colors.get(self.event_type, 'secondary')
    
    def __str__(self):
        return f"{self.title} - {self.date}"

class Activity(models.Model):
    CATEGORY_CHOICES = (
        ('arts', 'Arts créatifs'),
        ('sports', 'Sports & Motricité'),
        ('science', 'Sciences & Nature'),
        ('music', 'Musique & Danse'),
        ('language', 'Langues & Lecture'),
        ('technology', 'Technologie'),
    )
    
    AGE_GROUP_CHOICES = (
        ('2-3', '2-3 ans'),
        ('4-5', '4-5 ans'),
        ('6-7', '6-7 ans'),
        ('8+', '8 ans et plus'),
    )
    
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=200)
    full_description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES)
    image = models.ImageField(upload_to='activities/')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'teacher'})
    max_participants = models.PositiveIntegerField(default=12)
    duration = models.PositiveIntegerField(help_text="Durée en minutes")
    difficulty = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], default=3)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_free = models.BooleanField(default=True)
    weekly = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    
    # Pour les activités spéciales
    is_special = models.BooleanField(default=False)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    
    def get_badge_color(self):
        colors = {
            'arts': 'info',
            'sports': 'success',
            'science': 'warning',
            'music': 'danger',
            'language': 'primary',
            'technology': 'secondary',
        }
        return colors.get(self.category, 'dark')
    
    def __str__(self):
        return self.title

class Testimonial(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="parent_testimonials",
    limit_choices_to={'role': 'parent'})
    child_name = models.CharField(max_length=100)
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    date = models.DateField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Témoignage de {self.parent} - {self.date}"
    child = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="child_testimonials", 
    limit_choices_to={'role': 'child'})
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    date = models.DateField(default=timezone.now)
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Témoignage de {self.child} sur {self.activity}"
    
class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField()
    photo = models.ImageField(upload_to='team/')
    specialty = models.CharField(max_length=100, blank=True)
    experience = models.PositiveIntegerField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    EVENT_TYPES = (
    ('kids_events', 'party_events'),
    ('clubs_events', 'free_for_all'),)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    
    def __str__(self):
        return self.title

class Closure(models.Model):
    CLOSURE_TYPES = (
        ('holiday', 'Vacances scolaires'),
        ('training', 'Formation du personnel'),
        ('public', 'Jour férié'),
        ('other', 'Autre'),
    )
    
    title = models.CharField(max_length=200)
    closure_type = models.CharField(max_length=20, choices=CLOSURE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True)
    
    def get_badge_color(self):
        colors = {
            'holiday': 'secondary',
            'training': 'info',
            'public': 'primary',
            'other': 'warning',
        }
        return colors.get(self.closure_type, 'dark')
    
    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"
    
