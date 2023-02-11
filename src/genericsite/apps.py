from django.apps import apps, AppConfig
from django.utils.translation import gettext_lazy as _


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
    base_template = "genericsite/base.html"
    # List of blocks in the base template that include other templates, and can
    # be overridden on a per-view basis or with SiteVars.
    base_blocks = (
        "header_template",
        "precontent_template",
        "content_template",
        "postcontent_template",
        "footer_template",
    )
    bootstrap_container_class = "container"
    paginate_by = 15
    paginate_orphans = 2

    # Default block templates are injected to the template context by our context
    # processor, so they're accessible even to 3rd party views.
    header_template = "genericsite/blocks/header_simple.html"
    footer_template = "genericsite/blocks/footer_simple.html"

    detail_precontent_template = "genericsite/blocks/empty.html"
    detail_content_template = "genericsite/blocks/article_text.html"
    detail_postcontent_template = "genericsite/blocks/empty.html"

    # TODO list_precontent_template should probably be a custom block, not article_text
    list_precontent_template = "genericsite/blocks/article_text.html"
    list_content_template = "genericsite/blocks/article_list_blog.html"
    list_postcontent_template = "genericsite/blocks/empty.html"

    default_icon = "file-text"
    fallback_copyright = _("© Copyright {} {}. All rights reserved.")

    @property
    def pagebreak_separator(self):
        from django.conf import settings

        try:
            return settings.TINYMCE_DEFAULT_CONFIG["pagebreak_separator"]
        except Exception:
            # May not be configured
            return "<!-- MORE -->"

    def ready(self):
        # Add genericsite thumbnail aliases to the easy_thumbnails aliases.
        # This makes them accessible on thumbnail image fields.
        from easy_thumbnails.alias import aliases

        # Landscape aliases, most common in genericsite and many designs
        if not aliases.get("hd1080p"):
            aliases.set("hd1080p", {"size": (1920, 1080), "crop": True})
        if not aliases.get("hd720p"):
            aliases.set("hd720p", {"size": (1280, 720), "crop": True})
        # Ref https://buffer.com/library/ideal-image-sizes-social-media-posts/
        # Recommended size for sharing social images on FB, and close enough for others
        if not aliases.get("opengraph"):
            aliases.set("opengraph", {"size": (1200, 630), "crop": True})
        if not aliases.get("large"):
            aliases.set("large", {"size": (960, 540), "crop": True})
        if not aliases.get("medium"):
            aliases.set("medium", {"size": (400, 225), "crop": True})
        if not aliases.get("small"):
            aliases.set("small", {"size": (160, 90), "crop": True})

        # Portrait orientation aliases
        if not aliases.get("portrait_small"):
            aliases.set("portrait_small", {"size": (90, 160), "crop": True})
        if not aliases.get("portrait_medium"):
            aliases.set("portrait_medium", {"size": (225, 400), "crop": True})
        if not aliases.get("portrait_large"):
            aliases.set("portrait_large", {"size": (540, 960), "crop": True})
        # Buffer post recommends this size for Pinterest
        if not aliases.get("portrait_cover"):
            aliases.set("portrait_cover", {"size": (1000, 1500), "crop": True})
        # Buffer post recommends this size for Insta/FB
        if not aliases.get("portrait_social"):
            aliases.set("portrait_social", {"size": (1080, 1350), "crop": True})
        if not aliases.get("portrait_hd"):
            aliases.set("portrait_hd", {"size": (1080, 1920), "crop": True})


# A context processor to add our vars to template contexts:
def context_defaults(request):
    """Supply default context variables for GenericSite templates"""
    var = request.site.vars
    return {
        "header_template": var.get_value("header_template"),
        "footer_template": var.get_value("footer_template"),
        "precontent_template": var.get_value("detail_precontent_template"),
        "postcontent_template": var.get_value("detail_postcontent_template"),
        "content_template": var.get_value("detail_content_template"),
        "bootstrap_container_class": var.get_value("bootstrap_container_class"),
    }
