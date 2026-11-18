from django.apps import AppConfig
import sys

class SolverConfig(AppConfig):
    name = 'solver'
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        if any(cmd in sys.argv for cmd in ("makemigrations", "migrate", "collectstatic")):
            return
        from.dispatcher import start_dispatcher
        start_dispatcher()