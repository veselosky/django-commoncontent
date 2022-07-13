import typing as T

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _, to_locale
from django.utils import timezone
from django.urls import reverse
from filer.fields.image import FilerImageField
from filer.models import Image
from taggit.managers import TaggableManager
from tinymce.models import HTMLField

from genericsite.schemas import OpenGraph, OGArticle

# Transform "en-us" to "en_US"
DEFAULT_LOCALE = to_locale(settings.LANGUAGE_CODE)


class SiteVarQueryset(models.QuerySet):
    def get_value(self, name: str, default: str = "", asa: T.Callable = str):
        """
        Given a queryset pre-filtered by site, returns the value of the SiteVar with
        the given name. If no value is set for that name, returns the passed default
        value, or empty string if no default was passed. To transform the stored string
        to another type, pass a transform function in the asa argument. The default
        value should be passed as a string; it will be passed to the asa function
        for transformation.

        Examples:

        # Returns the string if set, or "" if not set
        x = site.vars.get_value("analytics_id")
        # Returns the string if set, or "Ignore" if not set
        x = site.vars.get_value("abort_retry_ignore", "Ignore")
        # Returns the number of pages as an integer. Note the default should be a str.
        num_items = site.vars.get_value("items_per_page", default="10", asa=int)
        # Parses the value as JSON and returns the result
        data = site.vars.get_value("json_data", "{}", json.loads)
        """
        try:
            return asa(self.get(name=name).value)
        except self.model.DoesNotExist:
            return asa(default)
        # Note explicitly NOT catching MultipleObjectsReturned, that's still an error


class SiteVar(models.Model):
    class Meta:
        base_manager_name = "objects"
        unique_together = ("site", "name")
        verbose_name = _("sitevar")
        verbose_name_plural = _("sitevars")

    site = models.ForeignKey(
        "sites.Site",
        verbose_name=_("site"),
        on_delete=models.CASCADE,
        related_name="vars",
    )
    name = models.CharField(_("name"), max_length=100)
    value = models.TextField(_("value"))

    objects = SiteVarQueryset.as_manager()

    def __str__(self):
        return self.value

    @classmethod
    def For(cls, site: T.Union[Site, int]) -> models.Manager:
        "Convenience class method returns a querset filtered by site"
        site_id = site
        if isinstance(site, Site):
            site_id = site.id
        return cls.objects.filter(site_id=site_id)


class Status(models.TextChoices):
    WITHHELD = "withheld", _("Draft (withheld)")
    USABLE = "usable", _("Publish (usable)")
    CANCELLED = "cancelled", _("Unpublish (cancelled)")


