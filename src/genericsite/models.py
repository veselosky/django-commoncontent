import mimetypes
import typing as T

from django.apps import apps
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils.html import format_html
from django.utils.timezone import get_current_timezone, make_aware, now
from django.utils.translation import gettext_lazy as _, to_locale
from django.utils import timezone
from django.urls import reverse
from easy_thumbnails.fields import ThumbnailerImageField
from easy_thumbnails.files import get_thumbnailer
from taggit.managers import TaggableManager
from tinymce.models import HTMLField

from genericsite.schemas import OpenGraph, OGArticle, ImageProp

# Transform "en-us" to "en_US"
DEFAULT_LOCALE = to_locale(settings.LANGUAGE_CODE)


######################################################################################
# Site Vars
######################################################################################
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


######################################################################################
# Media Objects
######################################################################################
class MediaObject(models.Model):
    """Abstract base class for stored media files (image, audio, video, attachment).

    Every media object has an `image_file` attribute so it can have a thumbnail of some
    kind to display in visual contexts. Thumbnails of standard sizes can be accessed
    via this field. We assume images will use this field as the main `content_field`.
    Other subclasses should use this to store a thumbnail or cover art, and add a new
    field to store their content file, and set the `content_field` attribute to the
    name of the new field where their audio/video/attachment is stored.

    If `mime_type` is not populated, it will be guessed when the instance is saved,
    based on the file name stored in the `content_field` (using `mimetypes.guess_type`).
    """

    class Meta:
        abstract = True
        unique_together = ("site", "title")

    content_field = "image_file"

    title = models.CharField(_("title"), max_length=255)
    description = models.CharField(
        verbose_name=_("description"), max_length=255, blank=True
    )
    image_file = ThumbnailerImageField(
        _("image file"),
        width_field="image_width",
        height_field="image_height",
        max_length=255,
    )
    image_width = models.IntegerField(_("image_width"), blank=True)
    image_height = models.IntegerField(_("image_height"), blank=True)
    alt_text = models.CharField(verbose_name=_("alt text"), max_length=255, blank=True)

    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=1)

    tags = TaggableManager(blank=True)

    # Open Graph has `type`, Schema.org calls it `encodingFormat`, both recommend MIME
    # type as the value
    mime_type = models.CharField(
        _("MIME type"), max_length=255, db_index=True, blank=True
    )
    copyright_holder = models.CharField(
        _("copyright holder"), max_length=255, blank=True
    )
    custom_copyright_notice = HTMLField(
        _("custom copyright notice"),
        blank=True,
        help_text=_(
            r"include a pair of curly braces {} where you want the year inserted"
        ),
    )
    uploaded_dt = models.DateTimeField(_("when uploaded"), auto_now_add=True)
    created_dt = models.DateTimeField(_("when taken"), blank=True, null=True)

    @property
    def copyright_year(self):
        if self.created_dt:
            return self.created_dt.year
        else:
            return self.uploaded_dt.year

    @property
    def copyright_notice(self):
        conf = apps.get_app_config("genericsite")
        var = self.site.vars
        if self.custom_copyright_notice:
            return format_html(self.custom_copyright_notice, self.copyright_year)
        elif notice := var.get_value("copyright_notice"):
            return format_html(notice, self.copyright_year)
        else:
            holder = var.get_value("copyright_holder", self.site.name)
            return format_html(conf.fallback_copyright, self.copyright_year, holder)

    def __str__(self):
        return self.title

    @property
    def _base_url(self):
        protocol = "http" if settings.DEBUG else "https"
        return f"{protocol}://{self.site.domain}"

    @property
    def url(self):
        path = getattr(self, self.content_field).url
        protocol = "http" if settings.DEBUG else "https"
        return f"{self._base_url}{path}"

    def save(self, *args, **kwargs):
        if not self.mime_type:
            self.mime_type, _ = mimetypes.guess_type(
                getattr(self, self.content_field).name, strict=False
            )
        return super().save(*args, **kwargs)


class Image(MediaObject):
    class Meta(MediaObject.Meta):
        verbose_name = _("image")
        verbose_name_plural = _("images")

    @property
    def opengraph(self):
        thumb = get_thumbnailer(self.image_file)["opengraph"]
        return ImageProp(
            url=f"{self._base_url}{thumb.url}",
            type=self.mime_type,
            width=thumb.width,
            height=thumb.height,
            alt=self.alt_text,
        )

    @property
    def icon_name(self):
        return "image"


