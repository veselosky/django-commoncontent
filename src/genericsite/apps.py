from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _

THUMBNAIL_PROCESSORS = (
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "easy_thumbnails.processors.scale_and_crop",
    "easy_thumbnails.processors.filters",
)
THUMBNAIL_WIDGET_OPTIONS = {"size": (160, 90)}

TINYMCE_CONFIG = {
    "height": "320px",
    "width": "960px",
    "menubar": "edit view insert format tools table help",
    "pagebreak_separator": "<!-- pagebreak --><span id=continue-reading></span>",
    "plugins": "advlist autoresize charmap code codesample help hr image imagetools "
    "link lists media pagebreak paste searchreplace table toc visualblocks "
    "visualchars wordcount",
    "toolbar": "undo redo | bold italic strikethrough | styleselect | removeformat | "
    "numlist bullist indent outdent | image pagebreak | code",
    "image_advtab": True,
    "image_caption": True,
    "image_class_list": [
        {"title": "Responsive", "value": "img-fluid"},
        {"title": "Left", "value": "float-left"},
        {"title": "Right", "value": "float-right"},
    ],
    "image_list": "/images/recent.json",
}


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
            aliases.set("medium", {"size": (400, 225), "crop": "smart"})
        if not aliases.get("small"):
            aliases.set("small", {"size": (160, 90), "crop": "smart"})

        # Portrait orientation aliases
        if not aliases.get("portrait_small"):
            aliases.set("portrait_small", {"size": (90, 160), "crop": "smart"})
        if not aliases.get("portrait_medium"):
            aliases.set("portrait_medium", {"size": (225, 400), "crop": "smart"})
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

    # Grab all the site vars from the DB and add them to the dictionary, overriding any
    # fallback defaults.
    gvars.update(request.site.vars.all().values_list("name", "value"))

    # Set the content blocks based on whether the current view is a list or detail view
    # (using a simple heuristic to determine listness.)
    view = request.resolver_match.func
    # For function-based views, check the name for obvious prefix/suffix
    name = view.__name__
    is_list = "_list" in name or name.startswith("list_")
    # For class-based views, the func name is "view". Check for inheritence of List features.
    if hasattr(view, "view_class"):
        from django.views.generic.list import MultipleObjectMixin

        is_list = isinstance(view.view_class, MultipleObjectMixin)

    if is_list:
        gvars["content_template"] = gvars["list_content_template"]
        gvars["precontent_template"] = gvars["list_precontent_template"]
        gvars["postcontent_template"] = gvars["list_postcontent_template"]
    else:
        gvars["content_template"] = gvars["detail_content_template"]
        gvars["precontent_template"] = gvars["detail_precontent_template"]
        gvars["postcontent_template"] = gvars["detail_postcontent_template"]

    # And don't forget to return the value!!!
    return gvars


def plus(*args):
    """Returns a list suitable to use as settings.py INSTALLED_APPS."""
    django_apps = [
        # Standard Django stuff we require
        "django.contrib.admin",
        "django.contrib.admindocs",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.messages",
        "django.contrib.redirects",
        "django.contrib.sessions",
        "django.contrib.sites",
        "django.contrib.staticfiles",
    ]
    # If the user passes in any Django apps that we use, remove them from our list so we
    # don't get dupes. This is slightly fragile, as the user MAY have a custom Appconfig
    # for the app and we would not detect that.
    for app in django_apps:
        if app in args:
            django_apps.remove(app)

    return [
        "genericsite",
        # 3rd party apps we require
        "django_bootstrap_icons",
        "easy_thumbnails",
        "taggit",
        "tinymce",
        # Insert the user's stuff here, above Django defaults, in case they
        # want to override default templates.
        *args,
        *django_apps,
        # Below contrib.admin so it can unregister default admins
        "genericsite.adminoverride",
    ]
