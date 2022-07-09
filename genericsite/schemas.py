"""
These models are based on the definitions of Open Graph objects documented at
https://ogp.me/
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from django.utils.html import format_html, format_html_join
from pydantic import BaseModel, HttpUrl, validator

metatag = '<meta property="{}:{}" content="{}" />\n'


class OGGender(Enum):
    "Gender as defined at ogp.me. Sorry non-binary folks, FB hates you."
    male = "male"
    female = "female"


class StructuredProperty(BaseModel):
    "Represents a generic structured property"
    _prefix: Optional[str] = None
    url: HttpUrl
    secure_url: Optional[HttpUrl]
    type: Optional[str]

    @validator("secure_url")
    def secure_url_requires_https(cls, v):
        assert v.scheme == "https", "secure_url must start with https://"
        return v

    def __str__(self):
        if not self._prefix:
            return ""
        val = format_html(metatag, "og", self._prefix, self.url)
        for attr, content in self:
            if attr == "url":
                continue
            if content:
                val += format_html(metatag, f"og:{self._prefix}", attr, content)
        return val


class AudioProp(StructuredProperty):
    "Represents the 'audio' structured property"
    _prefix = "audio"


class VideoProp(StructuredProperty):
    "Represents the 'video' structured property"
    _prefix = "video"
    width: Optional[int]
    height: Optional[int]


class ImageProp(VideoProp):
    "Represents the 'image' structured property"
    _prefix = "image"
    alt: Optional[str]


class OpenGraph(BaseModel, orm_mode=True):
    "A generic open graph object (page)"
    audio: List[AudioProp] = []
    description: Optional[str]
    determiner: Optional[str]
    image: List[ImageProp] = []
    locale: Optional[str]
    locale_alternate: List[str] = []
    site_name: Optional[str]
    title: str
    type: str = "website"
    url: HttpUrl
    video: List[VideoProp] = []

    def __str__(self):
        # Subclasses with attrs will use a separate namespace for them, so here we ONLY
        # want to output what's implemented in this class.
        basic_attrs = "description determiner locale site_name title type".split()
        val = format_html(metatag, "og", "url", self.url)
        for attr, content in self:
            if attr == "url":
                continue
            elif attr in ("audio", "image", "video"):
                # These are lists of StructuredProps
                for item in content:
                    val += str(item)
            elif attr == "locale_alternate":
                for locale in content:
                    val += format_html(metatag, "og", attr, content)
            elif content and attr in basic_attrs:
                val += format_html(metatag, "og", attr, content)
        return val


class OGArticle(OpenGraph):
    "OG Article object"
    published_time: Optional[datetime]
    modified_time: Optional[datetime]
    expiration_time: Optional[datetime]
    author: List[HttpUrl] = []
    section: Optional[str]
    tag: List[str] = []
    type: str = "article"

    def __str__(self):
        val = super().__str__()
        prefix = "article"
        article_props = "published_time modified_time expiration_time section".split()
        for attr, content in self:
            if attr in article_props and content:
                val += format_html(metatag, prefix, attr, content)
            elif attr in ("author", "tag") and content:
                for tag in content:
                    val += format_html(metatag, prefix, attr, tag)
        return val


class OGBook(OpenGraph):
    "OG book object"
    author: List[HttpUrl] = []
    isbn: Optional[str]
    release_date: Optional[datetime]
    tag: List[str] = []
    type: str = "book"

    def __str__(self):
        val = super().__str__()
        prefix = "book"
        book_props = "author isbn release_date".split()
        for attr, content in self:
            if attr in book_props and content:
                val += format_html(metatag, prefix, attr, content)
            elif attr in ("author", "tag") and content:
                for tag in content:
                    val += format_html(metatag, prefix, attr, tag)
        return val


class OGVideo(OpenGraph):
    "OG video/movie object (type video.other)"
    actor: List[HttpUrl] = []  # FIXME ignoring roles for now
    director: List[HttpUrl] = []
    writer: List[HttpUrl] = []
    duration: Optional[int]  # length in seconds
    release_date: Optional[datetime]
    tag: List[str] = []
    type: str = "video.other"

    def __str__(self):
        val = super().__str__()
        prefix = "video"
        video_props = "duration release_date".split()
        for attr, content in self:
            if attr in video_props and content:
                val += format_html(metatag, prefix, attr, content)
            elif attr in ("actor", "director", "tag", "writer") and content:
                for tag in content:
                    val += format_html(metatag, prefix, attr, tag)
        return val


class OGMovie(OGVideo):
    "OG movie object (type video.movie)"
    type: str = "video.movie"


class OGTVShow(OGVideo):
    "OG TV series (video.tv_show)"
    type: str = "video.tv_show"


class OGEpisode(OGVideo):
    "OG TV episode (video.episode)"
    series: Optional[OGTVShow]
    type: str = "video.episode"

    def __str__(self):
        val = super().__str__()
        if self.series:
            val += format_html(metatag, "video", "series", self.series)
        return val


class OGProfile(OpenGraph):
    "OG's 'person' object"
    first_name: Optional[str]
    last_name: Optional[str]
    username: Optional[str]
    gender: Optional[OGGender]
    type: str = "profile"

    def __str__(self):
        val = super().__str__()
        profile_props = "first_name last_name username gender".split()
        for attr, content in self:
            if content and attr in profile_props:
                val += format_html(metatag, "profile", attr, content)
        return val


# Omitting the music category of objects for now.
