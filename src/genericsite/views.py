import typing as T

from django.apps import apps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
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


class OpenGraphListView(ListView):
    """View for pages that present a list of articles (e.g. SectionPage, HomePage).

    The `get_object` method is left unimplemented here, as it will be different for
    each subclass. This is an extension of Django's views. In Django's GenericViews,
    List pages don't have an `object`, but in GenericSite, all pages have an `object`.
    """

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

    def get_paginate_by(self, queryset):
        # If set explicitly on class, return it
        if paginate_by := super().get_paginate_by(queryset):
            return paginate_by
        # Fall back to per-site setting or None
        return self.request.site.vars.get_value("paginate_by")

    def get_paginate_orphans(self) -> int:
        # If set explicitly on class, return it
        if orphans := super().get_paginate_orphans():
            return orphans
        # Fall back to per-site setting or 0 (Django's default)
        return self.request.site.vars.get_value("paginate_orphans", 0)

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


class ArticleListView(OpenGraphListView):
    model = Article


class SectionView(ArticleListView):
    allow_empty: bool = True
    object = None

    def get_object(self):
        return Section.objects.live().get(
            site=get_current_site(self.request),
            slug=self.kwargs["section_slug"],
        )


class HomePageView(ArticleListView):
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
