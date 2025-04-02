from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _

# Apps required for static site generation
CONTENT = [
    "commoncontent",
    # 3rd party apps we require
    "django_bootstrap_icons",
    "imagekit",
    "taggit",
]

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


class CommonContentConfig(AppConfig):
    """CommonContent app config contains fallback configuration values for customizable
    settings. Add the context processor to have this config injected into all templates
    to ensure global parts like headers and footers render correctly.
    """

    # ========================================================================
    # Django properties
    # ========================================================================
    default_auto_field = "django.db.models.BigAutoField"
    name = "commoncontent"

    # ========================================================================
    # Our configs
    # ========================================================================
    base_template = "commoncontent/base.html"
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
    header_template = "commoncontent/blocks/header_simple.html"
    footer_template = "commoncontent/blocks/footer_simple.html"

    detail_precontent_template = "commoncontent/blocks/empty.html"
    detail_content_template = "commoncontent/blocks/article_text.html"
    detail_postcontent_template = "commoncontent/blocks/empty.html"

    # TODO list_precontent_template should probably be a custom block, not article_text
    list_precontent_template = "commoncontent/blocks/article_text.html"
    list_content_template = "commoncontent/blocks/article_list_blog.html"
    list_postcontent_template = "commoncontent/blocks/empty.html"

    default_icon = "file-text"
    fallback_copyright = _("© Copyright {} {}. All rights reserved.")

    @property
    def excerpt_max_words(self):
        from django.conf import settings

        return getattr(settings, "COMMONCONTENT_EXCERPT_MAX_WORDS", 200)

    @property
    def pagebreak_separator(self):
        from django.conf import settings

        try:
            return settings.TINYMCE_DEFAULT_CONFIG["pagebreak_separator"]
        except Exception:
            # May not be configured
            return TINYMCE_CONFIG["pagebreak_separator"]

    @property
    def sitemap_changefreq(self):
        """How often search engines should check for article updates"""
        from django.conf import settings

        try:
            return settings.SITEMAP_CHANGEFREQ
        except Exception:
            return "weekly"

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


# A context processor to add our vars to template contexts:
def context_defaults(request):
    """Supply default context variables for Common Content templates"""
    # User could have installed a custom appconfig rather than using the default one
    # above, so always fetch it from Django.
    conf = apps.get_app_config("commoncontent")
    # Grab all the default configurations as a dictionary.
    gvars = conf.as_dict()

    # Set the content blocks based on whether the current view is a list or detail view
    # (using a simple heuristic to determine listness.)
    view = request.resolver_match.func
    # For function-based views, check the name for obvious prefix/suffix
    name = view.__name__
    is_list = "_list" in name or name.startswith("list_")
    # For class-based views, the func name is "view". Check for inheritence of List features.
    if hasattr(view, "view_class"):
        from django.views.generic.list import MultipleObjectMixin

        is_list = issubclass(view.view_class, MultipleObjectMixin)

    # Edge case: SiteVars override our settings by having inject_sitevars context
    # processor come after this one. But if they override list_*_template, we need to
    # check that here, since we're assigning values they may not have set.
    sitevars = apps.get_app_config("sitevars").get_site_for_request(request).vars
    list_tpls = [
        "list_content_template",
        "list_precontent_template",
        "list_postcontent_template",
    ]
    detail_tpls = [
        "detail_content_template",
        "detail_precontent_template",
        "detail_postcontent_template",
    ]
    # Since we must support py38, we can't use removeprefix, so we slice instead.
    if is_list:
        for tpl in list_tpls:  # prefix == "list_"
            gvars[tpl[5:]] = sitevars.get_value(tpl, gvars[tpl])
    else:
        for tpl in detail_tpls:  # prefix == "detail_"
            gvars[tpl[7:]] = sitevars.get_value(tpl, gvars[tpl])

    # And don't forget to return the value!!!
    return gvars
