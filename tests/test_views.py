from datetime import timedelta

from django.apps import apps
from django.contrib.auth.models import User
from django.http import HttpResponseNotFound
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from genericsite.models import Article, HomePage, Page, Section, Site, SiteVar, Status


class TestHomePageView(TestCase):
    def test_no_hp_in_db(self):
        """When no HomePages in DB (and DEBUG is True), should show default dev page"""
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(
            "genericsite/blocks/debug_newsite.html", [t.name for t in resp.templates]
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
        hp2 = HomePage.objects.create(
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
        hp_draft = HomePage.objects.create(
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
        hp_tomorrow = HomePage.objects.create(
            site=site,
            admin_name="FUTURE HomePage",
            title="FUTURE HomePage 1",
            date_published=timezone.now() + timedelta(days=1),
        )
        # HP scheduled for tomorrow should not be selected today
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, hp.title)


class TestPageView(TestCase):
    def test_page_not_found(self):
        resp = self.client.get(
            reverse("landing_page", kwargs={"page_slug": "page-not-created"})
        )
        self.assertIsInstance(resp, HttpResponseNotFound)

    def test_draft_page(self):
        site = Site.objects.get_current()
        page = Page.objects.create(
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
        page = Page.objects.create(
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
        site = Site.objects.get_current()
        site2, _ = Site.objects.get_or_create(
            id=2, defaults={"domain": "notmysite.com", "name": "notmysite.com"}
        )
        page = Page.objects.create(
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
        section = Section.objects.create(
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
        section = Section.objects.create(
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
        site = Site.objects.get_current()
        site2, _ = Site.objects.get_or_create(
            id=2, defaults={"domain": "notmysite.com", "name": "notmysite.com"}
        )
        section = Section.objects.create(
            site=site2,
            slug="test-section",
            title="Test Section 1",
            date_published=timezone.now(),
        )
        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(resp.status_code, 404)


class TestProfileView(TestCase):
    """User profile view"""

    def test_profile_view(self):
        "profile view"
        self.user = User.objects.create(
            username="test_admin",
            password="super-secure",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

        resp = self.client.get(reverse("account_profile"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("registration/profile.html", [t.name for t in resp.templates])


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
        article = Article.objects.create(
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
        article = Article.objects.create(
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


class TestViewsGetRightTemplateVars(BaseContentTestCase):
    """Issue #42, ensure views have the correct block variables set."""

    def test_all_blocks_in_context(self):
        config = apps.get_app_config("genericsite")

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
        config = apps.get_app_config("genericsite")

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
            value="account/messages/logged_in.txt",
        )
        SiteVar.objects.create(
            site=site,
            name="detail_precontent_template",
            value="account/messages/logged_out.txt",
        )
        SiteVar.objects.create(
            site=site,
            name="detail_postcontent_template",
            value="account/messages/password_set.txt",
        )

        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={"section_slug": "test-section", "article_slug": "test-article"},
            )
        )
        self.assertEqual(
            "account/messages/logged_in.txt", resp.context["content_template"]
        )
        self.assertEqual(
            "account/messages/logged_out.txt", resp.context["precontent_template"]
        )
        self.assertEqual(
            "account/messages/password_set.txt", resp.context["postcontent_template"]
        )

    def test_list_pages(self):
        config = apps.get_app_config("genericsite")

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
            value="account/messages/logged_in.txt",
        )
        SiteVar.objects.create(
            site=site,
            name="list_precontent_template",
            value="account/messages/logged_out.txt",
        )
        SiteVar.objects.create(
            site=site,
            name="list_postcontent_template",
            value="account/messages/password_set.txt",
        )

        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(
            "account/messages/logged_in.txt", resp.context["content_template"]
        )
        self.assertEqual(
            "account/messages/logged_out.txt", resp.context["precontent_template"]
        )
        self.assertEqual(
            "account/messages/password_set.txt", resp.context["postcontent_template"]
        )
