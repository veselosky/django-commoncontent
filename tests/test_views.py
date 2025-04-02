import json
from datetime import timedelta
from io import BytesIO

from django.apps import apps
from django.core.files.base import ContentFile
from django.http import HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image as PILImage
from sitevars.models import SiteVar

from commoncontent.models import (
    Article,
    ArticleSeries,
    Author,
    HomePage,
    Image,
    Page,
    Section,
    Status,
)
from commoncontent.sitemaps import ArticleSitemap

Site = apps.get_app_config("sitevars").Site


class TestHomePageView(TestCase):
    def test_no_hp_in_db(self):
        """When no HomePages in DB (and DEBUG is True), should show default dev page"""
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "commoncontent/blocks/debug_newsite.html", [t.name for t in resp.templates]
        )

    def test_homepage_exists(self):
        """When one HP exists, it should be used."""
        site, _ = Site.objects.get_or_create(
            id=1, defaults={"domain": "example.com", "name": "example.com"}
        )
        hp = HomePage.objects.create(
            site=site,
            admin_name="Test HomePage",
            title="Test HomePage 1",
            date_published=timezone.now(),
        )
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, hp.title)

    def test_homepage_site_filter(self):
        """HP should always be for current site."""
        site = Site.objects.get_current()
        site2, _ = Site.objects.get_or_create(
            id=2, defaults={"domain": "notmysite.com", "name": "notmysite.com"}
        )
        hp = HomePage.objects.create(
            site=site,
            admin_name="Test HomePage",
            title="Test HomePage 1",
            date_published=timezone.now() - timedelta(days=1),
        )
        HomePage.objects.create(
            site=site2,
            admin_name="NOT MY HomePage",
            title="NOT MY HomePage",
            date_published=timezone.now(),
        )
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, hp.title)

    def test_draft_homepage_skipped(self):
        "HPs not in published status should never be used by the view."
        site = Site.objects.get_current()
        hp = HomePage.objects.create(
            site=site,
            admin_name="Test HomePage",
            title="Test HomePage 1",
            date_published=timezone.now() - timedelta(days=1),
        )
        HomePage.objects.create(
            site=site,
            admin_name="DRAFT HomePage",
            title="DRAFT HomePage 1",
            date_published=timezone.now(),
            status=Status.WITHHELD,
        )
        # Draft is newer and would be selected if not filtering on status.
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, hp.title)

    def test_future_homepage_skipped(self):
        "HPs with pub dates in future should never be used by the view."
        site = Site.objects.get_current()
        hp = HomePage.objects.create(
            site=site,
            admin_name="Test HomePage",
            title="Test HomePage 1",
            date_published=timezone.now() - timedelta(days=1),
        )
        HomePage.objects.create(
            site=site,
            admin_name="FUTURE HomePage",
            title="FUTURE HomePage 1",
            date_published=timezone.now() + timedelta(days=1),
        )
        # HP scheduled for tomorrow should not be selected today
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, hp.title)

    def test_homepage_sorts_articles_by_date_published_descending(self):
        site = Site.objects.get_current()
        section = Section.objects.create(
            site=site,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now(),
        )
        HomePage.objects.create(
            site=site,
            admin_name="Test HomePage",
            title="Test HomePage 1",
            date_published=timezone.now(),
        )
        article1 = Article.objects.create(
            site=site,
            title="Article 1",
            slug="article-1",
            section=section,
            date_published=timezone.now() - timedelta(days=1),
        )
        article2 = Article.objects.create(
            site=site,
            title="Article 2",
            slug="article-2",
            section=section,
            date_published=timezone.now(),
        )
        article3 = Article.objects.create(
            site=site,
            title="Article 3",
            slug="article-3",
            section=section,
            date_published=timezone.now() + timedelta(days=1),
        )

        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, article3.title)
        self.assertContains(resp, article2.title)
        self.assertContains(resp, article1.title)
        self.assertGreater(
            resp.content.find(article1.title.encode()),
            resp.content.find(article2.title.encode()),
        )


