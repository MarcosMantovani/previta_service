from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.utils.autoreload import autoreload_started
from django.conf import settings

def celery_watchdog(sender, **kwargs):
    sender.watch_dir('/service', '*.py')

class ServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'service'
    verbose_name = _("Service")

    def ready(self):
        from . import consumers
        if settings.DEBUG:
            autoreload_started.connect(celery_watchdog)