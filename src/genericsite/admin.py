from django.contrib import admin

from genericsite.models import (
    Article,
    ArticleImage,
    HomePage,
    Page,
    Section,
    SiteVar,
    Link,
    Menu,
)


class ArticleImageInline(admin.StackedInline):
    extra: int = 1
    model = ArticleImage


@admin.register(SiteVar)
class SiteVarAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "site")
    list_filter = ("site",)


class OpenGraphAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    date_heirarchy = "published_time"
    list_display = ("title", "published_time", "site", "status")
    list_filter = ("site", "status")
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


@admin.register(Article)
class ArticleAdmin(OpenGraphAdmin):
    list_display = ("title", "section", "published_time", "site", "status")
    inlines = [ArticleImageInline]
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
    prepopulated_fields = {"slug": ("admin_name",)}
    list_display = ("admin_name", "published_time", "site", "status")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "admin_name",
                    "slug",
                    "title",
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


class LinkInline(admin.StackedInline):
    extra: int = 1
    model = Link


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    exclude = ["links"]
    inlines = [LinkInline]
    prepopulated_fields = {"slug": ("admin_name",)}