class TestPageView(TestCase):
    def test_page_not_found(self):
        resp = self.client.get(
            reverse("landing_page", kwargs={"page_slug": "page-not-created"})
        )
        self.assertIsInstance(resp, HttpResponseNotFound)

    def test_draft_page(self):
        site = Site.objects.get_current()
        Page.objects.create(
            site=site,
            slug="test-page",
            title="Test Page 1",
            date_published=timezone.now(),
            status=Status.WITHHELD,
        )
        resp = self.client.get(
            reverse("landing_page", kwargs={"page_slug": "test-page"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_future_page(self):
        site = Site.objects.get_current()
        Page.objects.create(
            site=site,
            slug="test-page",
            title="Test Page 1",
            date_published=timezone.now() + timedelta(days=1),
        )
        resp = self.client.get(
            reverse("landing_page", kwargs={"page_slug": "test-page"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_page_site_filter(self):
        site2, _ = Site.objects.get_or_create(
            id=2, defaults={"domain": "notmysite.com", "name": "notmysite.com"}
        )
        Page.objects.create(
            site=site2,
            slug="test-page",
            title="Test Page 1",
            date_published=timezone.now(),
        )
        resp = self.client.get(
            reverse("landing_page", kwargs={"page_slug": "test-page"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_page(self):
        site = Site.objects.get_current()
        page = Page.objects.create(
            site=site,
            slug="test-page",
            title="Test Page 1",
            date_published=timezone.now(),
        )
        resp = self.client.get(
            reverse("landing_page", kwargs={"page_slug": "test-page"})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, page.title)


class TestSectionView(TestCase):
    def test_empty_section(self):
        """Sections with no articles should still be visible"""
        site, _ = Site.objects.get_or_create(
            id=1, defaults={"domain": "example.com", "name": "example.com"}
        )
        section = Section.objects.create(
            site=site,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now(),
        )
        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, section.title)

    def test_section_not_found(self):
        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "section-not-created"})
        )
        self.assertIsInstance(resp, HttpResponseNotFound)

    def test_draft_section(self):
        site = Site.objects.get_current()
        Section.objects.create(
            site=site,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now(),
            status=Status.WITHHELD,
        )
        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_future_section(self):
        site = Site.objects.get_current()
        Section.objects.create(
            site=site,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now() + timedelta(days=1),
        )
        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_section_site_filter(self):
        site2, _ = Site.objects.get_or_create(
            id=2, defaults={"domain": "notmysite.com", "name": "notmysite.com"}
        )
        Section.objects.create(
            site=site2,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now(),
        )
        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(resp.status_code, 404)

    def test_section_sorts_articles_by_date_published_descending(self):
        site = Site.objects.get_current()
        section = Section.objects.create(
            site=site,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now(),
        )
        article1 = Article.objects.create(
            site=site,
            section=section,
            title="Article 1",
            slug="article-1",
            date_published=timezone.now() - timedelta(days=1),
        )
        article2 = Article.objects.create(
            site=site,
            section=section,
            title="Article 2",
            slug="article-2",
            date_published=timezone.now(),
        )
        article3 = Article.objects.create(
            site=site,
            section=section,
            title="Article 3",
            slug="article-3",
            date_published=timezone.now() + timedelta(days=1),
        )

        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, article3.title)
        self.assertContains(resp, article2.title)
        self.assertContains(resp, article1.title)
        self.assertGreater(
            resp.content.find(article1.title.encode()),
            resp.content.find(article2.title.encode()),
        )


class BaseContentTestCase(TestCase):
    """A base class that sets up some content for testing"""

    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get_current()
        site2, _ = Site.objects.get_or_create(
            id=2, defaults={"domain": "notmysite.com", "name": "notmysite.com"}
        )
        homepage = HomePage.objects.create(
            site=site,
            title="Test Home Page",
            slug="test-home-page",
            date_published=timezone.now(),
        )
        section = Section.objects.create(
            site=site,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now(),
        )
        section2 = Section.objects.create(
            site=site2,
            slug="test-section",
            title="Test Section 2",
            date_published=timezone.now(),
        )
        article = Article.objects.create(
            site=site,
            slug="test-article",
            section=section,
            title="Test Article 1",
            date_published=timezone.now() - timedelta(days=1),
        )
        article2 = Article.objects.create(
            site=site2,
            slug="test-article",
            section=section2,
            title="Test Article 2",
            date_published=timezone.now(),
        )
        cls.site = site
        cls.site2 = site2
        cls.homepage = homepage
        cls.section = section
        cls.section2 = section2
        cls.article = article
        cls.article2 = article2


class TestArticlesAndFeeds(BaseContentTestCase):
    def test_article(self):
        """Article page should contain metadata."""
        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={"section_slug": "test-section", "article_slug": "test-article"},
            )
        )
        self.assertEqual(resp.status_code, 200)
        # article2 from site2 has same slug, ensure we got the right one
        self.assertContains(resp, self.article.title)
        self.assertContains(resp, '''property="og:type" content="article"''')

    def test_article_draft(self):
        """Draft Article page should not be found."""
        Article.objects.create(
            site=self.site,
            slug="draft-article",
            section=self.section,
            title="DRAFT Article 1",
            date_published=timezone.now(),
            status=Status.WITHHELD,
        )
        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={
                    "section_slug": "test-section",
                    "article_slug": "draft-article",
                },
            )
        )
        self.assertEqual(resp.status_code, 404)

    def test_article_future(self):
        """Future-dated Article page should not be found."""
        Article.objects.create(
            site=self.site,
            slug="future-article",
            section=self.section,
            title="FUTURE Article 1",
            date_published=timezone.now() + timedelta(days=1),
        )
        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={
                    "section_slug": "test-section",
                    "article_slug": "future-article",
                },
            )
        )
        self.assertEqual(resp.status_code, 404)

    def test_article_not_found(self):
        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={
                    "section_slug": "test-section",
                    "article_slug": "article-not-published",
                },
            )
        )
        self.assertIsInstance(resp, HttpResponseNotFound)

    def test_site_rss(self):
        site = Site.objects.get_current()
        site.vars.create(name="tagline", value="Test Tagline")
        resp = self.client.get(reverse("site_feed"))
        self.assertEqual(resp.status_code, 200)

    def test_section_rss(self):
        resp = self.client.get(
            reverse("section_feed", kwargs={"section_slug": self.section.slug})
        )
        self.assertEqual(resp.status_code, 200)

    def test_article_rss_sort_order(self):
        """RSS feed should be in reverse chronological order."""
        article3 = Article.objects.create(
            site=self.site,
            section=self.section,
            title="Test Article 3",
            slug="test-article-3",
            date_published=timezone.now(),
        )
        resp = self.client.get(
            reverse(
                "section_feed",
                kwargs={"section_slug": self.section.slug},
            )
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.article.title)
        self.assertContains(resp, article3.title)
        self.assertGreater(
            resp.content.find(self.article.title.encode()),
            resp.content.find(article3.title.encode()),
        )


