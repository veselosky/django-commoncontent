from django.apps import AppConfig


class GenericsiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "genericsite"

    @property
    def pagebreak_separator(self):
        return "<!-- MORE -->"
