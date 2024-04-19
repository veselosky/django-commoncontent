"""
This module contains common functions and classes that are used across the site. Stored
here to help avoid circular imports.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


# This vocabulary taken from IPTC standards, upon which https://schema.org/creativeWork
# is based.
class Status(models.TextChoices):
    WITHHELD = "withheld", _("Draft (withheld)")
    USABLE = "usable", _("Publish (usable)")
    CANCELLED = "cancelled", _("Unpublish (cancelled)")
