from django.conf import settings
from django.contrib import admin
from imagekit.admin import AdminThumbnail

from commoncontent.models import (
    Article,
    ArticleSeries,
    Author,
    HomePage,
    Image,
    Link,
    Menu,
    Page,
    Section,
)


#######################################################################################
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "site")
    list_filter = ("site",)


#######################################################################################
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    def thumbnail(self, instance):
        if instance.is_portrait:
            return AdminThumbnail(image_field="portrait_small").__call__(instance)
        return AdminThumbnail(image_field="small").__call__(instance)

    readonly_fields = ("width", "height", "mime_type", "thumbnail")
    fields = (
        "title",
        "thumbnail",
        "image_file",
        "site",
        "alt_text",
        "tags",
        "description",
        "custom_copyright_holder",
        "custom_copyright_notice",
        "date_created",
        "date_published",
        "width",
        "height",
        "mime_type",
    )


#######################################################################################
class CreativeWorkAdmin(admin.ModelAdmin):
    rich_text_fields = ("description", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "date_published"
    list_display = ("title", "date_published", "site", "status")
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
                    "date_published",
                    "description",
                    "share_image",
                    "author",
                    "body",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "date_modified",
                    "expires",
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
                "fields": ("locale", "custom_icon", "custom_copyright_notice"),
            },
        ),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if (
            "tinymce" in settings.INSTALLED_APPS
            and db_field.name in self.rich_text_fields
        ):
            from tinymce.widgets import TinyMCE

            from commoncontent.apps import TINYMCE_CONFIG

            return db_field.formfield(
                widget=TinyMCE(
                    attrs={"cols": 90, "rows": 40},
                    mce_attrs=TINYMCE_CONFIG,
                )
            )
        return super().formfield_for_dbfield(db_field, **kwargs)


#######################################################################################
@admin.register(Article)
class ArticleAdmin(CreativeWorkAdmin):
    list_display = ("title", "section", "date_published", "site", "status")
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
                    "series",
                    "status",
                    "date_published",
                    "description",
                    "share_image",
                    "author",
                    "tags",
                    "body",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "date_modified",
                    "expires",
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
                "fields": ("locale", "custom_icon", "custom_copyright_notice"),
            },
        ),
    )


#######################################################################################
@admin.register(ArticleSeries)
class ArticleSeriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


#######################################################################################
@admin.register(Section)
class SectionAdmin(CreativeWorkAdmin):
    pass


#######################################################################################
@admin.register(Page)
class PageAdmin(CreativeWorkAdmin):
    pass


#######################################################################################
@admin.register(HomePage)
class HomePageAdmin(CreativeWorkAdmin):
    prepopulated_fields = {"slug": ("admin_name",)}
    list_display = ("admin_name", "date_published", "site", "status")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "admin_name",
                    "slug",
                    "title",
                    "description",
                    "share_image",
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
                    "date_published",
                    "date_modified",
                    "expires",
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
                "fields": ("locale", "custom_icon", "custom_copyright_notice"),
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
