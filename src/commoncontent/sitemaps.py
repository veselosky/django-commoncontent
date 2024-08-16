from django.apps import apps
from django.contrib.sitemaps import Sitemap

from commoncontent.models import Article, Author, HomePage, Page, Section

conf = apps.get_app_config("commoncontent")


class SiteAwareSiteMap(Sitemap):
    site = None
    model = None

    def get_urls(self, site=None, **kwargs):
        self.site = site
        return super().get_urls(site=site, **kwargs)

    def items(self):
        return self.model.objects.live().filter(site=self.site)

    def lastmod(self, obj):
        return obj.date_modified


class ArticleSitemap(SiteAwareSiteMap):
    changefreq = conf.sitemap_changefreq
    priority = 0.5
    model = Article

    def items(self):
        return super().items().order_by("-date_published")


class AuthorSitemap(SiteAwareSiteMap):
    changefreq = "weekly"
    priority = 0.5
    model = Author

    def items(self):
        return self.model.objects.filter(site=self.site)


class PageSitemap(SiteAwareSiteMap):
    changefreq = "weekly"
    priority = 0.5
    model = Page


class SectionSitemap(SiteAwareSiteMap):
    changefreq = "weekly"
    priority = 0.5
    model = Section


class HomePageSitemap(SiteAwareSiteMap):
    changefreq = "weekly"
    priority = 0.5
    model = HomePage

    def items(self):
        return [HomePage.objects.live().filter(site=self.site).latest()]


sitemaps = {
    "articles": ArticleSitemap,
    "authors": AuthorSitemap,
    "pages": PageSitemap,
    "sections": SectionSitemap,
    "home": HomePageSitemap,
}
