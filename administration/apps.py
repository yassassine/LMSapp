from django.apps import AppConfig

class AdministrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'LMSapp.administration'
    
    def ready(self):
        # Importer les signaux
        from LMSapp.administration import signals