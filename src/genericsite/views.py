import typing as T

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from genericsite.models import Article, HomePage, Page, Section, SiteVar


def supply_context_defaults(
    site, context, viewtype: T.Literal["detail", "list"] = "detail"
):
    "Mutate and return the context, adding common defaults to the context."
    var = SiteVar.For(site)
    context["header_template"] = var.get_value(
        "default_header_template", "genericsite/blocks/header_simple.html"
    )
    context["footer_template"] = var.get_value(
        "default_footer_template", "genericsite/blocks/footer_simple.html"
    )
    context["precontent_template"] = var.get_value(
        "default_precontent_template", "genericsite/blocks/empty.html"
    )
    context["postcontent_template"] = var.get_value(
        "default_postcontent_template", "genericsite/blocks/empty.html"
    )
    # The content block is a little more complicated
    tpl_var = f"default_{viewtype}_content_template"
    default = "genericsite/blocks/article_text.html"
    if viewtype == "list":
        default = "genericsite/blocks/article_list_blog.html"
    context["content_template"] = var.get_value(tpl_var, default)

    return context


class OpenGraphDetailView(DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = supply_context_defaults(self.object.site, context)
        context["opengraph"] = self.object.opengraph
        if custom_template := getattr(self.object, "content_template", ""):
            context["content_template"] = custom_template
        return context

    def get_context_object_name(self, object):
        return ""

    def get_template_names(self):
        var = SiteVar.For(self.object.site)
        return getattr(self.object, "base_template", "") or var.get_value(
            "default_base_template", "genericsite/base.html"
        )


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
    model = Article
    paginate_by: int = 10
    paginate_orphans: int = 2
    object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = supply_context_defaults(self.object.site, context, viewtype="list")
        context["object"] = self.object
        context["opengraph"] = self.object.opengraph
        if custom_template := getattr(self.object, "content_template", ""):
            context["content_template"] = custom_template
        return context

    def get_context_object_name(self, object_list):
        return ""

    def get_object(self):
        raise NotImplementedError

    def get_queryset(self):
        site = get_current_site(self.request)
        qs = super().get_queryset().live().filter(site=site)
        if section := self.kwargs.get("section_slug"):
            qs = qs.filter(section__slug=section)
        return qs

    def get_template_names(self):
        var = SiteVar.For(self.object.site)
        return getattr(self.object, "base_template", "") or var.get_value(
            "default_base_template", "genericsite/base.html"
        )


class SectionView(ArticleList):
    allow_empty: bool = False
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
            if settings.DEBUG:
                # Create a phony debug home page for bootstrapping.
                hp = HomePage(
                    site=get_current_site(self.request),
                    admin_name="__DEBUG__",
                    title="Generic Site",
                    published_time=timezone.now(),
                )
            else:
                raise e
        return hp

    def get_context_data(self, **kwargs):
        site = get_current_site(self.request)
        context = super().get_context_data(**kwargs)
        context = supply_context_defaults(self.object.site, context, viewtype="list")
        hp = self.get_object()
        context["object"] = hp
        if hp.admin_name == "__DEBUG__":
            context["precontent_template"] = "genericsite/blocks/debug_newsite.html"
        return context


class ProfileView(LoginRequiredMixin ,TemplateView):
    template_name = "registration/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "allauth" in settings.INSTALLED_APPS:  # use allauth views
            context["change_password_view"] = "account_change_password"
        else:  # use django.contrib.auth views
            context["change_password_view"] = "password_change"

        return context
