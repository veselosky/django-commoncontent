"""
The goal of this command is to import markdown files from Hugo or another static site
generator as Articles.

Since every Article needs a Section, we may also need to create one or more Sections
during the import. We need to provide a way to specify the Section via an argument.

Site is also a required field, so we need to have the site passed as an argument, but
we can default to the value of the SITE_ID setting if the argument is not provided.

Date and description fields in the YAML front matter will be mapped to the
corresponding fields in the Article model. The date fields should be parsed using
``dateutil.parser.parse``.

The title of the Article should be extracted from the YAML front matter. If no title is
provided, the title of the Article should be extracted from the first heading in the
markdown content.

The slug field should be populated from the filename of the markdown file without the
extension.

For now we are ignoring the author field because the format varies between different
SSGs. We can add support for this later if needed.

The command should be able to handle multiple markdown files passed as arguments.

The command should also be able to handle markdown files that do not have YAML front
matter.
"""

import logging
import re
from pathlib import Path

from dateutil.parser import parse
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from mistletoe import Document
from mistletoe.contrib.pygments_renderer import PygmentsRenderer
from yaml import Loader, load

from commoncontent.common import Status
from commoncontent.models import Article, Section

# Define the regular expression pattern for YAML front matter
# This pattern looks for text that starts and ends with triple dashes
# and captures everything in between as the YAML front matter.
# It also captures everything after the second set of triple dashes as content.
# Use the re.DOTALL flag to make the dot match newlines as well
pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)
logger = logging.getLogger(__name__)
Site = apps.get_app_config("sitevars").Site


def extract_title_from_ast(doc):
    """
    Extract the title from the AST of the markdown content.
    The title is assumed to be the first heading in the content.
    """
    for index, node in enumerate(doc.children):
        logger.debug(f"Examining node {node}")
        if node.__class__.__name__ == "Heading":
            logger.debug(f"Found heading node {node}")
            title = node.children[0].content
            # Remove the node from the AST, title is a separate element in the final HTML
            doc.children.pop(index)
            return title
    return ""


class Command(BaseCommand):
    help = "Import markdown files from Hugo or another static site generator."

    def add_arguments(self, parser):
        parser.add_argument(
            "section",
            help="Section to import the markdown files into. Give the title, the slug will be generated.",
        )
        parser.add_argument(
            "--site",
            default=settings.SITE_ID,
            required=False,
            help=(
                "ID or domain of the Site to import the markdown files into. "
                "Defaults to the value of the SITE_ID setting."
            ),
        )
        parser.add_argument(
            "files",
            type=Path,
            nargs="+",
            help="Markdown files to import as Articles. Can be one or more files.",
        )

    def handle(self, *args, **options):
        section_title = options["section"]
        site_id = options["site"]
        files = options["files"]
        now = timezone.now()

        # Determine whether they passed a site id or domain, and load the Site object
        # from the database
        try:
            site_id = int(site_id)
            lookup = {"id": site_id}
        except ValueError:
            lookup = {"domain": site_id}

        try:
            site = Site.objects.get(**lookup)
        except Site.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Site with {lookup} does not exist."))
            return

        # Check if the section exists and create if necessary
        section, created = Section.objects.get_or_create(
            title=section_title,
            site=site,
            defaults={"slug": slugify(section_title), "date_published": now},
        )

        for file in files:
            markdown_content = file.read_text()

            # Extract the YAML front matter and content from the markdown file
            match = re.match(pattern, markdown_content)

            ##################################################################
            # Has YAML front matter. Extract metadata and content from file
            ##################################################################
            if match:
                yaml_front_matter = match.group(1)
                content = match.group(2)

                # Convert the markdown content to AST form
                doc = Document(content)

                # Load the YAML front matter into a dictionary
                metadata = load(yaml_front_matter, Loader=Loader)
                # Hugo only allows certain fields in the front matter, and custom fields
                # are prefixed with "params."
                if "params" in metadata:
                    params = metadata.pop("params")
                    metadata.update(params)

                # Extract the title from the YAML front matter or the first heading
                title = metadata.get("title", None)
                if not title:
                    title = extract_title_from_ast(doc)

                # Extract the publish date from the YAML front matter. Various SSGs use
                # different keys for the date field, so we need to check for multiple
                # keys
                date_keys = ["date", "publishDate", "published", "publishedAt"]
                date = None
                for key in date_keys:
                    if key in metadata:
                        date = parse(metadata[key])
                        break
                if not date:
                    date = now

                # In some cases we also have a modified date
                mod_keys = ["lastmod", "lastModified", "updated", "updatedAt"]
                modified = None
                for key in mod_keys:
                    if key in metadata:
                        modified = parse(metadata[key])
                        break

                # In rare cases there may be an expiry date
                expiry_keys = ["expiryDate", "expires", "expiresAt"]
                expires = None
                for key in expiry_keys:
                    if key in metadata:
                        expires = parse(metadata[key])
                        break

                # Extract the description from the YAML front matter
                description = metadata.get("description", "")

                # Extract the slug from the filename
                slug = file.stem

                # If this is a draft, set the status appropriately
                status = Status.USABLE
                if metadata.get("draft", False):
                    status = Status.WITHHELD

                # Extract tags from the metadata
                tags = metadata.get("tags", [])

                # Produce the HTML content from the AST
                renderer = PygmentsRenderer()
                html_content = renderer.render(doc)

                # Create the Article object
                article = Article.objects.create(
                    title=title,
                    slug=slug,
                    section=section,
                    site=site,
                    status=status,
                    description=description,
                    body=html_content,
                    date_published=date,
                    date_modified=modified,
                    expires=expires,
                )
                if tags:
                    article.tags.add(*tags)

            ##################################################################
            # No YAML front matter. Assume the entire file is content
            ################################################################
            else:
                # Convert the markdown content to AST form
                doc = Document(markdown_content)
                # Extract the title from the first heading
                title = extract_title_from_ast(doc)
                renderer = PygmentsRenderer()
                content = renderer.render(doc)

                # Extract the slug from the filename
                slug = file.stem

                # Create the Article object
                article = Article.objects.create(
                    title=title,
                    slug=slug,
                    section=section,
                    site=site,
                    status=Status.USABLE,
                    body=content,
                    description="",
                    date_published=now,
                )