class AbstractOpenGraph(models.Model):
    class Meta:
        abstract = True
        get_latest_by = "published_time"
        ordering = ["-published_time"]

    title = models.CharField(_("title"), max_length=255)
    slug = models.SlugField(_("slug"))
    status = models.CharField(
        _("status"),
        max_length=50,
        choices=Status.choices,
        default=Status.USABLE,
        db_index=True,
    )
    site = models.ForeignKey(
        Site,
        verbose_name=_("site"),
        on_delete=models.CASCADE,
        default=1,
        related_name="+",
    )
    description = models.TextField(_("description"), blank=True)
    og_image = FilerImageField(
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("Image for social sharing"),
        related_name="+",
    )
    base_template = models.CharField(_("base template"), max_length=255, blank=True)
    content_template = models.CharField(
        _("content body template"),
        max_length=255,
        blank=True,
    )
    body = HTMLField(_("body content"), blank=True)
    images = models.ManyToManyField(
        Image, verbose_name=_("images"), related_name="+", blank=True
    )

    # The time fields properly belong to the Article subclass in Open Graph, but
    # they are useful on any model.
    published_time = models.DateTimeField(
        _("published time"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Must be non-blank and in the past for page to be 'live'"),
    )
    modified_time = models.DateTimeField(
        _("modified time"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Time of last significant editorial update"),
    )
    expiration_time = models.DateTimeField(
        _("expiration time"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Must be blank or in the future for page to be 'live'"),
    )

    # These metadata fields are seldom used and have sensible defaults where needed.
    type = models.CharField(
        _("opengraph type"),
        max_length=50,
        default="website",
        help_text=_("Open Graph type, see https://ogp.me"),
    )
    seo_title = models.CharField(_("SEO title override"), max_length=255, blank=True)
    seo_description = models.CharField(
        _("SEO description override"), max_length=255, blank=True
    )
    custom_copyright_notice = HTMLField(
        _("custom copyright notice"),
        blank=True,
        help_text=_(
            r"include a pair of curly braces {} where you want the year inserted"
        ),
    )
    custom_icon = models.CharField(
        _("custom icon"),
        max_length=50,
        blank=True,
        help_text="<a href=https://icons.getbootstrap.com/#icons target=iconlist>icon list</a>",
    )
    locale = models.CharField(_("locale"), max_length=10, default=DEFAULT_LOCALE)

    def __str__(self):
        return self.title

    @property
    def copyright_year(self):
        if self.published_time:
            return self.published_time.year
        else:
            return timezone.now().year

    @property
    def copyright_notice(self):
        var = SiteVar.For(self.site)
        if self.custom_copyright_notice:
            return format_html(self.custom_copyright_notice, self.copyright_year)
        elif notice := var.get_value("copyright_notice"):
            return format_html(notice, self.copyright_year)
        else:
            holder = var.get_value("copyright_holder", self.site.name)
            return format_html(
                "© Copyright {} {}. All rights reserved.", self.copyright_year, holder
            )

    @property
    def icon_name(self):
        "name of an icon to represent this object"
        if self.custom_icon:
            return self.custom_icon
        elif icon := SiteVar.For(self.site).get_value("default_icon"):
            return icon
        else:
            return "file-text"

    @property
    def url(self):
        return f"https://{self.site.domain}{self.get_absolute_url()}"

    @property
    def opengraph(self):
        og = OpenGraph.from_orm(self)
        og.site_name = self.site.name
        if self.og_image:
            og.image = [self.og_image]
        return og


class AbstractArticle(AbstractOpenGraph):
    class Meta:
        abstract = True
        get_latest_by = "published_time"
        ordering = ["-published_time"]
        unique_together = ("site", "section", "slug")
        verbose_name = _("article page")
        verbose_name_plural = _("article pages")

    type = models.CharField(
        _("type"),
        max_length=50,
        default="article",
        help_text=_("Open Graph type, see https://ogp.me"),
    )
    # Exists here to be inherited in custom models for users who do not want to
    # use the stock models below. The section field will be overridden in the
    # stock models, as Section will be an AbstractOpenGraph model.
    section = models.CharField(_("section"), max_length=50, blank=True)
    author_display_name = models.CharField(
        _("author name, as displayed"),
        max_length=255,
        blank=True,
        help_text=_("e.g. 'Dr. Samuel Clemens, Phd.'"),
    )
    author_profile_url = models.URLField(_("author URL"), max_length=255, blank=True)
    tags = TaggableManager(blank=True)

    def opengraph(self):
        og = OGArticle.from_orm(self)
        og.site_name = self.site.name
        if self.og_image:
            og.image = [self.og_image]
        if self.author_profile_url:
            og.author = [self.author_profile_url]
        tags = list(self.tags.names())
        if tags:
            og.tag = tags

        return og


#######################################################################
# Concrete models for the app
#######################################################################


class OpenGraphQuerySet(models.QuerySet):
    def live(self):
        return self.filter(
            models.Q(expiration_time__isnull=True)
            | models.Q(expiration_time__gt=timezone.now()),
            status=Status.USABLE,
            published_time__lte=timezone.now(),
        )


class GenericPageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("site", "og_image")


class Section(AbstractOpenGraph):
    "A model to represent major site categories."

    class Meta(AbstractOpenGraph.Meta):
        unique_together = ("site", "slug")
        verbose_name = _("section")
        verbose_name_plural = _("sections")

    objects = GenericPageManager.from_queryset(OpenGraphQuerySet)()

    def get_absolute_url(self):
        return reverse("section_page", kwargs={"section_slug": self.slug})


class Page(AbstractOpenGraph):
    "A model to represent a generic evergreen page or 'landing page'."

    class Meta(AbstractOpenGraph.Meta):
        unique_together = ("site", "slug")
        verbose_name = _("page")
        verbose_name_plural = _("pages")

    objects = GenericPageManager.from_queryset(OpenGraphQuerySet)()

    def get_absolute_url(self):
        return reverse("landing_page", kwargs={"page_slug": self.slug})


class HomePage(AbstractOpenGraph):
    "A model to represent the site home page."

    class Meta(AbstractOpenGraph.Meta):
        verbose_name = _("home page")
        verbose_name_plural = _("home pages")

    admin_name = models.CharField(
        _("admin name"),
        max_length=255,
        unique=True,
        help_text=_("Name used in the admin to distinguish from other home pages"),
    )
    objects = GenericPageManager.from_queryset(OpenGraphQuerySet)()

    def get_absolute_url(self):
        return reverse("home_page")


class ArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("site", "section", "og_image")


class Article(AbstractArticle):
    "Articles are the bread and butter of a site. They will appear in feeds."
    # We override the section from AbstractArticle to use our model instead.
    section = models.ForeignKey(
        Section, verbose_name=_("section"), on_delete=models.PROTECT
    )

    objects = ArticleManager.from_queryset(OpenGraphQuerySet)()

    def get_absolute_url(self):
        return reverse(
            "article_page",
            kwargs={"article_slug": self.slug, "section_slug": self.section.slug},
        )
