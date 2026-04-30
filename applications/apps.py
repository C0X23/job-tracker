from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "applications"
    verbose_name = "Candidatures"

    def ready(self) -> None:
        import applications.signals  # noqa: F401
