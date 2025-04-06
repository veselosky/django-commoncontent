import typing as T

from django.apps import apps
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed
from django.utils.html import escape, strip_tags
from django.views.generic import DetailView, ListView, RedirectView

from commoncontent.models import Article, ArticleSeries, Author, HomePage, Page, Section

sitevars = apps.get_app_config("sitevars")


######################################################################################
class BasePageDetailView(DetailView):
    template_name_field = "base_template"

    def dispatch(self, request, *args, **kwargs):
        self.site = sitevars.get_site_for_request(request)
        self.object = self.get_object()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conf = apps.get_app_config("commoncontent")

        context["opengraph"] = self.object.opengraph

        # Allow passing kwargs in the urlconf to override the default block templates
        for block in conf.base_blocks:
            if tpl := self.kwargs.get(block):
                context[block] = tpl

        if custom_template := getattr(self.object, "content_template", ""):
            context["content_template"] = custom_template
        return context

    def get_context_object_name(self, object):
        return None

    def get_template_names(self):
        # Allow using the Django convention <app>/<model>_detail.html
        # This also takes care of prioritizing an object-specific template
        # thanks to template_name_field.
        names = super().get_template_names()

        # Fall back to site default if set
        var = self.object.site.vars
        if site_default := var.get_value("base_template"):
            names.append(site_default)

        # Fall back to commoncontent default
        names.append("commoncontent/base.html")

        return names


######################################################################################
class ArticleSeriesView(RedirectView):
    """Redirects to the first article in a series."""

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        series = get_object_or_404(
            ArticleSeries.objects.filter(
                site_id=sitevars.get_site_id_for_request(self.request),
                slug=kwargs["series_slug"],
            )
        )
        article = series.article_set.live().first()
        return reverse(
            "article_series_page",
            kwargs={
                "section_slug": article.section.slug,
                "series_slug": article.series.slug,
                "article_slug": article.slug,
            },
        )


