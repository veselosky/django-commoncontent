import mimetypes
import typing as T

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.translation import to_locale
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit
from taggit.managers import TaggableManager

from genericsite.common import Status, upload_to
from genericsite.schemas import ImageProp, OGArticle, OGProfile, OpenGraph, ThingSchema

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
        num_items = site.vars.get_value("paginate_by", default="10", asa=int)
        # Parses the value as JSON and returns the result
        data = site.vars.get_value("json_data", "{}", json.loads)
        """
        try:
            return asa(self.get(name=name).value)
        except self.model.DoesNotExist:
            # Anything that can be a site var can also be configured app-wide.
            conf = apps.get_app_config("genericsite")
            if hasattr(conf, name):
                return asa(getattr(conf, name))
            # This allows None as a default, without crashing on e.g. `int(None)`
            return asa(default) if default is not None else default
        # Note explicitly NOT catching MultipleObjectsReturned, that's still an error


class SiteVar(models.Model):
    """
    Site-specific variables are stored here. All site variable are injected into
    template contexts using the generic site context processor in
    ``genericsite.apps.context_defaults``. You can store any variables for your own
    site. The variables below are used by the included generic templates.

    - ``base_template`` - The base template to use for generic pages. Defaults to
      ``genericsite/base.html``.
    - ``brand`` - Site's brand name. Uses Site.name if not set.
    - ``copyright_holder`` - Custom name for the copyright holder if using the default
      copyright notice. Falls back to ``site.name`` if not provided.
    - ``copyright_notice`` - HTML to include in the copyright notice section of the
      footer (replaces the default copyright notice).
    - ``custom_stylesheet`` - A site-specific CSS file. This is pulled into the
      ``extra_head`` block after bootstrap and genericsite's CSS, so you can use it to
      override default styles and customize the look and feel of each site. It is
      included using ``{% static custom_stylesheet %}`` so the value should be relative
      to the STATIC_ROOT.
    - ``default_icon`` - Name of a Bootstrap icon to use by default if the object
      provides none.
    - ``detail_precontent_template`` - Default template to use for the ``precontent``
      block for detail pages.
    - ``detail_content_template`` - Default template to use for the ``content`` block
      for detail pages.
    - ``detail_postcontent_template`` - Default template to use for the ``postcontent``
      block for detail pages.
    - ``footer_template`` - Default template to use for the ``footer`` block.
    - ``header_template`` - Default template to use for the ``header`` block.
    - ``list_postcontent_template`` - Default template to use for the ``postcontent``
      block for list pages.
    - ``list_precontent_template`` - Default template to use for the ``precontent``
      block for list pages.
    - ``list_content_template`` - Default template to use for the ``content`` block for
      list pages.
    - ``logo`` - The URL to your site's logo image.
    - ``paginate_by`` - Items per page on list pages, same as Django's ListView, see
      `pagination <https://docs.djangoproject.com/en/dev/ref/paginator/>`_ in the
      Django docs.
    - ``paginate_orphans`` - Same as Django's ListView, see
      `pagination <https://docs.djangoproject.com/en/dev/ref/paginator/>`_ in the
      Django docs.

    """

    site = models.ForeignKey(
        "sites.Site",
        verbose_name=_("site"),
        on_delete=models.CASCADE,
        related_name="vars",
    )
    name = models.CharField(_("name"), max_length=100)
    value = models.TextField(_("value"))

    objects = SiteVarQueryset.as_manager()

    class Meta:
        base_manager_name = "objects"
        unique_together = ("site", "name")
        verbose_name = _("site variable")
        verbose_name_plural = _("site variables")

    def __str__(self):
        return f"{self.name}={self.value} ({self.site.domain})"

    @classmethod
    def For(cls, site: T.Union[Site, int]) -> models.Manager:
        "Convenience class method returns a querset filtered by site"
        site_id = site
        if isinstance(site, Site):
            site_id = site.id
        return cls.objects.filter(site_id=site_id)


######################################################################################
class Author(models.Model):
    """
    An Author, in Schema.org, is a Person or Organization to whom credit is attributed.
    Neither Schema.org's Person nor Open Graph's Profile provides much interesting in
    the way of data model. For GenericSite, we use the model to provide basic
    attribution, and to populate a profile page. The Author can also be used to store
    default copyright information.
    """

    site = models.ForeignKey(
        Site,
        verbose_name=_("site"),
        on_delete=models.CASCADE,
        default=1,
    )
    name = models.CharField(
        _("author name, as displayed"),
        max_length=255,
        help_text=_("e.g. 'Dr. Samuel Clemens, Phd.'"),
    )
    slug = models.SlugField(_("slug"), help_text=_("e.g. 'samuel-clemens'"))
    description = models.CharField(
        _("description (text only, no markup)"),
        max_length=255,
        blank=True,
        help_text=_("A brief description of the author, used for SEO description."),
    )
    short_bio = models.TextField(
        _("short biography"),
        blank=True,
        help_text=_(
            "A brief biography of the author, one paragraph. May contain HTML."
        ),
    )
    full_bio = models.TextField(
        _("full biography"),
        blank=True,
        help_text=_(
            "A full biography of the author, main content for the profile page. May "
            "contain HTML."
        ),
    )
    profile_image = models.ForeignKey(
        "Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("Image for social sharing"),
        related_name="+",
    )
    social_links = models.ForeignKey(
        "Menu",
        verbose_name=_("social links"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_(
            "A list of links to the author's websites and/or social media profiles."
        ),
    )
    copyright_holder = models.CharField(
        _("copyright holder"),
        max_length=255,
        blank=True,
        help_text=_("Name of copyright holder for this author."),
    )
    copyright_notice = models.TextField(
        _("custom copyright notice"),
        blank=True,
        help_text=_(
            r"include a pair of curly braces {} where you want the year inserted"
        ),
    )
    date_modified = models.DateTimeField(
        _("date modified"),
        blank=True,
        null=True,
        help_text=_("Time of last significant editorial update"),
    )

    class Meta:
        verbose_name = _("author")
        verbose_name_plural = _("authors")
        constraints = [
            models.UniqueConstraint(
                fields=["site", "name"], name="unique_author_name_per_site"
            )
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("author_page", kwargs={"author_slug": self.slug})

    # Class properties
    icon_name = "person-vcard"

    @property
    def opengraph(self):
        og = OGProfile(title=self.name, type="profile")
        if self.profile_image:
            og.image = [self.profile_image.opengraph]
        return og

    @property
    def schema(self) -> ThingSchema:
        """Return the data as a schema.org object."""
        schema_class = ThingSchema.get_class_for_label("Person")
        schema = schema_class(
            name=self.name,
            description=self.short_bio,
            image=self.profile_image.url if self.profile_image else None,
        )
        return schema

    @property
    def url(self):
        return f"https://{self.site.domain}{self.get_absolute_url()}"


######################################################################################
# Content Models
######################################################################################


class AbstractCreativeWork(models.Model):
    """
    <https://schema.org/CreativeWork>. CreativeWork is the base class for all content.

    CreativeWork houses the common properties of content described by Schema.org, including
    copyright information and publication status, as well as some properties used for
    internal management.

    Every CreativeWork has foreign keys to site (Site) and owner (User). The owner is
    nullable for convenience of programatically created content, but is required for
    content created by users. The site is required for all content, and is used to
    determine the permissions, site-specific settings, and appearance of the content.

    Additionally, every CreativeWork is expected to be able to produce a schema.org
    dictionary for use in JSON-LD serialization, and a list of open graph properties
    and values describing itself. This is done by overriding the `schema_dict` and
    `opengraph` properties in subclasses. Opengraph data is returned as a list of
    key-value pairs rather than a dictionary because open graph allows duplicate keys,
    and the order of the keys is significant.
    """

    title = models.CharField(_("title"), max_length=255)
    # From https://schema.org/creativeWorkStatus
    status = models.CharField(
        _("status"),
        max_length=50,
        choices=Status.choices,
        default=Status.USABLE,
        help_text=_(
            'Must be "usable" to appear on the site. '
            'See <a href="https://schema.org/creativeWorkStatus">Schema.org</a> '
            "for details."
        ),
    )
    site = models.ForeignKey(
        Site,
        verbose_name=_("site"),
        on_delete=models.CASCADE,
        default=1,
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
        help_text=_(
            "The user who created/uploaded the content (for internal permissions, audits)."
        ),
    )
    author = models.ForeignKey(
        Author,
        verbose_name=_("author"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    description = models.TextField(_("description"), blank=True)

    # Equivalent to https://schema.org/dateCreated
    date_created = models.DateTimeField(
        _("date created"),
        blank=True,
        null=True,
        help_text=_("When the work was originally created."),
    )
    # Equivalent to https://schema.org/datePublished
    date_published = models.DateTimeField(
        _("date published"),
        blank=True,
        null=True,
        help_text=_("Must be non-blank and in the past for page to be 'live'"),
    )
    # Equivalent to https://schema.org/dateModified
    date_modified = models.DateTimeField(
        _("date modified"),
        blank=True,
        null=True,
        help_text=_("Time of last significant editorial update"),
    )
    # Equivalent to https://schema.org/expires
    expires = models.DateTimeField(
        _("expiration date"),
        blank=True,
        null=True,
        help_text=_("Must be blank or in the future for page to be 'live'"),
    )
    custom_copyright_notice = models.TextField(
        _("custom copyright notice"),
        blank=True,
        help_text=_(
            r"include a pair of curly braces {} where you want the year inserted"
        ),
    )
    custom_copyright_holder = models.CharField(
        _("custom copyright holder"),
        max_length=255,
        blank=True,
    )
    locale = models.CharField(_("locale"), max_length=10, default=DEFAULT_LOCALE)

    tags = TaggableManager(blank=True)

    class Meta:
        abstract = True
        get_latest_by = "date_published"
        ordering = ["-date_published"]
        # Nearly all queries will filter on these fields
        indexes = [
            models.Index(fields=["site", "status", "date_published", "expires", "slug"])
        ]

    def __str__(self):
        return self.title

    # Class properties
    icon_name = "file"
    schema_type = "CreativeWork"
    opengraph_type = "website"

    @property
    def copyright_holder(self):
        if self.custom_copyright_holder:
            return self.custom_copyright_holder
        elif self.author:
            return self.author.copyright_holder or self.author.name
        else:
            return self.site.vars.get_value("copyright_holder", self.site.name)

    @property
    def copyright_year(self):
        if self.date_published:
            return self.date_published.year
        elif self.date_created:
            return self.date_created.year
        else:
            return timezone.now().year

    @property
    def copyright_notice(self):
        conf = apps.get_app_config("genericsite")
        var = self.site.vars
        if self.custom_copyright_notice:
            return format_html(self.custom_copyright_notice, self.copyright_year)
        elif self.author and self.author.copyright_notice:
            return format_html(self.author.copyright_notice, self.copyright_year)
        elif notice := var.get_value("copyright_notice"):
            return format_html(notice, self.copyright_year)
        else:
            return format_html(
                conf.fallback_copyright, self.copyright_year, self.copyright_holder
            )

    @property
    def url(self):
        return f"https://{self.site.domain}{self.get_absolute_url()}"

    @property
    def schema(self) -> ThingSchema:
        """Return the data as a schema.org object."""
        schema_class = ThingSchema.get_class_for_label(self.schema_type)
        schema = schema_class(
            headline=self.title,
            description=self.description,
            creativeWorkStatus=self.status,
            url=self.url,
            dateCreated=self.date_created,
            datePublished=self.date_published,
            dateModified=self.date_modified,
            expires=self.expires,
        )
        if self.author:
            schema.author = self.author.schema
        try:
            tags = list(self.tags.names())
        except ValueError:
            # ValueError: objects need to have a primary key value before you
            # can access their tags.
            tags = []
        if tags:
            schema.keywords = tags
        return schema

    @property
    def opengraph(self) -> OpenGraph:
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
        og = OpenGraph(
            title=self.title,
            description=self.description,
            url=self.url,
            locale=self.locale,
            site_name=self.site.name,
            type=self.opengraph_type,
        )
        og.site_name = self.site.vars.get_value("brand", self.site.name)
        return og


######################################################################################
# Media Objects
######################################################################################
class MediaObject(AbstractCreativeWork):
    """Abstract base class for stored media files (image, audio, video, attachment).

    Every media object has an `content_field` attribute that names the field containing
    its content. This field is a FileField or ImageField, and is used to store the media
    file itself. The `content_field` is required to be overridden in subclasses.

    If `mime_type` is not populated, it will be guessed when the instance is saved,
    based on the file name stored in the `content_field` (using `mimetypes.guess_type`).
    """

    # Override inherited field. For MediaObjects, title is optional to facilitate easy uploads.
    title = models.CharField(_("title"), max_length=255, blank=True)
    # Open Graph has `type`, Schema.org calls it `encodingFormat`, both recommend MIME
    # type as the value
    mime_type = models.CharField(
        _("MIME type"), max_length=255, db_index=True, blank=True
    )
    upload_date = models.DateTimeField(_("when uploaded"), default=timezone.now)

    tags = TaggableManager(blank=True)

    class Meta:
        abstract = True
        unique_together = ("site", "title")

    def save(self, *args, **kwargs):
        if not self.mime_type:
            self.mime_type, _ = mimetypes.guess_type(
                getattr(self, self.content_field).name, strict=False
            )
        return super().save(*args, **kwargs)

    # Class properties
    content_field = None  # Must override in subclasses
    icon_name = "file-richtext"
    schema_type = "MediaObject"
    opengraph_type = "image"

    @property
    def _base_url(self):
        protocol = "http" if settings.DEBUG else "https"
        return f"{protocol}://{self.site.domain}"

    @property
    def url(self):
        path = getattr(self, self.content_field).url
        return f"{self._base_url}{path}"


class Image(MediaObject):
    image_file = models.ImageField(
        _("image file"),
        blank=True,
        null=True,
        width_field="width",
        height_field="height",
        upload_to=upload_to,
    )
    alt_text = models.CharField(_("alt text"), max_length=255, blank=True)
    width = models.PositiveIntegerField(_("width"), blank=True, null=True)
    height = models.PositiveIntegerField(_("height"), blank=True, null=True)

    # ImageSpec fields defining different renditions
    # Small, medium, and social renditions are used in layouts, so they are ResizeToFill
    # which crops to exact dimensions. Large and HD are ResizeToFit, which scales to fit
    # the bounding box, preserving aspect ratio, for featured images.
    hd1080p = ImageSpecField(
        source="image_file",
        processors=[ResizeToFit(1920, 1080)],
        format="JPEG",
        options={"quality": 60},
    )
    hd720p = ImageSpecField(
        source="image_file",
        processors=[ResizeToFit(1280, 720)],
        format="JPEG",
        options={"quality": 60},
    )
    social = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(1200, 630)],
        format="JPEG",
        options={"quality": 60},
    )
    large = ImageSpecField(
        source="image_file",
        processors=[ResizeToFit(960, 540)],
        format="JPEG",
        options={"quality": 60},
    )
    medium = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(400, 225)],
        format="JPEG",
        options={"quality": 60},
    )
    small = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(160, 90)],
        format="JPEG",
        options={"quality": 60},
    )
    portrait_small = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(90, 160)],
        format="JPEG",
        options={"quality": 60},
    )
    portrait_medium = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(225, 400)],
        format="JPEG",
        options={"quality": 60},
    )
    portrait_large = ImageSpecField(
        source="image_file",
        processors=[ResizeToFit(540, 960)],
        format="JPEG",
        options={"quality": 60},
    )
    portrait_cover = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(1000, 1500)],
        format="JPEG",
        options={"quality": 60},
    )
    portrait_social = ImageSpecField(
        source="image_file",
        processors=[ResizeToFill(1080, 1350)],
        format="JPEG",
        options={"quality": 60},
    )
    portrait_hd = ImageSpecField(
        source="image_file",
        processors=[ResizeToFit(1080, 1920)],
        format="JPEG",
        options={"quality": 60},
    )

    class Meta(MediaObject.Meta):
        verbose_name = _("image")
        verbose_name_plural = _("images")

    content_field = "image_file"
    icon_name = "image"

    @property
    def is_portrait(self):
        try:
            return self.height > self.width
        except TypeError:
            # Probably not saved yet
            return False

    @property
    def opengraph(self):
        return ImageProp(
            url=f"{self._base_url}{self.image_file.url}",
            type=self.mime_type,
            width=self.width,
            height=self.height,
            alt=self.alt_text,
        )


class Attachment(MediaObject):
    file = models.FileField(_("file"), max_length=255, upload_to=upload_to)

    class Meta(MediaObject.Meta):
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    content_field = "file"


#######################################################################
# Content models
#######################################################################


class CreativeWorkQuerySet(models.QuerySet):
    def live(self):
        return self.filter(
            models.Q(expires__isnull=True) | models.Q(expires__gt=timezone.now()),
            status=Status.USABLE,
            date_published__lte=timezone.now(),
        )


class GenericPageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("site", "share_image")


#######################################################################
class BasePage(AbstractCreativeWork):
    "A model to represent a generic page."

    slug = models.SlugField(_("slug"))
    # From https://schema.org/articleBody or https://schema.org/text
    body = models.TextField(_("body content"), blank=True)
    share_image = models.ForeignKey(
        "Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("Image for social sharing"),
        related_name="+",
    )
    custom_icon = models.CharField(
        _("custom icon"),
        max_length=50,
        blank=True,
        help_text="<a href=https://icons.getbootstrap.com/#icons target=iconlist>icon list</a>",
    )
    seo_title = models.CharField(_("SEO title override"), max_length=255, blank=True)
    seo_description = models.CharField(
        _("SEO description override"), max_length=255, blank=True
    )
    base_template = models.CharField(
        _("base template"),
        max_length=255,
        blank=True,
        help_text=_(
            "Replaces the standard base.html root layout. This allows you to have a "
            "totally custom layout for a page."
        ),
    )
    content_template = models.CharField(
        _("content body template"),
        max_length=255,
        blank=True,
        help_text=_(
            "The template that renders the content body within the page layout "
            "provided by the base.html. This only affects the 'main' section of "
            "the page, the rest of the layout is inherited from base.html."
        ),
    )

    objects = GenericPageManager.from_queryset(CreativeWorkQuerySet)()

    class Meta(AbstractCreativeWork.Meta):
        abstract = True
        verbose_name = _("page")
        verbose_name_plural = _("pages")

    def get_absolute_url(self):
        return reverse("generic_page", kwargs={"page_slug": self.slug})

    # Class properties
    schema_type = "WebPage"
    opengraph_type = "website"

    @property
    def icon_name(self):
        "name of an icon to represent this object"
        return self.custom_icon or self.site.vars.get_value("default_icon", "file-text")

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
    def has_excerpt(self):
        """True if there is more body text to read after the excerpt. False if
        excerpt == body.
        """
        config = apps.get_app_config("genericsite")
        return config.pagebreak_separator in self.body


#######################################################################
class Section(BasePage):
    "A model to represent major site categories."

    objects = GenericPageManager.from_queryset(CreativeWorkQuerySet)()

    class Meta(BasePage.Meta):
        verbose_name = _("section")
        verbose_name_plural = _("sections")
        constraints = [
            models.UniqueConstraint(
                fields=["site", "slug"], name="unique_section_slug_per_site"
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.site.name})"

    def get_absolute_url(self):
        return reverse("section_page", kwargs={"section_slug": self.slug})


#######################################################################
class Page(BasePage):
    "A model to represent a generic evergreen page or 'landing page'."

    objects = GenericPageManager.from_queryset(CreativeWorkQuerySet)()

    class Meta(BasePage.Meta):
        unique_together = ("site", "slug")
        verbose_name = _("page")
        verbose_name_plural = _("pages")

    def get_absolute_url(self):
        return reverse("landing_page", kwargs={"page_slug": self.slug})


#######################################################################
class HomePage(BasePage):
    "A model to represent the site home page."

    admin_name = models.CharField(
        _("admin name"),
        max_length=255,
        unique=True,
        help_text=_("Name used in the admin to distinguish from other home pages"),
    )
    objects = GenericPageManager.from_queryset(CreativeWorkQuerySet)()

    class Meta(BasePage.Meta):
        verbose_name = _("home page")
        verbose_name_plural = _("home pages")

    def get_absolute_url(self):
        return reverse("home_page")


#######################################################################
class ArticleSeries(models.Model):
    """
    A model to represent a series of articles. This model is used to group articles
    together in a series. The series is not a page, but a way to group articles for
    display in feeds and to provide a way to navigate between articles in the series.
    """

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"))
    description = models.TextField(_("description"), blank=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name=_("site"))

    def __str__(self):
        return self.name


#######################################################################
class ArticleManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("site", "section", "series", "share_image")
        )


class Article(BasePage):
    "Articles are the bread and butter of a site. They will appear in feeds."

    section = models.ForeignKey(
        Section, verbose_name=_("section"), on_delete=models.PROTECT
    )
    series = models.ForeignKey(
        ArticleSeries,
        verbose_name=_("series"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    image_set = models.ManyToManyField(Image, verbose_name=_("related images"))
    attachment_set = models.ManyToManyField(Attachment, verbose_name=_("attachments"))

    objects = ArticleManager.from_queryset(CreativeWorkQuerySet)()

    # Intentionally not inherting from AbstractCreativeWork's Meta because `ordering`
    # and `order_with_respect_to` are not compatible with each other.
    class Meta:
        get_latest_by = "date_published"
        order_with_respect_to = "series"
        verbose_name = _("article")
        verbose_name_plural = _("articles")
        constraints = [
            models.UniqueConstraint(
                fields=["site", "section", "slug"],
                name="unique_article_slug_per_section",
            )
        ]
        indexes = [
            models.Index(
                fields=[
                    "site",
                    "status",
                    "date_published",
                    "expires",
                    "section",
                    "slug",
                ]
            )
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            # Django should do the Right Thing setting _order on new instances
            return super().save(*args, **kwargs)

        # When adding a series to an existing article, Django does not set _order,
        # so it has the default 0, which breaks get_next_in_order
        if self.series and not self._order:
            # Order not assigned, place at end of series
            self._order = self.series.get_article_order().count() + 1
        elif not self.series:
            # If the series is removed, reset the order
            self._order = 0
        # Save before resetting series order so the query finds this instance
        retval = super().save(*args, **kwargs)
        if self.series:
            # Possible the series has changed, which could cause dupes. This
            # will reset the _order for all articles in the series.
            self.series.set_article_order(self.series.get_article_order())
        return retval

    def get_absolute_url(self):
        if self.series:
            return reverse(
                "article_series_page",
                kwargs={
                    "section_slug": self.section.slug,
                    "series_slug": self.series.slug,
                    "article_slug": self.slug,
                },
            )
        return reverse(
            "article_page",
            kwargs={"article_slug": self.slug, "section_slug": self.section.slug},
        )

    schema_type = "Article"
    opengraph_type = "article"

    @property
    def opengraph(self):
        "Serialize data to Open Graph metatags"
        og = OGArticle(
            title=self.title,
            description=self.description,
            url=self.url,
            published_time=self.date_published,
            section=self.section,
            modified_time=self.date_modified,
            expiration_time=self.expires,
            site_name=self.site.name,
        )
        if self.share_image:
            og.image = [self.share_image.opengraph]
        if self.author:
            og.author = [self.author.url]
        tags = list(self.tags.names())
        if tags:
            og.tag = tags
        return og

    @property
    def series_part(self):
        if not self.series:
            return None

        # Return a string formatted as "Part 1 of 3" based on the order of the article in the series
        ids = list(self.series.get_article_order())
        return f"Part {ids.index(self.id) + 1} of {len(ids)}"


#######################################################################
# Site Menus
#######################################################################
class Menu(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name=_("site"))
    admin_name = models.CharField(_("admin name"), max_length=255)
    slug = models.SlugField(
        _("slug"),
        help_text=_(
            "Slug 'main-nav' will automatically be included in generic headers."
        ),
    )
    title = models.CharField(_("title"), max_length=255, blank=True)

    class Meta:
        unique_together = ("site", "slug")

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
    share_image = models.ForeignKey(
        "Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("Image for social sharing"),
        related_name="+",
    )

    class Meta:
        unique_together = (("menu", "url"), ("menu", "title"))

    def __str__(self):
        return format_html('<a href="{}">{}</a>', self.url, self.title)

    @property
    def icon_name(self):
        "name of an icon to represent this object"
        return self.custom_icon or self.site.vars.get_value(
            "default_icon", "link-45deg"
        )

    @property
    def image(self):
        if self.share_image:
            return [self.share_image]
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
