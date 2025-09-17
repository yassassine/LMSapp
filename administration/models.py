from django.db import models
from LMSapp.lms.models import *
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from LMSapp.enrollment.models import *
from LMSapp.accounts.models import *
from django.contrib.auth import get_user_model
from django.utils import timezone
#from django.contrib.auth.models import Activity, ChildProgress

# Create your models here.

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('update', 'Mise à jour'),
        ('delete', 'Suppression'),
        ('activate', 'Activation'),
        ('deactivate', 'Désactivation'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_actions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activités"

    def __str__(self):
        return f"{self.get_action_display()} - {self.user.username} par {self.admin.username}"

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    last_access = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil Admin - {self.user.get_full_name()}"

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('teacher', 'Enseignant'),
        ('parent', 'Parent'),
        ('child', 'Enfant'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles")
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rôle Utilisateur"
        verbose_name_plural = "Rôles Utilisateurs"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_type_display()}"

class UserStatus(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('pending', 'En attente'),
        ('suspended', 'Suspendu'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='status')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    status_changed = models.DateTimeField(auto_now=True)
    status_reason = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Statut Utilisateur"
        verbose_name_plural = "Statuts Utilisateurs"

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"

class BulkUserImport(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    import_file = models.FileField(upload_to='user_imports/')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('processing', 'En cours'),
            ('completed', 'Terminé'),
            ('failed', 'Échec'),
        ],
        default='pending'
    )
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    error_log = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Importation d'utilisateurs"
        verbose_name_plural = "Importations d'utilisateurs"

    def __str__(self):
        return f"Import du {self.created_at.strftime('%d/%m/%Y')} par {self.admin.username}"

# Signaux pour automatiser la création des profils associés
@receiver(post_save, sender=User)
def create_user_related_models(sender, instance, created, **kwargs):
    if created:
        # Créer un rôle par défaut (admin si superuser, sinon à définir)
        default_role = 'admin' if instance.is_superuser else 'parent'
        UserRole.objects.create(user=instance, role_type=default_role)
        
        # Créer un statut par défaut
        UserStatus.objects.create(user=instance)
        
        # Créer un profil admin si superuser
        if instance.is_superuser or instance.is_staff:
            AdminProfile.objects.create(user=instance)

class ContentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#4361ee', verbose_name="Couleur")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Catégorie de contenu"
        verbose_name_plural = "Catégories de contenu"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (DRAFT, 'Brouillon'),
        (PUBLISHED, 'Publié'),
        (ARCHIVED, 'Archivé'),
    ]
    
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    LEVEL_CHOICES = [
        (BEGINNER, 'Débutant'),
        (INTERMEDIATE, 'Intermédiaire'),
        (ADVANCED, 'Avancé'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(verbose_name="Description")
    short_description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description courte")
    category = models.ForeignKey(ContentCategory, on_delete=models.SET_NULL, null=True, verbose_name="Catégorie", related_name="courses")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créateur", related_name='created_courses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT, verbose_name="Statut")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=BEGINNER, verbose_name="Niveau")
    duration = models.IntegerField(
        help_text="Durée estimée en heures", 
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Durée"
    )
    featured_image = models.ImageField(upload_to='course_images/', blank=True, null=True, verbose_name="Image mise en avant")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.short_description and self.description:
            self.short_description = self.description[:200] + '...' if len(self.description) > 200 else self.description
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})
    
    @property
    def lessons_count(self):
        return self.lessons.count()

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Cours", related_name='lessons')
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, blank=True)
    content = models.TextField(verbose_name="Contenu")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre")
    video_url = models.URLField(blank=True, null=True, verbose_name="URL vidéo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"
        ordering = ['order']
        unique_together = ['course', 'order']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Resource(models.Model):
    PDF = 'pdf'
    VIDEO = 'video'
    AUDIO = 'audio'
    IMAGE = 'image'
    LINK = 'link'
    RESOURCE_TYPES = [
        (PDF, 'PDF'),
        (VIDEO, 'Vidéo'),
        (AUDIO, 'Audio'),
        (IMAGE, 'Image'),
        (LINK, 'Lien externe'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name="Leçon", related_name='resources')
    title = models.CharField(max_length=200, verbose_name="Titre")
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, verbose_name="Type de ressource")
    file = models.FileField(upload_to='resources/', blank=True, null=True, verbose_name="Fichier")
    external_link = models.URLField(blank=True, null=True, verbose_name="Lien externe")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Ressource"
        verbose_name_plural = "Ressources"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_download_url(self):
        if self.file:
            return self.file.url
        return self.external_link

class Activity(models.Model):
    QUIZ = 'quiz'
    ASSIGNMENT = 'assignment'
    INTERACTIVE = 'interactive'
    DISCUSSION = 'discussion'
    ACTIVITY_TYPES = [
        (QUIZ, 'Quiz'),
        (ASSIGNMENT, 'Devoir'),
        (INTERACTIVE, 'Activité interactive'),
        (DISCUSSION, 'Discussion'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name="Leçon", related_name='activities')
    title = models.CharField(max_length=200, verbose_name="Titre")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name="Type d'activité")
    instructions = models.TextField(verbose_name="Instructions")
    max_score = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Score maximal"
    )
    due_date = models.DateTimeField(blank=True, null=True, verbose_name="Date limite")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class ContentAnalytics(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    completions = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Analyse de contenu"
        verbose_name_plural = "Analyses de contenu"
        unique_together = ['course', 'date']
    
    def __str__(self):
        return f"Analytics for {self.course.title} on {self.date}"

User = get_user_model()

class EnrollmentStatusLog(models.Model):
    enrollment = models.ForeignKey(ChildEnrollment, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.enrollment.child} - {self.old_status}→{self.new_status}"

User = get_user_model()

class FinancialRecord(models.Model):
    RECORD_TYPE = [
        ('income', 'Recette'),
        ('expense', 'Dépense'),
    ]
    
    record_type = models.CharField(max_length=10, choices=RECORD_TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_record_type_display()} - {self.amount}€ - {self.date}"

class ReportConfiguration(models.Model):
    name = models.CharField(max_length=100)
    period = models.CharField(max_length=50)
    age_group = models.CharField(max_length=20, blank=True, null=True)
    class_group = models.CharField(max_length=50, blank=True, null=True)
    report_type = models.CharField(max_length=50)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name