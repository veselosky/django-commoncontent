"""
Export functions for exporting Common Content sites to Hugo format.

The main entry points are:
- export_page: exports a single BasePage instance to a Hugo page bundle
- export_site: exports an entire site to a Hugo project directory
"""

import logging
import os
import re
import shutil
from pathlib import Path

import yaml
from django.apps import apps
from django.conf import settings

from commoncontent.common import Status
from commoncontent.models import Article, Attachment, HomePage, Image, Page, Section

logger = logging.getLogger(__name__)

Site = apps.get_app_config("sitevars").Site


def _format_datetime(dt):
    """Format a datetime for YAML front matter."""
    if dt is None:
        return None
    return dt.isoformat()


def _build_front_matter(instance):
    """Build a dictionary of Hugo front matter fields from a page instance."""
    fm = {}
    if instance.title:
        fm["title"] = instance.title
    if instance.subtitle:
        fm["subtitle"] = instance.subtitle
    if instance.seo_title:
        fm["seo_title"] = instance.seo_title
    if instance.seo_description:
        fm["description"] = instance.seo_description
    # draft: false if USABLE, true otherwise
    fm["draft"] = instance.status != Status.USABLE
    if instance.date_created:
        fm["dateCreated"] = _format_datetime(instance.date_created)
    if instance.date_published:
        fm["publishdate"] = _format_datetime(instance.date_published)
    if instance.date_modified:
        fm["lastmod"] = _format_datetime(instance.date_modified)
    if instance.expires:
        fm["expirydate"] = _format_datetime(instance.expires)
    # copyright_notice returns a SafeString (str subclass); concatenation
    # produces a plain str which yaml.safe_dump can serialize cleanly.
    copyright = instance.copyright_notice
    if copyright:
        fm["copyright"] = copyright + ""
    if instance.icon_name:
        fm["icon_name"] = instance.icon_name
    if instance.share_image:
        fm["cover"] = instance.share_image.url
    return fm


def _render_page(instance, front_matter, body):
    """Render a Hugo page with YAML front matter and HTML body."""
    yaml_str = yaml.safe_dump(front_matter, default_flow_style=False)
    return f"---\n{yaml_str}---\n{body}\n"


def _get_bundle_path(instance, content_dir: Path):
    """Get the page bundle directory path for a page instance."""
    # Remove .html suffix for bundle dir
    url_path = instance.get_absolute_url().removesuffix(".html")
    # Normalize: remove leading/trailing slashes
    url_path = url_path.strip("/")
    if url_path:
        bundle_dir = content_dir / url_path
    else:
        # Home page: root of content dir
        bundle_dir = content_dir
    return bundle_dir


def _get_index_filename(instance):
    """Get the index file name for a page instance."""
    if isinstance(instance, (HomePage, Section)):
        return "_index.html"
    return "index.html"


def _export_media_file(media_obj, bundle_dir, mode="skip", force=False):
    """Export a media object's file to the page bundle directory.

    Returns the relative filename within the bundle, or None if skipped.
    """
    content_field = getattr(media_obj, media_obj.content_field)
    if not content_field:
        return None

    filename = os.path.basename(content_field.name)
    dest = bundle_dir / filename

    if dest.exists() and mode == "skip":
        return filename

    if dest.exists() and mode == "overwrite" and not force:
        # Check modification time
        dest_mtime = dest.stat().st_mtime
        export_time = media_obj.upload_date
        if export_time:
            export_ts = export_time.timestamp()
            if dest_mtime > export_ts:
                return filename

    bundle_dir.mkdir(parents=True, exist_ok=True)
    try:
        content_field.open("rb")
        with open(dest, "wb") as f:
            for chunk in content_field.chunks():
                f.write(chunk)
        content_field.close()
    except (IOError, OSError):
        logger.error("Failed to export media file %s", content_field.name)
        return None
    return filename


