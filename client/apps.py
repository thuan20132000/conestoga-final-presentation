from django.apps import AppConfig


class ClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'client'
    verbose_name = 'Client Management'
    
    def ready(self):
        """Import signal handlers when the app is ready"""
        import client.signals