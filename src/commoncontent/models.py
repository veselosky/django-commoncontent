import mimetypes

from django.apps import apps
from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.translation import to_locale
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit
from taggit.managers import TaggableManager

from commoncontent.common import AliasForField, Status, upload_to
from commoncontent.schemas import (
    ImageProp,
    OGArticle,
    OGProfile,
    OpenGraph,
    ThingSchema,
)

# Transform "en-us" to "en_US"
DEFAULT_LOCALE = to_locale(settings.LANGUAGE_CODE)
sitevars = apps.get_app_config("sitevars")


######################################################################################
class Author(models.Model):
    """
    An Author, in Schema.org, is a Person or Organization to whom credit is attributed.
    Neither Schema.org's Person nor Open Graph's Profile provides much interesting in
    the way of data model. For CommonContent, we use the model to provide basic
    attribution, and to populate a profile page. The Author can also be used to store
    default copyright information.
    """

    site = models.ForeignKey(
        sitevars.site_model,
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

    # From https://schema.org/headline
    title = models.CharField(
        _("title"), max_length=255, help_text=_("The main headline")
    )
    # From https://schema.org/alternativeHeadline
    subtitle = models.CharField(
        _("subtitle"),
        max_length=255,
        blank=True,
        help_text=_("A subtitle or secondary headline"),
    )
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
        sitevars.site_model,
        verbose_name=_("site"),
        on_delete=models.CASCADE,
        default=1,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
        help_text=_(
            "The user who created/uploaded the content (for internal permissions, audits)."
        ),
    )
    # From https://schema.org/author
    author = models.ForeignKey(
        Author,
        verbose_name=_("author"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # From https://schema.org/description & https://schema.org/abstract
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_(
            "An abstract of the content or marketing description. "
            "Intended to entice a reader to click through to the content. "
            "May contain inline HTML and multiple paragraphs."
        ),
    )

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
    # https://schema.org/copyrightNotice
    custom_copyright_notice = models.TextField(
        _("custom copyright notice"),
        blank=True,
        help_text=_(
            r"include a pair of curly braces {} where you want the year inserted"
        ),
    )
    # https://schema.org/copyrightHolder
    custom_copyright_holder = models.CharField(
        _("custom copyright holder"),
        max_length=255,
        blank=True,
    )
    custom_icon = models.CharField(
        _("custom icon"),
        max_length=50,
        blank=True,
        help_text="<a href=https://icons.getbootstrap.com/#icons target=iconlist>icon list</a>",
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
    default_icon_name = "file"
    schema_type = "CreativeWork"
    opengraph_type = "website"
    headline = AliasForField("title")
    alternative_headline = AliasForField("subtitle")

    @property
    def abstract(self):
        """Rich text excerpt for use in teases and feed content. If no abstract has
        been specified, returns the full description text."""
        if self.description:
            return self.description
        if hasattr(self, "excerpt"):
            return self.excerpt
        return ""

    @property
    def icon_name(self):
        """name of an icon to represent this object"""
        if self.custom_icon:
            return self.custom_icon
        return self.default_icon_name

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
        conf = apps.get_app_config("commoncontent")
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
            alternativeHeadline=self.subtitle,
            author=self.author,
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
        use by Common Content, the ones serialized here are only the ones declared in
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


class WebContent(AbstractCreativeWork):
    """
    A model to represent web content, i.e. HTML.

    CreativeWorks bifurcate into two types: MediaObjects (images, audio, video, etc.) and
    WebContent (HTML, text, etc.) that can reference MediaObjects.
    """

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

    class Meta(AbstractCreativeWork.Meta):
        verbose_name = _("web content")
        verbose_name_plural = _("web content")
        abstract = True

    @cached_property
    def excerpt(self):
        """Rich text excerpt for use in teases and feed content. If no excerpt has
        been specified, returns the full body text."""
        config = apps.get_app_config("commoncontent")
        if not self.body:
            return ""
        excerpt = self.body.split(config.pagebreak_separator, maxsplit=1)[0]
        return truncatewords_html(excerpt, config.excerpt_max_words)

    @property
    def has_excerpt(self):
        """True if there is more body text to read after the excerpt. False if
        excerpt == body.
        """
        return not self.excerpt == self.body


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
    default_icon_name = "file-richtext"
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
    default_icon_name = "image"

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


# Subclasses of WebContent all can have sets of images associated with them. However,
# due to the technicalities of ManyToMany relationships and abstract models, we couldn't
# declare the ManyToManyField on the WebContent class. Each concrete subclass requires
# its own concrete through-table, and must declare its own m2m field. We declare the
# through-table as an abstract model for the shared fields, and then subclass it for
# each concrete WebContent subclass. (This is also true of Attachments, but we don't
# need to store any relationship data for Attachments, so there's no need to pre-declare
# a through-table. The ManyToManyField on the WebContent subclass is sufficient.)
class BaseContentImage(models.Model):
    """
    Base model for associating images with WebContent subclasses.
    Includes shared fields for the relationship.
    """

    image = models.ForeignKey(
        "Image",
        on_delete=models.CASCADE,
        verbose_name=_("image"),
    )
    title = models.CharField(_("title"), max_length=255, blank=True)
    description = models.TextField(_("description"), blank=True)
    alt_text = models.CharField(_("alt text"), max_length=255, blank=True)
    order = models.PositiveIntegerField(_("order"), default=0)
    tags = TaggableManager(blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.image}"


class ArticleImage(BaseContentImage):
    """
    Through-table for associating images with Articles.
    """

    article = models.ForeignKey(
        "Article",
        on_delete=models.CASCADE,
        related_name="article_images",
        verbose_name=_("article"),
    )


class SectionImage(BaseContentImage):
    """
    Through-table for associating images with Sections.
    """

    section = models.ForeignKey(
        "Section",
        on_delete=models.CASCADE,
        related_name="section_images",
        verbose_name=_("section"),
    )


class PageImage(BaseContentImage):
    """
    Through-table for associating images with Pages.
    """

    page = models.ForeignKey(
        "Page",
        on_delete=models.CASCADE,
        related_name="page_images",
        verbose_name=_("page"),
    )


class HomePageImage(BaseContentImage):
    """
    Through-table for associating images with HomePages.
    """

    homepage = models.ForeignKey(
        "HomePage",
        on_delete=models.CASCADE,
        related_name="homepage_images",
        verbose_name=_("home page"),
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
class BasePage(WebContent):
    "A model to represent a generic page."

    slug = models.SlugField(_("slug"))
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
    default_icon_name = "file-text"


#######################################################################
class Section(BasePage):
    "A model to represent major site categories."

    image_set = models.ManyToManyField(
        "Image",
        through="SectionImage",
        related_name="sections",
        verbose_name=_("related images"),
    )
    attachment_set = models.ManyToManyField(Attachment, verbose_name=_("attachments"))

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

    image_set = models.ManyToManyField(
        "Image",
        through="PageImage",
        related_name="pages",
        verbose_name=_("related images"),
    )
    attachment_set = models.ManyToManyField(Attachment, verbose_name=_("attachments"))

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
    image_set = models.ManyToManyField(
        "Image",
        through="HomePageImage",
        related_name="homepages",
        verbose_name=_("related images"),
    )
    attachment_set = models.ManyToManyField(Attachment, verbose_name=_("attachments"))

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
    site = models.ForeignKey(
        sitevars.site_model, on_delete=models.CASCADE, verbose_name=_("site")
    )

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
    image_set = models.ManyToManyField(
        "Image",
        through="ArticleImage",
        related_name="articles",
        verbose_name=_("related images"),
    )

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
    site = models.ForeignKey(
        sitevars.site_model, on_delete=models.CASCADE, verbose_name=_("site")
    )
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
    of properties required by CommonContent is: url, title and the extension
    "icon_name". For completeness, the model also supports storing a description and
    image, though at this writing CommonContent templates do not use these properties.
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
    def __init__(self, site, title: str = "", sections=None, pages=None) -> None:
        self.site = site
        self.title = title
        self.sections = sections or Section.objects.live().filter(site=site).order_by(
            "title"
        )
        self.pages = pages

    @property
    def links(self):
        try:
            home = HomePage.objects.live().filter(site=self.site).latest()
        except HomePage.DoesNotExist:
            home = HomePage(
                site=self.site,
                admin_name="__DEBUG__",
                title=self.site.name,
                date_published=timezone.now(),
            )

        menu = [home]
        menu.extend(self.sections)
        if self.pages:
            menu.extend(self.pages)
        return menu
