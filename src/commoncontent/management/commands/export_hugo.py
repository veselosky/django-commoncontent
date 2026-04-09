"""
Management command to export a site to a directory in a format suitable for Hugo.

Usage:
    python manage.py export_hugo <site> <outdir> [options]

The site argument can be a site ID or domain name. The outdir is the top-level
Hugo project directory where content will be written.

Export modes:
    --skip (default): Do not overwrite existing files.
    --overwrite: Update files, but skip if the existing file is newer.
    --remove: Delete the output directory and recreate from scratch.
    --force: When used with --overwrite, always overwrite regardless of mtime.
"""

import logging

from django.apps import apps
from django.core.management.base import BaseCommand

from commoncontent.actions import export_site

logger = logging.getLogger(__name__)
Site = apps.get_app_config("sitevars").Site


class Command(BaseCommand):
    help = "Export a site to a directory in Hugo format."

    def add_arguments(self, parser):
        parser.add_argument(
            "site",
            help="Site to export, by ID or domain name.",
        )
        parser.add_argument(
            "outdir",
            help="Output directory (Hugo project root). Will be created if needed.",
        )
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            "--skip",
            action="store_const",
            const="skip",
            dest="mode",
            help="Skip existing files (default).",
        )
        mode_group.add_argument(
            "--overwrite",
            action="store_const",
            const="overwrite",
            dest="mode",
            help="Overwrite existing files (skip if existing is newer).",
        )
        mode_group.add_argument(
            "--remove",
            action="store_const",
            const="remove",
            dest="mode",
            help="Remove and recreate the output directory. Requires confirmation.",
        )
        parser.set_defaults(mode="skip")
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Force overwrite regardless of modification time (use with --overwrite).",
        )

    def handle(self, *args, **options):
        site_id = options["site"]
        outdir = options["outdir"]
        mode = options["mode"]
        force = options["force"]

        # Resolve site
        try:
            site_id_int = int(site_id)
            lookup = {"id": site_id_int}
        except ValueError:
            lookup = {"domain": site_id}

        try:
            site = Site.objects.get(**lookup)
        except Site.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Site with {lookup} does not exist."))
            return

        # Confirm remove mode
        if mode == "remove":
            confirm = input(
                f"WARNING: This will delete all files in '{outdir}' and recreate. "
                "Are you sure? [y/N] "
            )
            if confirm.lower() != "y":
                self.stderr.write("Export cancelled.")
                return

        self.stdout.write(f"Exporting site '{site.domain}' to '{outdir}' (mode={mode})...")
        export_site(site, outdir, mode=mode, force=force)
        self.stdout.write(self.style.SUCCESS("Export complete."))
