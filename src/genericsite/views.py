import typing as T

from django.apps import apps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.generic import DetailView, ListView, TemplateView
from genericsite.models import Article, HomePage, Page, Section


class OpenGraphDetailView(DetailView):
    template_name_field = "base_template"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opengraph"] = self.object.opengraph
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
        if site_default := var.get_value("default_base_template"):
            names.append(site_default)

        # Fall back to Genericsite default
        names.append("genericsite/base.html")

        return names


class ArticleDetailView(OpenGraphDetailView):
    def get_object(self):
        return Article.objects.live().get(
            site=get_current_site(self.request),
            section__slug=self.kwargs["section_slug"],
            slug=self.kwargs["article_slug"],
        )


class PageDetailView(OpenGraphDetailView):
    def get_object(self):
        return Page.objects.live().get(
            site=get_current_site(self.request),
            slug=self.kwargs["page_slug"],
        )


class ArticleList(ListView):
    """View for pages that present a list of articles (e.g. SectionPage, HomePage).

    The `get_object` method is left unimplemented here, as it will be different for
    each subclass. This is an extension of Django's views. In Django's GenericViews,
    List pages don't have an `object`, but in GenericSite, all pages have an `object`.
    """

    model = Article
    paginate_by: int = 15
    paginate_orphans: int = 2
    object = None
    # template_name_suffix = "_list" is supplied by ListView

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        conf = apps.get_app_config("genericsite")
        site = get_current_site(self.request)
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["opengraph"] = self.object.opengraph
        context[
            "content_template"
        ] = self.object.content_template or site.vars.get_value(
            "default_list_content_template", conf.default_list_content_template
        )

        return context

    def get_context_object_name(self, object_list):
        return None

    def get_object(self):
        raise NotImplementedError

    def get_queryset(self):
        site = get_current_site(self.request)
        qs = super().get_queryset().live().filter(site=site)
        if section := self.kwargs.get("section_slug"):
            qs = qs.filter(section__slug=section)
        return qs

    def get_template_names(self):
        names = []
        # Per Django convention, `template_name` on the View takes precedence
        if tname := getattr(self, "template_name"):
            names.append(tname)

        # Django's ListView doesn't account for an object overriding the template,
        # so we need to do that ourselves.
        if self.object.base_template:
            names.append(self.object.base_template)

        # Allow using the Django convention <app>/<model>_list.html
        if hasattr(self.object_list, "model"):
            opts = self.object_list.model._meta
            names.append(
                "%s/%s%s.html"
                % (opts.app_label, opts.model_name, self.template_name_suffix)
            )

        # Fall back to site default if set
        var = self.object.site.vars
        if site_default := var.get_value("default_base_template"):
            names.append(site_default)

        # Fall back to Genericsite default
        names.append("genericsite/base.html")

        return names


class SectionView(ArticleList):
    allow_empty: bool = True
    object = None

    def get_object(self):
        return Section.objects.live().get(
            site=get_current_site(self.request),
            slug=self.kwargs["section_slug"],
        )


class HomePageView(ArticleList):
    allow_empty: bool = True

    def get_object(self):
        try:
            hp = (
                HomePage.objects.live()
                .filter(site=get_current_site(self.request))
                .latest()
            )
        except HomePage.DoesNotExist as e:
            # Create a phony debug home page for bootstrapping.
            hp = HomePage(
                site=get_current_site(self.request),
                admin_name="__DEBUG__",
                title="Generic Site",
                published_time=timezone.now(),
            )
        return hp

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hp = self.object
        if hp.admin_name == "__DEBUG__":
            context["precontent_template"] = "genericsite/blocks/debug_newsite.html"
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "registration/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "allauth" in settings.INSTALLED_APPS:  # use allauth views
            context["change_password_view"] = "account_change_password"
        else:  # use django.contrib.auth views
            context["change_password_view"] = "password_change"

        return context


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


class SiteFeed(Feed):
    "RSS feed of site Article Pages"
    feed_type = ContentFeed

    def get_object(self, request, *args, **kwargs):
        "For site feed, get_object will return the site"
        return request.site

    def title(self, obj):
        tagline = obj.vars.get_value("tagline")
        if tagline:
            return f"{obj.name} -- {obj.tagline}"
        return obj.name

    def link(self, obj):
        return reverse("home_page")

    def description(self, obj):
        page = HomePage.objects.live().filter(site=obj).latest()
        return page.description

    def feed_url(self, obj):
        return reverse("site_feed")

    def author_name(self, obj):
        return obj.vars.get_value("author_display_name")

    def feed_copyright(self, obj):
        page = HomePage.objects.live().filter(site=obj).latest()
        return page.copyright_notice

    def items(self, obj):
        paginate_by = obj.vars.get_value("paginate_by", 15, asa=int)
        return Article.objects.live().filter(site=obj)[:paginate_by]

    def item_title(self, item):
        return item.opengraph.title

    def item_description(self, item):
        return item.opengraph.description

    def item_link(self, item):
        return item.get_absolute_url()

    def item_author_name(self, item):
        return item.author_display_name

    def item_pubdate(self, item):
        return item.published_time

    def item_updateddate(self, item):
        return item.modified_time

    def item_copyright(self, item):
        return item.copyright_notice

    def item_extra_kwargs(self, item):
        return {"content_encoded": self.item_content_encoded(item)}

    def item_content_encoded(self, item):
        return item.excerpt


class SectionFeed(SiteFeed):
    "Feed of Articles in a specified section"

    def get_object(self, request, *args, **kwargs):
        "Return the CategoryPage for this feed"
        return Section.objects.live().get(
            site=request.site, slug=kwargs["section_slug"]
        )

    def title(self, obj):
        return obj.opengraph.title

    def link(self, obj):
        return obj.get_absolute_url()

    def description(self, obj):
        return obj.opengraph.description

    def feed_url(self, obj):
        return reverse("section_feed", kwargs={"section_slug": obj.slug})

    def author_name(self, obj):
        return obj.author_display_name or obj.site.vars.get_value("author_display_name")

    def feed_copyright(self, obj):
        return obj.copyright_notice

    def items(self, obj):
        paginate_by = obj.site.vars.get_value("paginate_by", 15, asa=int)
        return Article.objects.live().filter(section=obj)[:paginate_by]
