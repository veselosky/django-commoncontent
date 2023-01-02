from django.apps import apps, AppConfig


class GenericsiteConfig(AppConfig):
    """Genericsite app config contains fallback configuration values for customizable
    settings. Add the context processor to have this config injected into all templates
    to ensure global parts like headers and footers render correctly.
    """

    # ========================================================================
    # Django properties
    # ========================================================================
    default_auto_field = "django.db.models.BigAutoField"
    name = "genericsite"

    # ========================================================================
    # Our configs
    # ========================================================================

    # Default block templates are injected to the template context by our context
    # processor, so they're accessible even to 3rd party views.
    default_header_template = "genericsite/blocks/header_simple.html"
    default_footer_template = "genericsite/blocks/footer_simple.html"
    default_precontent_template = "genericsite/blocks/empty.html"
    default_postcontent_template = "genericsite/blocks/empty.html"
    default_content_template = "genericsite/blocks/article_text.html"
    default_list_content_template = "genericsite/blocks/article_list_blog.html"
    # TODO list_precontent_template should probably be a custom block, not article_text
    default_list_precontent_template = "genericsite/blocks/article_text.html"
    default_list_postcontent_template = "genericsite/blocks/empty.html"
    bootstrap_container_class = "container"

    default_icon = "file-text"

    @property
    def pagebreak_separator(self):
        from django.conf import settings

        try:
            return settings.TINYMCE_DEFAULT_CONFIG["pagebreak_separator"]
        except Exception:
            # May not be configured
            return "<!-- MORE -->"


def context_defaults(request):
    """Supply default context variables for GenericSite templates"""
    # We don't access the class above directly, because the end user can make thier own
    # subclass to customize the defaults. Use the configured class according to Django.
    conf = apps.get_app_config("genericsite")
    var = request.site.vars
    return {
        "header_template": var.get_value(
            "default_header_template", conf.default_header_template
        ),
        "footer_template": var.get_value(
            "default_footer_template", conf.default_footer_template
        ),
        "precontent_template": var.get_value(
            "default_precontent_template", conf.default_precontent_template
        ),
        "postcontent_template": var.get_value(
            "default_postcontent_template", conf.default_postcontent_template
        ),
        "content_template": var.get_value(
            "default_content_template", conf.default_content_template
        ),
        "bootstrap_container_class": var.get_value(
            "bootstrap_container_class", conf.bootstrap_container_class
        ),
    }
