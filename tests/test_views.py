from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase

from genericsite.models import Article, HomePage, Section, Site


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
            published_time=timezone.now(),
        )
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, hp.title)


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
            published_time=timezone.now(),
        )
        resp = self.client.get(
            reverse("section_page", kwargs={"section_slug": "test-section"})
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, section.title)


class TestArticleView(TestCase):
    def test_article(self):
        """Article page should contain metadata"""
        site, _ = Site.objects.get_or_create(
            id=1, defaults={"domain": "example.com", "name": "example.com"}
        )
        section = Section.objects.create(
            site=site,
            slug="test-section",
            title="Test Section 1",
            published_time=timezone.now(),
        )
        article = Article.objects.create(
            site=site,
            slug="test-article",
            section=section,
            title="Test Article 1",
            published_time=timezone.now(),
        )
        resp = self.client.get(
            reverse(
                "article_page",
                kwargs={"section_slug": "test-section", "article_slug": "test-article"},
            )
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, article.title)
        self.assertContains(resp, '''property="og:type" content="article"''')


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
