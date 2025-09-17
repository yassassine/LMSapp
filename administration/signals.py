from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Course, ContentAnalytics
from django.utils import timezone

@receiver(post_save, sender=Course)
def create_initial_analytics(sender, instance, created, **kwargs):
    if created:
        # Créer une entrée analytics pour le nouveau cours
        ContentAnalytics.objects.create(course=instance, date=timezone.now().date())

@receiver(post_save, sender=Course)
def update_course_analytics(sender, instance, **kwargs):
    # Mettre à jour les analytics quotidiennes
    today = timezone.now().date()
    analytics, created = ContentAnalytics.objects.get_or_create(
        course=instance, 
        date=today,
        defaults={'views': 0, 'downloads': 0, 'completions': 0}
    )
    if not created:
        analytics.save()