class TestViewsGetRightTemplateVars(BaseContentTestCase):
    """Issue #42, ensure views have the correct block variables set."""

    def test_all_blocks_in_context(self):
        config = apps.get_app_config("commoncontent")

        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={"section_slug": "test-section", "article_slug": "test-article"},
            )
        )
        for tpl in config.base_blocks:
            with self.subTest("Check for var in context", block=tpl):
                self.assertIn(tpl, resp.context)

    def test_detail_pages(self):
        config = apps.get_app_config("commoncontent")

        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={"section_slug": "test-section", "article_slug": "test-article"},
            )
        )
        self.assertEqual(
            config.detail_content_template, resp.context["content_template"]
        )
        self.assertEqual(
            config.detail_precontent_template, resp.context["precontent_template"]
        )
        self.assertEqual(
            config.detail_postcontent_template, resp.context["postcontent_template"]
        )

    def test_detail_pages_custom(self):
        site = Site.objects.get_current()
        SiteVar.objects.create(
            site=site,
            name="detail_content_template",
            value="commoncontent/blocks/debug_newsite.html",
        )
        SiteVar.objects.create(
            site=site,
            name="detail_precontent_template",
            value="commoncontent/blocks/debug_newsite.html",
        )
        SiteVar.objects.create(
            site=site,
            name="detail_postcontent_template",
            value="commoncontent/blocks/debug_newsite.html",
        )

        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={"section_slug": "test-section", "article_slug": "test-article"},
            )
        )
        self.assertEqual(
            "commoncontent/blocks/debug_newsite.html", resp.context["content_template"]
        )
        self.assertEqual(
            "commoncontent/blocks/debug_newsite.html",
            resp.context["precontent_template"],
        )
        self.assertEqual(
            "commoncontent/blocks/debug_newsite.html",
            resp.context["postcontent_template"],
        )

    def test_list_pages(self):
        config = apps.get_app_config("commoncontent")

        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(config.list_content_template, resp.context["content_template"])
        self.assertEqual(
            config.list_precontent_template, resp.context["precontent_template"]
        )
        self.assertEqual(
            config.list_postcontent_template, resp.context["postcontent_template"]
        )

    def test_list_pages_custom(self):
        site = Site.objects.get_current()
        SiteVar.objects.create(
            site=site,
            name="list_content_template",
            value="commoncontent/blocks/debug_newsite.html",
        )
        SiteVar.objects.create(
            site=site,
            name="list_precontent_template",
            value="commoncontent/blocks/debug_newsite.html",
        )
        SiteVar.objects.create(
            site=site,
            name="list_postcontent_template",
            value="commoncontent/blocks/debug_newsite.html",
        )

        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(
            "commoncontent/blocks/debug_newsite.html", resp.context["content_template"]
        )
        self.assertEqual(
            "commoncontent/blocks/debug_newsite.html",
            resp.context["precontent_template"],
        )
        self.assertEqual(
            "commoncontent/blocks/debug_newsite.html",
            resp.context["postcontent_template"],
        )


