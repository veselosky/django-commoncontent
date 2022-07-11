from django.contrib import admin

from genericsite.models import Article, HomePage, Page, Section


class OpenGraphAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    date_heirarchy = "published_time"
    search_fields = ("title", "description")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "og_image",
                    "body",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "site",
                    "status",
                    "published_time",
                    "modified_time",
                    "expiration_time",
                    "seo_title",
                    "seo_description",
                    "content_template",
                    "base_template",
                )
            },
        ),
        (
            "Additional metadata",
            {
                "classes": ("collapse",),
                "fields": ("type", "locale", "custom_icon", "custom_copyright_notice"),
            },
        ),
    )

    list_display = ("title", "published_time", "site", "status")
    list_filter = ("site", "status")


@admin.register(Article)
class ArticleAdmin(OpenGraphAdmin):
    list_display = ("title", "section", "published_time", "site", "status")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "section",
                    "author_display_name",
                    "author_profile_url",
                    "description",
                    "og_image",
                    "tags",
                    "body",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "site",
                    "status",
                    "published_time",
                    "modified_time",
                    "expiration_time",
                    "seo_title",
                    "seo_description",
                    "content_template",
                    "base_template",
                )
            },
        ),
        (
            "Additional metadata",
            {
                "classes": ("collapse",),
                "fields": ("type", "locale", "custom_icon", "custom_copyright_notice"),
            },
        ),
    )


@admin.register(Section)
class SectionAdmin(OpenGraphAdmin):
    pass


@admin.register(Page)
class PageAdmin(OpenGraphAdmin):
    pass


@admin.register(HomePage)
class HomePageAdmin(OpenGraphAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "admin_name",
                    "title",
                    "slug",
                    "description",
                    "og_image",
                    "body",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "site",
                    "status",
                    "published_time",
                    "modified_time",
                    "expiration_time",
                    "seo_title",
                    "seo_description",
                    "content_template",
                    "base_template",
                )
            },
        ),
        (
            "Additional metadata",
            {
                "classes": ("collapse",),
                "fields": ("type", "locale", "custom_icon", "custom_copyright_notice"),
            },
        ),
    )


list_display = ("admin_name", "published_time", "site", "status")
