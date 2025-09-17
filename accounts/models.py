from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

# accounts/models.py

class TeachingLevel(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = (
        ('parent', 'Parent'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
        ('child', 'Child'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)

    # Champs spécifiques aux enseignants
    specialization = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    bio = models.TextField(blank=True)
    availability = models.CharField(max_length=200, blank=True)
    taught_levels = models.ManyToManyField(TeachingLevel, blank=True)

    def get_age(self):
        """Calculer l'âge de l'enfant (si birth_date est défini)."""
        if hasattr(self, "birth_date") and self.birth_date:
            today = timezone.now().date()
            return (
                today.year
                - self.birth_date.year
                - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
            )
        return "?"

    # Méthode utilitaire pour les enseignants
    def get_active_courses(self):
        return self.taught_courses.filter(end_date__gte=timezone.now())

    def get_total_students(self):
        return self.taught_courses.aggregate(total=models.Count("students"))["total"]


class Reward(models.Model):
    child = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'child'}
    )
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fa-medal')
    color = models.CharField(
        max_length=20,
        choices=(
            ('yellow', 'Or'),
            ('blue', 'Bleu'),
            ('purple', 'Violet'),
            ('green', 'Vert'),
        ),
        default='yellow'
    )
    date_awarded = models.DateField(auto_now_add=True)


class Course(models.Model):
    # Ajoute tes champs ici (teacher, students, title, etc.)
    title = models.CharField(max_length=100, blank=True)

    def get_schedule(self):
        """Exemple: Lundi et Mercredi à 10h"""
        return "Lundi et Mercredi à 10h"

    def get_next_session(self):
        """Exemple: Dans 2 jours"""
        return "Dans 2 jours"

'''class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles"
    )'''