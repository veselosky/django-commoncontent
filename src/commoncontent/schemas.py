"""
These schemas are dataclasses based on the definitions of respective items from
Schema.org and Open Graph <https://ogp.me/>.
"""

import dataclasses
import typing as T
import urllib.parse
from datetime import date
from enum import Enum

from django.db import models
from django.utils.html import escape, format_html, json_script, mark_safe, strip_tags

from commoncontent.common import Status


def validate_http_url(value):
    parsed_url = urllib.parse.urlparse(value)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValueError(f"{value} is not a valid URL")
    if not parsed_url.scheme.startswith("http"):
        raise ValueError("URL must start with http or https")
    return value


########################################################################################
# Schema.org objects
########################################################################################
class SchemaBase:
    def asdict(self):
        return {k: v for k, v in self.items() if v is not None}

    def items(self):
        """Yield the name and value of each field in the dataclass (similar to the dict
        method).
        """
        for field in dataclasses.fields(self):
            yield field.name, getattr(self, field.name)

    def safe_dict(self):
        """Return a dictionary of the object's fields with HTML escaped values."""
        items = {}
        for k, v in self.items():
            if v is None:
                continue
            if isinstance(v, SchemaBase):
                items[k] = v.safe_dict()
            else:
                items[k] = escape(strip_tags(v))
        items["@context"] = "https://schema.org"
        items["@type"] = self._label
        return items


@dataclasses.dataclass
class ThingSchema(SchemaBase):
    "Schema.org Thing object"

    name: T.Optional[str] = None
    description: T.Optional[str] = None
    url: T.Optional[str] = None
    image: T.Optional[T.Union[str, SchemaBase]] = None
    _label: T.ClassVar[str] = "Thing"
    _registry: T.ClassVar[dict] = {}

    def __post_init__(self):
        if self.url:
            self.url = validate_http_url(self.url)

    @classmethod
    def _register(cls, subclass):
        cls._registry[subclass._label] = subclass

    def __str__(self):
        schema = super().safe_dict()
        out = json_script(schema, element_id="schema-data")
        return mark_safe(out.replace("application/json", "application/ld+json"))

    def __init_subclass__(cls):
        ThingSchema._register(cls)

    @classmethod
    def get_class_for_label(cls, label):
        """
        ThingSchema keeps a registry of all subclasses that have been defined. This
        method returns the class that corresponds to the given label, or the base class
        if no subclass has been defined for that label.
        """
        return cls._registry.get(label, cls)


@dataclasses.dataclass
class CreativeWorkSchema(ThingSchema):
    "Schema.org CreativeWork object"

    abstract: T.Optional[str] = None
    alternativeHeadline: T.Optional[str] = None
    author: T.Optional[str] = None
    copyrightHolder: T.Optional[str] = None
    copyrightNotice: T.Optional[str] = None
    copyrightYear: T.Optional[str] = None
    creativeWorkStatus: T.Optional[Status] = None
    dateCreated: T.Optional[str] = None
    datePublished: T.Optional[str] = None
    dateModified: T.Optional[str] = None
    expires: T.Optional[str] = None
    headline: T.Optional[str] = None
    keywords: T.Optional[str] = None
    _label: T.ClassVar[str] = "CreativeWork"

    def __post_init__(self):
        if self.datePublished and isinstance(self.datePublished, date):
            self.datePublished = self.datePublished.isoformat()
        if self.dateModified and isinstance(self.dateModified, date):
            self.dateModified = self.dateModified.isoformat()
        if self.expires and isinstance(self.expires, date):
            self.expires = self.expires.isoformat()
        if isinstance(self.author, models.Model):
            self.author = str(self.author)


@dataclasses.dataclass
class WebPageSchema(CreativeWorkSchema):
    "Schema.org WebPage object"

    breadcrumb: T.Optional[str] = None
    lastReviewed: T.Optional[str] = None
    mainContentOfPage: T.Optional[str] = None
    primaryImageOfPage: T.Optional[str] = None
    relatedLink: T.Optional[str] = None
    reviewedBy: T.Optional[str] = None
    significantLink: T.Optional[str] = None
    significantLinks: T.Optional[str] = None
    _label: T.ClassVar[str] = "WebPage"


