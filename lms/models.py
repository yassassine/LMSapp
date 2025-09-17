from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings

# Create your models here.
# lms/models.py

class CourseCategory(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#4361ee')  # Code couleur hex
    icon = models.CharField(max_length=50, default='fas fa-book')
    
    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    #teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses')
    #teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    description = models.TextField()
    LEVEL_CHOICES = [
        ('PT', 'Petits (2-3 ans)'),
        ('MO', 'Moyens (3-4 ans)'),
        ('GR', 'Grands (5-6 ans)'),
    ]
    
    description = models.TextField()
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    duration = models.PositiveIntegerField(help_text="Durée en minutes")
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        default=0.0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.title
    
    def get_rating_stars(self):
        """Retourne les étoiles de notation pour le template"""
        full_stars = int(self.rating)
        half_star = 1 if (self.rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        return {
            'full': range(full_stars),
            'half': range(half_star),
            'empty': range(empty_stars)
        }
    LEVEL_CHOICES = (
        ('PS', 'Petite Section'),
        ('MS', 'Moyenne Section'),
        ('GS', 'Grande Section'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
    short_description = models.TextField(max_length=300)
    long_description = models.TextField()
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    category = models.CharField(max_length=50, default='Arts')
    image = models.ImageField(upload_to='courses/', null=True, blank=True)
    start_date = models.DateField()
    duration_weeks = models.PositiveIntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('lms:course_detail', kwargs={'pk': self.pk, 'slug': self.slug})
    
    @property
    def modules_count(self):
        return self.modules.count()
    
# lms/models.py

User = get_user_model()
    
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()
    description = models.TextField()
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Resource(models.Model):
    RESOURCE_TYPES = (
        ('pdf', 'PDF'),
        ('video', 'Vidéo'),
        ('image', 'Image'),
        ('link', 'Lien'),
        ('zip', 'Archive ZIP'),
    )
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    file = models.FileField(upload_to='resources/', null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

# lms/models.py

User = get_user_model()

class Assignment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'À rendre'),
        ('submitted', 'Soumis'),
        ('late', 'En retard'),
        ('completed', 'Complété'),
    )

    PRIORITY_CHOICES = (
        ('high', 'Haute'),
        ('medium', 'Moyenne'),
        ('low', 'Basse'),
    )

    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField(null=True, blank=True, help_text="Optional detailed content or instructions")

    # Relations
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments_given')
    children = models.ManyToManyField(User, related_name='assignments', blank=True)

    # Tracking & workflow
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # Submissions & grading
    submission = models.FileField(upload_to='assignments/', null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    grade = models.CharField(max_length=10, null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} ({self.course})"

    @property
    def is_late(self):
        return timezone.now() > self.due_date and self.status != 'completed'

    @property
    def days_remaining(self):
        remaining = self.due_date - timezone.now()
        return remaining.days if remaining.days > 0 else 0

class AssignmentSubmission(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('late', 'En retard'),
        ('graded', 'Évalué'),
    )
    
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE)
    child = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions_made')
    comments = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Soumission #{self.id} - {self.assignment.title}"

class SubmittedFile(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='assignments/submissions/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.original_filename


User = get_user_model()

class ActivityCategory(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#4361ee')
    icon = models.CharField(max_length=50, default='fas fa-star')
    
    def __str__(self):
        return self.name

class InteractiveActivity(models.Model):
    ACTIVITY_TYPES = [
        ('quiz', 'Quiz'),
        ('video', 'Video'),
        ('game', 'Game'),
        ('workshop', 'Atelier'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('completed', 'Complété'),
        ('in_progress', 'En cours'),
        ('not_started', 'Non commencé'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Facile'),
        ('medium', 'Moyen'),
        ('hard', 'Difficile'),
    ]

    module = models.ForeignKey("Module", on_delete=models.CASCADE, related_name="activities")
    category = models.ForeignKey("ActivityCategory", on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    description = models.TextField()
    
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="not_started")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="easy")

    order = models.PositiveIntegerField()
    estimated_time = models.PositiveIntegerField(help_text="Temps estimé en minutes")
    icon = models.CharField(max_length=50, default="fas fa-gamepad")
    url = models.URLField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

class ChildActivityProgress(models.Model):
    child = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(InteractiveActivity, on_delete=models.CASCADE)
    stars_earned = models.PositiveIntegerField(default=0)
    completion_rate = models.PositiveIntegerField(default=0)
    last_played = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('child', 'activity')
    
    def __str__(self):
        return f"{self.child} - {self.activity}: {self.completion_rate}%"
    

User = get_user_model()

class ChildProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='child_profile')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    birth_date = models.DateField()
    level = models.CharField(max_length=50)  # Petite Section, Moyenne Section, etc.
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return self.user.get_full_name()

class ProgressCategory(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#4361ee')
    icon = models.CharField(max_length=50, default='fas fa-star')
    
    def __str__(self):
        return self.name

class ActivityRecord(models.Model):
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=200)
    category = models.ForeignKey(ProgressCategory, on_delete=models.CASCADE)
    date = models.DateField()
    duration = models.PositiveIntegerField(help_text="Durée en minutes")
    score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField(default=10)
    
    @property
    def percentage(self):
        return round((self.score / self.max_score) * 100)
    
    def __str__(self):
        return f"{self.child} - {self.title}"

class Milestone(models.Model):
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_value = models.PositiveIntegerField()
    current_value = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def progress(self):
        return round((self.current_value / self.target_value) * 100)
    
    def __str__(self):
        return self.title

class ChildProgress(models.Model):
    SKILL_CATEGORIES = (
        ('social', 'Compétences Sociales'),
        ('cognitive', 'Compétences Cognitives'),
        ('physical', 'Développement Physique'),
        ('emotional', 'Développement Émotionnel'),
    )

    child = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default="not_started")
    updated_at = models.DateTimeField(auto_now=True)
    # For course-level tracking
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name='progress',
        null=True,
        blank=True,
        help_text="Leave empty if this progress is not linked to a course"
    )

    # For skill/category-level tracking
    category = models.CharField(
        max_length=20,
        choices=SKILL_CATEGORIES,
        blank=True,
        null=True,
        help_text="Leave empty if this progress is course-based"
    )
    skill = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Optional skill within the category"
    )

    # Progress metrics
    overall_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # 0.00–100.00%
    score = models.PositiveIntegerField(default=0)  # 0–100%
    activities_completed = models.PositiveIntegerField(default=0)
    resources_viewed = models.PositiveIntegerField(default=0)

    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Progrès des enfants"
        unique_together = ('child', 'course', 'category', 'skill')

    def __str__(self):
        if self.course:
            return f"{self.child} - {self.course}: {self.overall_progress}%"
        skill_part = f" - {self.skill}" if self.skill else ""
        return f"{self.child} - {self.category}{skill_part}: {self.score}%"



class Reward(models.Model):
    REWARD_TYPES = (
        ('star', 'Étoile'),
        ('badge', 'Badge'),
        ('trophy', 'Trophée'),
    )

    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rewards')
    title = models.CharField(max_length=200)  # From first class
    description = models.TextField(blank=True, null=True)  # Optional text
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    
    # From second class
    badge = models.CharField(max_length=2, blank=True, null=True, help_text="Emoji or symbol")
    activity = models.ForeignKey(Assignment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Dates (kept both, but aligned)
    awarded_at = models.DateTimeField(auto_now_add=True)  # Keep datetime
    date_earned = models.DateField(auto_now_add=True)     # Keep date for filtering

    class Meta:
        ordering = ['-date_earned', '-awarded_at']

    def __str__(self):
        return f"{self.badge or ''} {self.title} - {self.child.username}"