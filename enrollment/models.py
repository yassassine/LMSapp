from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class ClassGroup(models.Model):
    name = models.CharField("Nom", max_length=100)
    teacher = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teaching_groups',
        verbose_name="Enseignant"
    )
    age_range = models.CharField("Tranche d'âge", max_length=20, default="3-5 ans")
    description = models.TextField("Description", blank=True, null=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    
    class Meta:
        verbose_name = "Groupe d'enfants"
        verbose_name_plural = "Groupes d'enfants"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def children_count(self):
        return self.children.count()
    
    @property
    def attendance_rate(self):
        # Logique simplifiée - à remplacer par la vraie logique métier
        return min(100, 80 + self.id * 5)
    
    @property
    def last_activity(self):
        # Logique simplifiée - à remplacer par la vraie logique métier
        activities = Activity.objects.filter(group=self).order_by('-date')
        return activities[0].title if activities.exists() else "Aucune activité"


class ChildEnrollment(models.Model):
    SCHEDULE_CHOICES = [
        ('FT', 'Temps plein'),
        ('PT_AM', 'Mi-temps (matin)'),
        ('PT_PM', 'Mi-temps (après-midi)'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]    
    
    # Informations enfant
    child_first_name = models.CharField("Prénom", max_length=100)
    child_last_name = models.CharField("Nom", max_length=100)
    birth_date = models.DateField("Date de naissance")
    gender = models.CharField("Genre", max_length=1, choices=GENDER_CHOICES)
    grade_level = models.CharField("Niveau scolaire", max_length=50)
    
    # Informations médicales
    allergies = models.TextField("Allergies", blank=True, null=True)
    medical_conditions = models.TextField("Conditions médicales", blank=True, null=True)
    medical_certificate = models.FileField(
        "Certificat médical", 
        upload_to='medical_certs/', 
        blank=True, 
        null=True
    )
    
    # Préférences de garde
    schedule_type = models.CharField("Horaire", max_length=10, choices=SCHEDULE_CHOICES)
    start_date = models.DateField("Date de début")
    special_requirements = models.TextField("Besoins spéciaux", blank=True, null=True)
    
    # Contacts d'urgence
    emergency_contact_name = models.CharField("Nom du contact", max_length=100)
    emergency_contact_phone = models.CharField("Téléphone", max_length=20)
    emergency_contact_relation = models.CharField("Relation", max_length=50)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField("Approuvé", default=False)

    def __str__(self):
        return f"{self.child_first_name} {self.child_last_name} - {self.grade_level}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Payé'),
        ('due_soon', 'Dû bientôt'),
        ('overdue', 'En retard'),
    ]
    
    # Relation parent-enfant
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    photo = models.ImageField(upload_to='children_photos/', blank=True, null=True)
    grade_level = models.CharField(max_length=50)
    enrollment_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    group = models.ForeignKey('ClassGroup', on_delete=models.SET_NULL, null=True, blank=True)
    next_payment_due = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='paid')
    
    class Meta:
        verbose_name = "Enfant"
        verbose_name_plural = "Enfants"
        ordering = ['-enrollment_date']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

class Child(models.Model):
    AGE_GROUP_CHOICES = [
        ('toddlers', 'Toddlers'),
        ('preschool', 'Preschool'),
        ('school_age', 'School Age'),
    ]
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES)
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    birth_date = models.DateField("Date de naissance")
    photo = models.ImageField("Photo", upload_to='children_photos/', blank=True, null=True)
    group = models.ForeignKey(
        ClassGroup,
        on_delete=models.SET_NULL,
        related_name='children',
        null=True,
        blank=True,
        verbose_name="Groupe"
    )
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    
    class Meta:
        verbose_name = "Enfant"
        verbose_name_plural = "Enfants"
        ordering = ['first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

class Activity(models.Model):
    TYPE_CHOICES = [
        ('educational', 'Éducative'),
        ('creative', 'Créative'),
        ('physical', 'Physique'),
        ('social', 'Sociale'),
        ('other', 'Autre'),
    ]
    
    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Description")
    activity_type = models.CharField("Type", max_length=20, choices=TYPE_CHOICES, default='educational')
    date = models.DateTimeField("Date et heure")
    group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Groupe"
    )
    is_completed = models.BooleanField("Terminée", default=False)
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    
    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"
        ordering = ['-date']
    
    def __str__(self):
        return self.title
    
    def get_type_class(self):
        classes = {
            'educational': 'primary',
            'creative': 'info',
            'physical': 'success',
            'social': 'warning',
            'other': 'secondary'
        }
        return classes.get(self.activity_type, 'secondary')

class Observation(models.Model):
    CATEGORY_CHOICES = [
        ('behavior', 'Comportement'),
        ('learning', 'Apprentissage'),
        ('social', 'Socialisation'),
        ('progress', 'Progrès'),
        ('health', 'Santé'),
    ]
    
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='observations',
        verbose_name="Enfant"
    )
    group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name='observations',
        verbose_name="Groupe"
    )
    category = models.CharField("Catégorie", max_length=20, choices=CATEGORY_CHOICES, default='behavior')
    note = models.TextField("Observation")
    date = models.DateTimeField("Date", auto_now_add=True)
    photo = models.ImageField("Photo", upload_to='observations/', blank=True, null=True)
    
    class Meta:
        verbose_name = "Observation"
        verbose_name_plural = "Observations"
        ordering = ['-date']
    
    def __str__(self):
        return f"Observation de {self.child} - {self.get_category_display()}"
    
    def get_category_class(self):
        classes = {
            'behavior': 'primary',
            'learning': 'info',
            'social': 'success',
            'progress': 'warning',
            'health': 'danger'
        }
        return classes.get(self.category, 'secondary')