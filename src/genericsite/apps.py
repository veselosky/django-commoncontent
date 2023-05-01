from django.apps import AppConfig, apps
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

    def as_dict(self) -> dict:
        return {
            "base_template": self.base_template,
            "bootstrap_container_class": self.bootstrap_container_class,
            "default_icon": self.default_icon,
            "detail_content_template": self.detail_content_template,
            "detail_precontent_template": self.detail_precontent_template,
            "detail_postcontent_template": self.detail_postcontent_template,
            "footer_template": self.footer_template,
            "header_template": self.header_template,
            "list_content_template": self.list_content_template,
            "list_postcontent_template": self.list_postcontent_template,
            "list_precontent_template": self.list_precontent_template,
            "paginate_by": self.paginate_by,
            "paginate_orphans": self.paginate_orphans,
        }

    def ready(self):
        # Add genericsite thumbnail aliases to the easy_thumbnails aliases.
        # This makes them accessible on thumbnail image fields.
        from easy_thumbnails.alias import aliases
        from easy_thumbnails.signal_handlers import generate_aliases_global
        from easy_thumbnails.signals import saved_file

        # Landscape aliases, most common in genericsite and many designs
        if not aliases.get("hd1080p"):
            aliases.set("hd1080p", {"size": (1920, 1080), "crop": False})
        if not aliases.get("hd720p"):
            aliases.set("hd720p", {"size": (1280, 720), "crop": False})
        # Ref https://buffer.com/library/ideal-image-sizes-social-media-posts/
        # Recommended size for sharing social images on FB, and close enough for others
        if not aliases.get("opengraph"):
            aliases.set("opengraph", {"size": (1200, 630), "crop": "smart"})
        if not aliases.get("large"):
            aliases.set("large", {"size": (960, 540), "crop": False})
        if not aliases.get("medium"):
            aliases.set("medium", {"size": (400, 225), "crop": False})
        if not aliases.get("small"):
            aliases.set("small", {"size": (160, 90), "crop": False})

        # Portrait orientation aliases
        if not aliases.get("portrait_small"):
            aliases.set("portrait_small", {"size": (90, 160), "crop": False})
        if not aliases.get("portrait_medium"):
            aliases.set("portrait_medium", {"size": (225, 400), "crop": False})
        if not aliases.get("portrait_large"):
            aliases.set("portrait_large", {"size": (540, 960), "crop": False})
        # Buffer post recommends this size for Pinterest
        if not aliases.get("portrait_cover"):
            aliases.set("portrait_cover", {"size": (1000, 1500), "crop": False})
        # Buffer post recommends this size for Insta/FB
        if not aliases.get("portrait_social"):
            aliases.set("portrait_social", {"size": (1080, 1350), "crop": "smart"})
        if not aliases.get("portrait_hd"):
            aliases.set("portrait_hd", {"size": (1080, 1920), "crop": False})

        # Auto-generate thumbs on file upload
        saved_file.connect(generate_aliases_global)


# A context processor to add our vars to template contexts:
def context_defaults(request):
    """Supply default context variables for GenericSite templates"""
    # User could have installed a custom appconfig rather than using the default one
    # above, so always fetch it from Django.
    conf = apps.get_app_config("genericsite")
    # Grab all the default configurations as a dictionary.
    gvars = conf.as_dict()
    # Grab all the sitvars from the DB and add them to the dictionary, overriding any
    # fallback defaults.
    gvars.update(request.site.vars.all().values_list("name", "value"))
    # And don't forget to return the value!!!
    return gvars
