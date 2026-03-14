from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import nltk
        import os
        from django.conf import settings
        
        # Add local nltk_data to search path
        nltk_path = os.path.join(settings.BASE_DIR, 'nltk_data')
        if os.path.exists(nltk_path) and nltk_path not in nltk.data.path:
            nltk.data.path.append(nltk_path)