######################################################################################
class ArticleDetailView(BasePageDetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Canonical URL for articles in a series includes the series slug
        if self.object.series and (
            "series_slug" not in kwargs
            or kwargs["series_slug"] != self.object.series.slug
        ):
            return redirect(self.object, permanent=True)
        return super().get(request, *args, **kwargs)

    def get_object(self):
        # This lookup ignores the series_slug. Article slugs are still required to be
        # unique within their section, even if in a series
        return get_object_or_404(
            Article.objects.live().filter(
                site=self.site,
                section__slug=self.kwargs["section_slug"],
                slug=self.kwargs["article_slug"],
            )
        )


######################################################################################
class PageDetailView(BasePageDetailView):
    def get_object(self):
        return get_object_or_404(
            Page.objects.live().filter(
                site=self.site,
                slug=self.kwargs["page_slug"],
            )
        )


######################################################################################
class BasePageListView(ListView):
    """View for pages that present a list of articles (e.g. SectionPage, HomePage).

    The `get_object` method is left unimplemented here, as it will be different for
    each subclass. This is an extension of Django's views. In Django's GenericViews,
    List pages don't have an `object`, but in CommonContent, all pages have an `object`.
    """

    object = None
    # template_name_suffix = "_list" is supplied by ListView

    def dispatch(self, request, *args, **kwargs):
        self.site = sitevars.get_site_for_request(request)
        self.object = self.get_object()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        conf = apps.get_app_config("commoncontent")
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["opengraph"] = self.object.opengraph
        if content_template := getattr(self.object, "content_template", None):
            context["content_template"] = content_template

        # Allow passing kwargs in the urlconf to override the default block templates
        for block in conf.base_blocks:
            if tpl := self.kwargs.get(block):
                context[block] = tpl

        return context

    def get_context_object_name(self, object_list):
        return None

    def get_object(self):
        raise NotImplementedError

    def get_paginate_by(self, queryset):
        # If set explicitly on class, return it
        if paginate_by := super().get_paginate_by(queryset):
            return paginate_by
        # Fall back to per-site setting or None
        return self.site.vars.get_value("paginate_by", None, asa=int)

    def get_paginate_orphans(self) -> int:
        # If set explicitly on class, return it
        if orphans := super().get_paginate_orphans():
            return orphans
        # Fall back to per-site setting or 0 (Django's default)
        return self.site.vars.get_value("paginate_orphans", 0, asa=int)

    def get_queryset(self):
        qs = super().get_queryset().live().filter(site=self.site)
        if section := self.kwargs.get("section_slug"):
            qs = qs.filter(section__slug=section)
        return qs

    def get_template_names(self):
        names = []
        # Per Django convention, `template_name` on the View takes precedence
        if tname := getattr(self, "template_name", None):
            names.append(tname)

        # Django's ListView doesn't account for an object overriding the template,
        # so we need to do that ourselves.
        if base_template := getattr(self.object, "base_template", None):
            names.append(base_template)

        # Allow using the Django convention <app>/<model>_list.html
        if hasattr(self.object_list, "model"):
            opts = self.object_list.model._meta
            names.append(
                "%s/%s%s.html"
                % (opts.app_label, opts.model_name, self.template_name_suffix)
            )

        # Fall back to site default if set
        var = self.object.site.vars
        if site_default := var.get_value("base_template"):
            names.append(site_default)

        # Fall back to commoncontent default
        names.append("commoncontent/base.html")

        return names


######################################################################################
class ArticleListView(BasePageListView):
    model = Article

    def get_queryset(self):
        # Because Articles can belong to ArticlesSeries, the default ordering doesn't
        # work as expected, so we must explicitly order by date_published.
        return super().get_queryset().order_by("-date_published")


######################################################################################
class AuthorView(ArticleListView):
    allow_empty: bool = True
    object = None

    def get_context_data(self, **kwargs) -> T.Dict[str, T.Any]:
        context = super().get_context_data(**kwargs)
        context["precontent_template"] = "commoncontent/blocks/author_profile.html"
        return context

    def get_object(self):
        return get_object_or_404(
            Author.objects.filter(
                site=self.site,
                slug=self.kwargs["author_slug"],
            )
        )

    def get_queryset(self):
        return super().get_queryset().filter(author=self.get_object())


######################################################################################
class AuthorListView(ListView):
    model = Author
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.site = sitevars.get_site_for_request(request)
        self.object = self.get_object()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> T.Dict[str, T.Any]:
        context = super().get_context_data(**kwargs)
        context["content_template"] = "commoncontent/blocks/author_list_album.html"
        return context

    def get_object(self):
        site_name = self.site.vars.get_value("brand", self.site.name)
        self.object = Page(
            site=self.site,
            title=f"Contributors to {site_name}",
            description="Authors who have contributed to this site.",
            date_published=timezone.now(),
        )
        return self.object

    def get_template_names(self) -> T.List[str]:
        names = super().get_template_names()

        # Fall back to site default if set
        var = self.object.site.vars
        if site_default := var.get_value("base_template"):
            names.append(site_default)

        # Fall back to commoncontent default
        names.append("commoncontent/base.html")
        return names


######################################################################################
class SectionView(ArticleListView):
    allow_empty: bool = True
    object = None

    def get_object(self):
        return get_object_or_404(
            Section.objects.live().filter(
                site=self.site,
                slug=self.kwargs["section_slug"],
            )
        )


######################################################################################
class HomePageView(ArticleListView):
    allow_empty: bool = True

    def get_object(self):
        try:
            hp = HomePage.objects.live().filter(site=self.site).latest()
        except HomePage.DoesNotExist:
            # Create a phony debug home page for bootstrapping.
            hp = HomePage(
                site=self.site,
                admin_name="__DEBUG__",
                title=self.site.name,
                date_published=timezone.now(),
            )
        return hp

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hp = self.object
        if hp.admin_name == "__DEBUG__":
            context["precontent_template"] = "commoncontent/blocks/debug_newsite.html"
        return context


######################################################################################
# FEEDS AND APIS
######################################################################################
# Custom feeds are not very well documented. This snippet shows how to
# do this: https://djangosnippets.org/snippets/2202/
class ContentFeed(Rss201rev2Feed):
    "Feed generator supporting content:encoded element"

    def root_attributes(self):
        attrs = super().root_attributes()
        attrs["xmlns:content"] = "http://purl.org/rss/1.0/modules/content/"
        return attrs

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        handler.addQuickElement("content:encoded", item["content_encoded"])


######################################################################################
class SiteFeed(Feed):
    "RSS feed of site Article Pages"

    feed_type = ContentFeed

    def get_object(self, request, *args, **kwargs):
        "For site feed, get_object will return the site"
        return sitevars.get_site_for_request(request)

    def title(self, obj):
        tagline = obj.vars.get_value("tagline")
        if tagline:
            return f"{obj.name} -- {tagline}"
        return obj.name

    def link(self, obj):
        return reverse("home_page")

    def description(self, obj):
        page = HomePage.objects.live().filter(site=obj).latest()
        return page.seo_description or escape(strip_tags(page.abstract))

    def feed_url(self, obj):
        return reverse("site_feed")

    def author_name(self, obj):
        return obj.vars.get_value("author_display_name")

    def feed_copyright(self, obj):
        page = HomePage.objects.live().filter(site=obj).latest()
        return page.copyright_notice

    def items(self, obj):
        paginate_by = obj.vars.get_value("paginate_by", 15, asa=int)
        return (
            Article.objects.live()
            .filter(site=obj)
            .order_by("-date_published")[:paginate_by]
        )

    def item_title(self, item):
        return item.opengraph.title

    def item_description(self, item):
        return item.opengraph.description

    def item_link(self, item):
        return item.get_absolute_url()

    def item_author_name(self, item):
        if item.author:
            return item.author.name
        else:
            return item.site.vars.get_value("author_display_name")

    def item_pubdate(self, item):
        return item.date_published

    def item_updateddate(self, item):
        return item.date_modified

    def item_copyright(self, item):
        return item.copyright_notice

    def item_extra_kwargs(self, item):
        return {"content_encoded": self.item_content_encoded(item)}

    def item_content_encoded(self, item):
        return item.excerpt


######################################################################################
class SectionFeed(SiteFeed):
    "Feed of Articles in a specified section"

    def get_object(self, request, *args, **kwargs):
        "Return the CategoryPage for this feed"
        return get_object_or_404(
            Section.objects.live().filter(
                site=sitevars.get_site_for_request(request), slug=kwargs["section_slug"]
            )
        )

    def title(self, obj):
        return obj.title

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.description

    def feed_url(self, obj):
        return reverse("section_feed", kwargs={"section_slug": obj.slug})

    def author_name(self, obj):
        if obj.author:
            return obj.author.name
        else:
            return obj.site.vars.get_value("author_display_name")

    def feed_copyright(self, obj):
        return obj.copyright_notice

    def items(self, obj):
        paginate_by = obj.site.vars.get_value("paginate_by", 15, asa=int)
        return (
            Article.objects.live()
            .filter(section=obj)
            .order_by("-date_published")[:paginate_by]
        )


######################################################################################
class AuthorFeed(SiteFeed):
    "Feed of Articles by a specified author"

    def get_object(self, request, *args, **kwargs):
        "Return the Author for this feed"
        return get_object_or_404(
            Author.objects.filter(site=request.site, slug=kwargs["author_slug"])
        )

    def title(self, obj):
        return obj.name

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.description

    def feed_url(self, obj):
        return reverse("author_feed", kwargs={"author_slug": obj.slug})

    def author_name(self, obj):
        return obj.name

    def feed_copyright(self, obj):
        return obj.copyright_notice

    def items(self, obj):
        paginate_by = obj.site.vars.get_value("paginate_by", 15, asa=int)
        return (
            Article.objects.live()
            .filter(author=obj)
            .order_by("-date_published")[:paginate_by]
        )
