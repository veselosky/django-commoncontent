"""
This module contains common functions and classes that are used across the site. Stored
here to help avoid circular imports.
"""

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


# This vocabulary taken from IPTC standards, upon which https://schema.org/creativeWork
# is based.
class Status(models.TextChoices):
    WITHHELD = "withheld", _("Draft (withheld)")
    USABLE = "usable", _("Publish (usable)")
    CANCELLED = "cancelled", _("Unpublish (cancelled)")


def upload_to(instance, filename):
    """Generate a path for uploaded files."""
    target = getattr(settings, "COMMONCONTENT_UPLOAD_TO", None)
    if target:
        if isinstance(target, str):
            target = import_string(target)
        return target(instance, filename)
    when = now()
    return f"{instance.site.domain}/{when.year}/{when.month}/{when.day}/{filename}"