@dataclasses.dataclass
class MediaObjectSchema(CreativeWorkSchema):
    "Schema.org MediaObject object"

    contentUrl: T.Optional[str] = None
    embedUrl: T.Optional[str] = None
    encodingFormat: T.Optional[str] = None
    fileSize: T.Optional[str] = None
    height: T.Optional[str] = None
    playerType: T.Optional[str] = None
    productionCompany: T.Optional[str] = None
    regionsAllowed: T.Optional[str] = None
    requiresSubscription: T.Optional[str] = None
    uploadDate: T.Optional[str] = None
    width: T.Optional[str] = None
    _label: T.ClassVar[str] = "MediaObject"


@dataclasses.dataclass
class ArticleSchema(CreativeWorkSchema):
    "Schema.org Article object"

    articleBody: T.Optional[str] = None
    articleSection: T.Optional[str] = None
    wordCount: T.Optional[int] = None
    _label: T.ClassVar[str] = "Article"


@dataclasses.dataclass
class PersonSchema(ThingSchema):
    "Schema.org Person object"

    additionalName: T.Optional[str] = None
    address: T.Optional[str] = None
    birthDate: T.Optional[str] = None
    birthPlace: T.Optional[str] = None
    brand: T.Optional[str] = None
    contactPoint: T.Optional[str] = None
    deathDate: T.Optional[str] = None
    deathPlace: T.Optional[str] = None
    email: T.Optional[str] = None
    familyName: T.Optional[str] = None
    givenName: T.Optional[str] = None
    nationality: T.Optional[str] = None
    _label: T.ClassVar[str] = "Person"


########################################################################################
# Open Graph objects
########################################################################################
metatag = '<meta property="{}:{}" content="{}" />\n'


class OGGender(Enum):
    "Gender as defined at ogp.me. Sorry non-binary folks, FB hates you."

    male = "male"
    female = "female"


@dataclasses.dataclass
class StructuredProperty(SchemaBase):
    "Represents a generic structured property"

    _prefix: T.ClassVar[str] = ""
    type: T.Optional[str] = None
    url: T.Optional[str] = None
    secure_url: T.Optional[str] = None

    def __post_init__(self):
        if self.url:
            self.url = validate_http_url(self.url)
        if self.secure_url:
            self.secure_url = validate_http_url(self.secure_url)

    def __str__(self):
        if not self._prefix:
            return ""
        val = format_html(metatag, "og", self._prefix, self.url)
        for attr, content in self.items():
            if attr == "url":
                continue
            if content:
                val += format_html(metatag, f"og:{self._prefix}", attr, content)
        return val

    def get_absolute_url(self):
        return self.url.path


@dataclasses.dataclass
class AudioProp(StructuredProperty):
    "Represents the 'audio' structured property"

    _prefix: T.ClassVar[str] = "audio"


@dataclasses.dataclass
class VideoProp(StructuredProperty):
    "Represents the 'video' structured property"

    _prefix: T.ClassVar[str] = "video"
    width: T.Optional[int] = None
    height: T.Optional[int] = None


@dataclasses.dataclass
class ImageProp(VideoProp):
    "Represents the 'image' structured property"

    _prefix: T.ClassVar[str] = "image"
    alt: T.Optional[str] = None


@dataclasses.dataclass
class OpenGraph(SchemaBase):
    "A generic open graph object (page)"

    # The allegedly required fields for an OG object
    title: str
    url: T.Optional[str] = None
    type: str = "website"
    image: T.Union[None, ImageProp, T.List[ImageProp]] = None

    description: T.Optional[str] = None
    determiner: T.Optional[str] = None
    locale: T.Optional[str] = None
    site_name: T.Optional[str] = None

    def __post_init__(self):
        if self.url:
            self.url = validate_http_url(self.url)
        if isinstance(self.image, ImageProp):
            self.image = [self.image]

    def __str__(self):
        # Subclasses with attrs will use a separate namespace for them, so here we ONLY
        # want to output what's implemented in this class.
        basic_attrs = "description determiner locale site_name title type".split()
        val = format_html(metatag, "og", "url", self.url)
        for attr, content in self.items():
            if attr == "url" or content is None:
                continue
            elif attr in ("audio", "image", "video"):
                # These are lists of StructuredProps
                for item in content:
                    val += str(item)
            elif attr == "locale_alternate":
                for locale in content:
                    val += format_html(metatag, "og", attr, locale)
            elif content and attr in basic_attrs:
                val += format_html(metatag, "og", attr, content)
        return val