def _build_image_metadata(image):
    """Build metadata dict for an Image."""
    meta = {}
    if image.title:
        meta["title"] = image.title
    if image.mime_type:
        meta["mime_type"] = image.mime_type
    if image.upload_date:
        meta["upload_date"] = _format_datetime(image.upload_date)
    tags = list(image.tags.names())
    if tags:
        meta["tags"] = tags
    if image.alt_text:
        meta["alt_text"] = image.alt_text
    if image.width:
        meta["width"] = image.width
    if image.height:
        meta["height"] = image.height
    return meta


def _build_attachment_metadata(attachment):
    """Build metadata dict for an Attachment."""
    meta = {}
    if attachment.title:
        meta["title"] = attachment.title
    if attachment.mime_type:
        meta["mime_type"] = attachment.mime_type
    if attachment.upload_date:
        meta["upload_date"] = _format_datetime(attachment.upload_date)
    tags = list(attachment.tags.names())
    if tags:
        meta["tags"] = tags
    return meta


def _export_media_metadata(media_obj, filename, bundle_dir):
    """Export a YAML metadata file for a media object."""
    if isinstance(media_obj, Image):
        meta = _build_image_metadata(media_obj)
    elif isinstance(media_obj, Attachment):
        meta = _build_attachment_metadata(media_obj)
    else:
        return

    meta_path = bundle_dir / f"{filename}.yaml"
    yaml_str = yaml.safe_dump(meta, default_flow_style=False)
    meta_path.write_text(yaml_str, encoding="utf-8")


def _get_image_collection_name(instance):
    """Get the related name for the image collection for an instance."""
    if isinstance(instance, Article):
        return "article_images"
    elif isinstance(instance, Section):
        return "section_images"
    elif isinstance(instance, Page):
        return "page_images"
    elif isinstance(instance, HomePage):
        return "homepage_images"
    return None


def _find_local_img_urls(body):
    """Find all local image URLs referenced in img tags in HTML body."""
    if not body:
        return []
    # Match src attributes of img tags
    pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    urls = pattern.findall(body)
    # Filter to local URLs only (not starting with http:// or https:// or //)
    local_urls = []
    for url in urls:
        if url.startswith(("http://", "https://", "//")):
            continue
        local_urls.append(url)
    return local_urls


def _resolve_local_url_to_file(url):
    """Try to resolve a local URL to an actual file path in media or static roots."""
    media_url = getattr(settings, "MEDIA_URL", "media/")
    static_url = getattr(settings, "STATIC_URL", "static/")
    media_root = Path(settings.MEDIA_ROOT)
    static_root = Path(settings.STATIC_ROOT)

    # Normalize url: strip leading /
    clean_url = url.lstrip("/")

    # Check if it's a media URL
    if clean_url.startswith(media_url.lstrip("/")):
        relative = clean_url[len(media_url.lstrip("/")) :]
        candidate = media_root / relative
        if candidate.exists():
            return candidate

    # Check if it's a static URL
    if clean_url.startswith(static_url.lstrip("/")):
        relative = clean_url[len(static_url.lstrip("/")) :]
        candidate = static_root / relative
        if candidate.exists():
            return candidate

    # Try media root directly
    candidate = media_root / clean_url
    if candidate.exists():
        return candidate

    # Try static root directly
    candidate = static_root / clean_url
    if candidate.exists():
        return candidate

    return None


def _export_local_images_from_body(body, bundle_dir, mode="skip", force=False):
    """Export any local images referenced in img tags in the body HTML."""
    urls = _find_local_img_urls(body)
    for url in urls:
        file_path = _resolve_local_url_to_file(url)
        if file_path is None:
            logger.error("Could not locate file for URL: %s", url)
            continue

        filename = file_path.name
        dest = bundle_dir / filename

        if dest.exists() and mode == "skip":
            continue

        if dest.exists() and mode == "overwrite" and not force:
            dest_mtime = dest.stat().st_mtime
            source_mtime = file_path.stat().st_mtime
            if dest_mtime > source_mtime:
                continue

        bundle_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(file_path), str(dest))