class Attachment(MediaObject):
    class Meta(MediaObject.Meta):
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    content_field = "file"

    file = models.FileField(_("file"), max_length=255)


######################################################################################
# Content Models
######################################################################################

# This vocabulary taken from IPTC standards, upon which https://schema.org/creativeWork
# is based.
class Status(models.TextChoices):
    WITHHELD = "withheld", _("Draft (withheld)")
    USABLE = "usable", _("Publish (usable)")
    CANCELLED = "cancelled", _("Unpublish (cancelled)")


class AbstractOpenGraph(models.Model):
    """Abstract base model for all models that will represent content pages"""

    class Meta:
        abstract = True
        get_latest_by = "published_time"
        ordering = ["-published_time"]

    title = models.CharField(_("title"), max_length=255)
    slug = models.SlugField(_("slug"))
    # From https://schema.org/creativeWorkStatus
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
    # In a list context, OG objects are frequently represented using their image, or
    # rather the first image in their image set. To prevent having to perform complex
    # queries to get images for all listed objects, we "cache" the first image in the
    # og_image field. This allows a simple `select_related` to retrieve the objects and
    # their images in one query.
    og_image = models.ForeignKey(
        "Image",
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
    # From https://schema.org/articleBody or https://schema.org/text
    body = HTMLField(_("body content"), blank=True)

    # The time, author, and tag fields properly belong to the Article subclass in Open
    # Graph, but they are useful on any model.

    # Equivalent to https://schema.org/datePublished
    published_time = models.DateTimeField(
        _("published time"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Must be non-blank and in the past for page to be 'live'"),
    )
    # Equivalent to https://schema.org/dateModified
    modified_time = models.DateTimeField(
        _("modified time"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Time of last significant editorial update"),
    )
    # Equivalent to https://schema.org/expires
    expiration_time = models.DateTimeField(
        _("expiration time"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Must be blank or in the future for page to be 'live'"),
    )
    author_display_name = models.CharField(
        _("author name, as displayed"),
        max_length=255,
        blank=True,
        help_text=_("e.g. 'Dr. Samuel Clemens, Phd.'"),
    )
    author_profile_url = models.URLField(_("author URL"), max_length=255, blank=True)
    tags = TaggableManager(blank=True)

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
        conf = apps.get_app_config("genericsite")
        var = self.site.vars
        if self.custom_copyright_notice:
            return format_html(self.custom_copyright_notice, self.copyright_year)
        elif notice := var.get_value("copyright_notice"):
            return format_html(notice, self.copyright_year)
        else:
            holder = var.get_value("copyright_holder", self.site.name)
            return format_html(conf.fallback_copyright, self.copyright_year, holder)

    @property
    def excerpt(self):
        """Rich text excerpt for use in teases and feed content. If no excerpt has
        been specified, returns the full body text."""
        config = apps.get_app_config("genericsite")
        if not self.body:
            return ""
        excerpt = self.body.split(config.pagebreak_separator, maxsplit=1)[0]
        return excerpt

    @property
    def icon_name(self):
        "name of an icon to represent this object"
        return self.custom_icon or self.site.vars.get_value("default_icon", "file-text")

    @property
    def url(self):
        return f"https://{self.site.domain}{self.get_absolute_url()}"

    @property
    def opengraph(self):
        """Serialize data to Open Graph metatags.

        Note: although many additional properties are declared on the base class for
        use by GenericSite, the ones serialized here are only the ones declared in
        the base of the Open Graph protocol. The author and tags fields properly
        belong only to subclasses and are explicitly excluded here to ensure tags are
        serialized correctly. We declare this in the superclass so that plain pages,
        section pages, etc. do not need to redeclare it. Subclasses that are proper
        Open Graph subtypes (Article, Video) will need to redeclare this property to
        add their unique OG metadata (by instantiating the correct schema).

        """
        og = OpenGraph.from_orm(self)
        og.site_name = self.site.name
        if self.og_image:
            og.image = [self.og_image.opengraph]
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


#######################################################################
class Section(AbstractOpenGraph):
    "A model to represent major site categories."

    class Meta(AbstractOpenGraph.Meta):
        unique_together = ("site", "slug")
        verbose_name = _("section")
        verbose_name_plural = _("sections")

    objects = GenericPageManager.from_queryset(OpenGraphQuerySet)()

    def get_absolute_url(self):
        return reverse("section_page", kwargs={"section_slug": self.slug})


#######################################################################
class Page(AbstractOpenGraph):
    "A model to represent a generic evergreen page or 'landing page'."

    class Meta(AbstractOpenGraph.Meta):
        unique_together = ("site", "slug")
        verbose_name = _("page")
        verbose_name_plural = _("pages")

    objects = GenericPageManager.from_queryset(OpenGraphQuerySet)()

    def get_absolute_url(self):
        return reverse("landing_page", kwargs={"page_slug": self.slug})


#######################################################################
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


#######################################################################
class ArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("site", "section", "og_image")


class Article(AbstractOpenGraph):
    "Articles are the bread and butter of a site. They will appear in feeds."

    class Meta:
        get_latest_by = "published_time"
        ordering = ["-published_time"]
        unique_together = ("site", "section", "slug")
        verbose_name = _("article")
        verbose_name_plural = _("articles")

    type = models.CharField(
        _("type"),
        max_length=50,
        default="article",
        help_text=_("Open Graph type, see https://ogp.me"),
    )
    section = models.ForeignKey(
        Section, verbose_name=_("section"), on_delete=models.PROTECT
    )
    image_set = models.ManyToManyField(Image, verbose_name=_("related images"))
    attachment_set = models.ManyToManyField(Attachment, verbose_name=_("attachments"))

    objects = ArticleManager.from_queryset(OpenGraphQuerySet)()

    def get_absolute_url(self):
        return reverse(
            "article_page",
            kwargs={"article_slug": self.slug, "section_slug": self.section.slug},
        )

    @property
    def opengraph(self):
        "Serialize data to Open Graph metatags"
        og = OGArticle.from_orm(self)
        og.site_name = self.site.name
        if self.og_image:
            og.image = [self.og_image.opengraph]
        if self.author_profile_url:
            og.author = [self.author_profile_url]
        tags = list(self.tags.names())
        if tags:
            og.tag = tags
        return og


#######################################################################
# Site Menus
#######################################################################
class Menu(models.Model):
    class Meta:
        unique_together = ("site", "slug")

    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name=_("site"))
    admin_name = models.CharField(_("admin name"), max_length=255)
    slug = models.SlugField(_("slug"))
    title = models.CharField(_("title"), max_length=255, blank=True)

    def __str__(self):
        return self.admin_name

    @property
    def links(self):
        return self.link_set.all()


class Link(models.Model):
    """
    A model to store links that can be used in menus. Note, Links are not complete
    open graph objects and intentionally lack many open graph properties. The subset
    of properties required by GenericSite is: url, title and the GenericSite extension
    "icon_name". For completeness, the model also supports storing a description and
    image, though at this writing GenericSite templates do not use these properties.
    """

    class Meta:
        unique_together = (("menu", "url"), ("menu", "title"))

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, verbose_name=_("menu"))
    url = models.CharField(
        _("URL"),
        max_length=255,
        help_text=_(
            "This can be either an absolute path or a full URL "
            "starting with a scheme such as “https://”."
        ),
    )
    title = models.CharField(_("title"), blank=True, max_length=255)
    custom_icon = models.CharField(
        _("custom icon"),
        max_length=50,
        blank=True,
        help_text="<a href=https://icons.getbootstrap.com/#icons target=iconlist>icon list</a>",
    )
    description = models.TextField(_("description"), blank=True)
    og_image = models.ForeignKey(
        "Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("Image for social sharing"),
        related_name="+",
    )

    @property
    def icon_name(self):
        "name of an icon to represent this object"
        return self.custom_icon or self.site.vars.get_value(
            "default_icon", "link-45deg"
        )

    @property
    def image(self):
        if self.og_image:
            return [self.og_image]
        return []


class SectionMenu:
    def __init__(self, site: Site, title: str = "", sections=None, pages=None) -> None:
        self.site = site
        self.title = title
        self.sections = sections or Section.objects.live().filter(site=site).order_by(
            "title"
        )
        self.pages = pages

    @property
    def links(self):
        home = HomePage.objects.live().filter(site=self.site).latest()
        menu = [home]
        menu.extend(self.sections)
        if self.pages:
            menu.extend(self.pages)
        return menu
