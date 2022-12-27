from django.apps import AppConfig


class GenericsiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "genericsite"

    @property
    def pagebreak_separator(self):
        from django.conf import settings

        try:
            return settings.TINYMCE_DEFAULT_CONFIG["pagebreak_separator"]
        except Exception:
            # May not be configured
            return "<!-- MORE -->"