def export_page(instance, content_dir, mode="skip", force=False):
    """Export a single BasePage instance to a Hugo page bundle.

    Args:
        instance: A BasePage subclass instance (HomePage, Page, Section, Article).
        content_dir: Path to the Hugo content directory.
        mode: Export mode - "skip", "overwrite", or "remove".
        force: If True and mode is "overwrite", always overwrite regardless of mtime.
    """
    content_dir = Path(content_dir)
    bundle_dir = _get_bundle_path(instance, content_dir)
    index_filename = _get_index_filename(instance)
    index_path = bundle_dir / index_filename

    if index_path.exists() and mode == "skip":
        return

    if index_path.exists() and mode == "overwrite" and not force:
        dest_mtime = index_path.stat().st_mtime
        if instance.date_modified:
            export_ts = instance.date_modified.timestamp()
            if dest_mtime > export_ts:
                return

    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Build front matter and write the page
    front_matter = _build_front_matter(instance)
    body = instance.body or ""
    page_content = _render_page(instance, front_matter, body)
    index_path.write_text(page_content, encoding="utf-8")

    # Export rich_description if the page has a description
    if instance.description:
        desc_path = bundle_dir / "rich_description.html"
        desc_path.write_text(instance.description, encoding="utf-8")

    # Export share_image
    if instance.share_image:
        filename = _export_media_file(
            instance.share_image, bundle_dir, mode=mode, force=force
        )
        if filename:
            _export_media_metadata(instance.share_image, filename, bundle_dir)

    # Export image collection
    collection_name = _get_image_collection_name(instance)
    if collection_name:
        for rel in getattr(instance, collection_name).select_related("image").all():
            filename = _export_media_file(rel.image, bundle_dir, mode=mode, force=force)
            if filename:
                _export_media_metadata(rel.image, filename, bundle_dir)

    # Export attachments
    if hasattr(instance, "attachment_set"):
        for attachment in instance.attachment_set.all():
            filename = _export_media_file(
                attachment, bundle_dir, mode=mode, force=force
            )
            if filename:
                _export_media_metadata(attachment, filename, bundle_dir)

    # Export local images from body HTML
    _export_local_images_from_body(body, bundle_dir, mode=mode, force=force)


def _export_static_files(site, outdir, mode="skip", force=False):
    """Copy static files from static/$domain/ to the assets directory."""
    static_root = Path(settings.STATIC_ROOT)  # Let it die if not configured
    domain_static = static_root / site.domain
    if not domain_static.exists():
        return

    assets_dir = Path(outdir) / "assets"

    for src_file in domain_static.rglob("*"):
        if src_file.is_dir():
            continue
        relative = src_file.relative_to(domain_static)
        dest = assets_dir / relative

        if dest.exists() and mode == "skip":
            continue

        if dest.exists() and mode == "overwrite" and not force:
            dest_mtime = dest.stat().st_mtime
            src_mtime = src_file.stat().st_mtime
            if dest_mtime > src_mtime:
                continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_file), str(dest))


def export_site(site, outdir, mode="skip", force=False):
    """Export an entire site to a Hugo project directory.

    Args:
        site: The Site instance to export.
        outdir: Path to the Hugo project directory.
        mode: Export mode - "skip", "overwrite", or "remove".
        force: If True and mode is "overwrite", always overwrite regardless of mtime.
    """
    outdir = Path(outdir)

    if mode == "remove" and outdir.exists():
        shutil.rmtree(outdir)

    outdir.mkdir(parents=True, exist_ok=True)
    content_dir = outdir / "content"
    content_dir.mkdir(parents=True, exist_ok=True)

    # Export in breadth-first order by model
    # 1. HomePage: only the current home page
    try:
        homepage = HomePage.objects.live().filter(site=site).latest()
    except HomePage.DoesNotExist:
        homepage = None

    if homepage:
        export_page(homepage, content_dir, mode=mode, force=force)

    # 2. Page: export all
    for page in Page.objects.filter(site=site):
        export_page(page, content_dir, mode=mode, force=force)

    # 3. Section: export all
    for section in Section.objects.filter(site=site):
        export_page(section, content_dir, mode=mode, force=force)

    # 4. Article: export all
    for article in Article.objects.filter(site=site):
        export_page(article, content_dir, mode=mode, force=force)

    # Export static files
    _export_static_files(site, outdir, mode=mode, force=force)