class TestTinyMCEImageListView(TestCase):
    def test_get(self):
        # create an in-memory PILImage to be used as a test image
        img = PILImage.new("RGB", (100, 100))
        # Create a BytesIO object containing the image data
        img_io = BytesIO()
        img.save(
            img_io,
            format="PNG",
        )
        img_io.seek(0)

        Image.objects.create(
            title="test image",
            image_file=ContentFile(img_io.read(), name="test.png"),
            alt_text="test alt",
        )
        resp = self.client.get(reverse("tinymce_image_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/json")
        data = json.loads(resp.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "test image")


class ArticleSeriesViewsTest(BaseContentTestCase):
    def setUp(self):
        self.series = ArticleSeries.objects.create(site_id=1, slug="series_slug")
        self.series_article = Article.objects.create(
            section=self.section,
            series=self.series,
            slug="article_slug",
            site=self.site,
            status=Status.USABLE,
            date_published=timezone.now(),
        )

    def test_redirect_url(self):
        """Test <section>/<series>/ redirects to first article in series."""
        response = self.client.get(
            reverse(
                "series_page",
                kwargs={
                    "section_slug": self.series_article.section.slug,
                    "series_slug": self.series.slug,
                },
            )
        )

        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response.url,
            reverse(
                "article_series_page",
                kwargs={
                    "section_slug": self.series_article.section.slug,
                    "series_slug": self.series.slug,
                    "article_slug": self.series_article.slug,
                },
            ),
        )

    def test_article_with_series_redirect(self):
        """
        Test that a request to "<section_slug>/<article_slug>.html" redirects to
        "<section_slug>/<series_slug>/<article_slug>.html" when the article has a series."""
        response = self.client.get(
            reverse(
                "article_page",
                kwargs={
                    "section_slug": self.series_article.section.slug,
                    "article_slug": self.series_article.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response.url,
            reverse(
                "article_series_page",
                kwargs={
                    "section_slug": self.series_article.section.slug,
                    "series_slug": self.series.slug,
                    "article_slug": self.series_article.slug,
                },
            ),
        )


class TestAuthorViews(TestCase):
    def setUp(self):
        self.author = Author.objects.create(
            name="Test Author", site_id=1, slug="test-author"
        )
        self.section = Section.objects.create(
            site_id=1, slug="section_slug", date_published=timezone.now()
        )
        self.article = Article.objects.create(
            site_id=1,
            section=self.section,
            title="Test Article",
            slug="test-article",
            site=Site.objects.get_current(),
            status=Status.USABLE,
            date_published=timezone.now(),
            author=self.author,
        )

    def test_author_list(self):
        response = self.client.get(reverse("author_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.name)

    def test_author_page(self):
        response = self.client.get(
            reverse("author_page", kwargs={"author_slug": self.author.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.name)

    def test_author_page_paginated(self):
        response = self.client.get(
            reverse(
                "author_page_paginated",
                kwargs={"author_slug": self.author.slug, "page": 1},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.name)

    def test_author_feed(self):
        response = self.client.get(
            reverse("author_feed", kwargs={"author_slug": self.author.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.author.name)


class ArticleSitemapTest(BaseContentTestCase):
    def setUp(self):
        # Note: The base class provides a site, section, article, and article2,
        # with self.article "Test Article 1" belonging to the site and published
        # yesterday. Article2 is from a different site and should not be returned.
        self.article3 = Article.objects.create(
            site=self.site,
            section=self.section,
            title="Test Article 3",
            slug="test-article-3",
            date_published=timezone.now() - timezone.timedelta(days=2),
        )
        self.article4 = Article.objects.create(
            site=self.site,
            section=self.section,
            title="Test Article 4",
            slug="test-article-4",
            date_published=timezone.now() - timezone.timedelta(days=3),
        )
        self.sitemap = ArticleSitemap()
        self.sitemap.site = self.site

    def test_items_order(self):
        items = list(self.sitemap.items())
        self.assertEqual(items, [self.article, self.article3, self.article4])
