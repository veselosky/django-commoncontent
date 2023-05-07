from django.contrib import admin
from easy_thumbnails.fields import ThumbnailerImageField
from easy_thumbnails.widgets import ImageClearableFileInput

from genericsite.models import (
    Article,
    HomePage,
    Image,
    Link,
    Menu,
    Page,
    Section,
    SiteVar,
)


#######################################################################################
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    formfield_overrides = {
        ThumbnailerImageField: {"widget": ImageClearableFileInput},
    }
    readonly_fields = ("image_width", "image_height", "mime_type")
    fields = (
        "title",
        "image_file",
        "site",
        "alt_text",
        "tags",
        "description",
        "copyright_holder",
        "custom_copyright_notice",
        "created_dt",
        "image_width",
        "image_height",
        "mime_type",
    )


#######################################################################################
@admin.register(SiteVar)
class SiteVarAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "site")
    list_filter = ("site",)


#######################################################################################
class OpenGraphAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_time"
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
                    "site",
                    "status",
                    "published_time",
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


#######################################################################################
@admin.register(Article)
class ArticleAdmin(OpenGraphAdmin):
    list_display = ("title", "section", "published_time", "site", "status")
    list_filter = ("section", "site", "status")
    raw_id_fields = ["image_set"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "site",
                    "section",
                    "status",
                    "published_time",
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


#######################################################################################
@admin.register(Section)
class SectionAdmin(OpenGraphAdmin):
    pass


#######################################################################################
@admin.register(Page)
class PageAdmin(OpenGraphAdmin):
    pass


#######################################################################################
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


#######################################################################################
class LinkInline(admin.StackedInline):
    extra: int = 1
    model = Link


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    exclude = ["links"]
    inlines = [LinkInline]
    prepopulated_fields = {"slug": ("admin_name",)}