@dataclasses.dataclass
class OGArticle(OpenGraph):
    "OG Article object"

    # Fields without defaults
    published_time: T.Optional[str] = None
    modified_time: T.Optional[str] = None
    expiration_time: T.Optional[str] = None
    section: T.Union[None, str, models.Model] = None
    # Structured properties
    author: T.Optional[T.List[T.Union[str, models.Model]]] = None
    tag: T.Optional[T.List[str]] = None

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        # Force the type to article
        self.type = "article"
        if isinstance(self.section, models.Model):
            self.section = str(self.section)

        for f in ("published_time", "modified_time", "expiration_time"):
            val = getattr(self, f)
            # Fun fact: datetime is a subclass of date, so this covers both
            if isinstance(val, date):
                setattr(self, f, val.isoformat())

    def __str__(self):
        val = super().__str__()
        prefix = "article"
        article_props = "published_time modified_time expiration_time section".split()
        for attr, content in self.items():
            if content is None:
                continue
            elif attr in article_props:
                val += format_html(metatag, prefix, attr, content)
            elif attr in ("author", "tag"):
                for tag in content:
                    val += format_html(metatag, prefix, attr, tag)
        return val


@dataclasses.dataclass
class OGBook(OpenGraph):
    "OG book object"

    # Fields without defaults
    isbn: T.Optional[str] = None
    release_date: T.Optional[str] = None
    # Structured properties
    author: T.Optional[T.List[T.Union[str, models.Model]]] = None
    tag: T.Optional[T.List[str]] = None

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        # Force the type to book
        self.type = "book"
        # Convert author to a list of strings
        if self.author and isinstance(self.author, models.Model):
            self.author = [str(self.author)]
        elif self.author:
            self.author = [str(author) for author in self.author]
        if self.release_date and isinstance(self.release_date, date):
            self.release_date = self.release_date.isoformat()

    def __str__(self):
        val = super().__str__()
        prefix = "book"
        book_props = "author isbn release_date".split()
        for attr, content in self.items():
            if content is None:
                continue
            elif attr in book_props:
                val += format_html(metatag, prefix, attr, content)
            elif attr in ("author", "tag"):
                for tag in content:
                    val += format_html(metatag, prefix, attr, tag)
        return val


# @dataclasses.dataclass
# class OGVideo(OpenGraph):
#     "OG video/movie object (type video.other)"

#     # Fields without defaults
#     duration: T.Optional[int]  # length in seconds
#     release_date: T.Optional[datetime]
#     # Fields with sensible defaults
#     type: str = "video.other"
#     # Structured properties
#     actor: T.List[str] = dataclasses.field(
#         default_factory=list
#     )  # FIXME ignoring roles for now
#     director: T.List[str] = dataclasses.field(default_factory=list)
#     writer: T.List[str] = dataclasses.field(default_factory=list)
#     tag: T.List[str] = dataclasses.field(default_factory=list)

#     def __str__(self):
#         val = super().__str__()
#         prefix = "video"
#         video_props = "duration release_date".split()
#         for attr, content in self.items():
#             if attr in video_props and content:
#                 val += format_html(metatag, prefix, attr, content)
#             elif attr in ("actor", "director", "tag", "writer") and content:
#                 for tag in content:
#                     val += format_html(metatag, prefix, attr, tag)
#         return val


# @dataclasses.dataclass
# class OGMovie(OGVideo):
#     "OG movie object (type video.movie)"

#     type: str = "video.movie"


# @dataclasses.dataclass
# class OGTVShow(OGVideo):
#     "OG TV series (video.tv_show)"

#     type: str = "video.tv_show"


# @dataclasses.dataclass
# class OGEpisode(OGVideo):
#     "OG TV episode (video.episode)"

#     series: T.Optional[OGTVShow]
#     type: str = "video.episode"

#     def __str__(self):
#         val = super().__str__()
#         if self.series:
#             val += format_html(metatag, "video", "series", self.series)
#         return val


@dataclasses.dataclass
class OGProfile(OpenGraph):
    "OG's 'person' object"

    first_name: T.Optional[str] = None
    last_name: T.Optional[str] = None
    username: T.Optional[str] = None
    gender: T.Optional[OGGender] = None

    def __post_init__(self, *args, **kwargs):
        super().__post_init__(*args, **kwargs)
        # Force the type to profile
        self.type = "profile"

    def __str__(self):
        val = super().__str__()
        profile_props = "first_name last_name username gender".split()
        for attr, content in self.items():
            if content and attr in profile_props:
                val += format_html(metatag, "profile", attr, content)
        return val


# Omitting the music category of objects for now.
