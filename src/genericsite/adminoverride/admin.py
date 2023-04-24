from django.contrib import admin
from django.contrib.sites.models import Site

from genericsite.models import SiteVar

#######################################################################################
# Override the default Site admin so we can add sitevars as an inline. This has to be
# in a separate app that's listed BELOW admin in INSTALLED_APPS. If we register ours
# first, Django will crash when admin tries to register theirs. We let them go first,
# then unregister theirs to replace it with ours.
#######################################################################################

# Note: this could raise admin.NotRegistered, but if it does, that means contrib.sites
# is not installed, which is a problem anyway, so we don't catch it.
admin.sites.site.unregister(Site)


class SiteVarInline(admin.TabularInline):
    extra: int = 1
    model = SiteVar


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("domain", "name")
    search_fields = ("domain", "name")
    inlines = [SiteVarInline]
