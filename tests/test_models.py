from datetime import datetime
from unittest import mock

from django.apps import apps
from django.test import TestCase as DjangoTestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from sitevars.models import SiteVar

from commoncontent.common import upload_to
from commoncontent.models import (
    Article,
    ArticleSeries,
    HomePage,
    Link,
    Menu,
    Page,
    Section,
    SectionMenu,
    Status,
)

Site = apps.get_app_config("sitevars").Site


class TestModels(DjangoTestCase):
    def test_copyright_notice_has_custom(self):
        """Page has custom_copyright_notice. Pub year should be interpolated
        into custom notice.
        """
        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
            custom_copyright_notice="{} custom copyright notice",
        )
        self.assertIn("2021 custom copyright notice", page.copyright_notice)

    def test_copyright_notice_site_has_fallback(self):
        """Page has no custom_copyright_notice.
        Site has a SiteVar setting the site-wide copyright notice. Pub year
        should be interpolated into the site-wide notice.
        """
        site = Site.objects.get(id=1)
        SiteVar.objects.create(
            site=site, name="copyright_notice", value="{} sitewide copyright"
        )
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
        )
        self.assertIn("2021 sitewide copyright", page.copyright_notice)

    def test_copyright_notice_site_has_holder(self):
        """Page has no custom_copyright_notice.
        Site has a SiteVar setting the copyright holder. Var copyright_holder
        should be interpolated into the default notice.
        """
        site = Site.objects.get(id=1)
        SiteVar.objects.create(
            site=site, name="copyright_holder", value="custom holder"
        )
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
        )
        self.assertIn("2021 custom holder. All rights", page.copyright_notice)

    def test_copyright_notice_default(self):
        """Page has no custom_copyright_notice.
        Site has no SiteVar copyright settings. Pub year
        should be interpolated into the default notice.
        """
        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
        )
        self.assertIn("2021 example.com. All rights", page.copyright_notice)

    def test_explicit_excerpt(self):
        """Page has a pagebreak marker for excerpt. Should return only content before
        the marker.
        """
        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
            body="""First paragraph.
            <!-- pagebreak --><span id=continue-reading></span>
            Second paragraph.
            """,
        )
        self.assertIn("First paragraph.", page.excerpt)
        self.assertNotIn("Second paragraph.", page.excerpt)

    def test_no_explicit_excerpt(self):
        """Page has no pagebreak marker for excerpt. Should return all content."""
        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
            body="""First paragraph.
            Second paragraph.
            """,
        )
        self.assertIn("First paragraph.", page.excerpt)
        self.assertIn("Second paragraph.", page.excerpt)

    def test_excerpt_truncated(self):
        """If the content is longer that conf.excerpt_max_words, it should be truncated."""
        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
            body="""<p>First paragraph.</p><p>Second paragraph.</p>""",
        )
        expected = """<p>First paragraph.</p><p>Second …</p>"""
        with override_settings(COMMONCONTENT_EXCERPT_MAX_WORDS=3):
            self.assertHTMLEqual(page.excerpt, expected)


def upload_to_target_for_test(instance, filename):
    return "arf.jpg"


class TestUploadTo(DjangoTestCase):
    def test_upload_to_target(self):
        """upload_to function should use the target function if set."""

        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
        )
        with override_settings(COMMONCONTENT_UPLOAD_TO=upload_to_target_for_test):
            self.assertEqual(upload_to(page, "test.jpg"), "arf.jpg")

    def test_upload_to_target_is_string(self):
        """upload_to function should use the target function if set."""
        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
        )
        with override_settings(
            COMMONCONTENT_UPLOAD_TO="tests.test_models.upload_to_target_for_test"
        ):
            self.assertEqual(upload_to(page, "test.jpg"), "arf.jpg")

    def test_upload_to_default(self):
        """upload_to function should use the default path if target not set."""
        site = Site.objects.get(id=1)
        page = Page(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=site,
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
        )
        with mock.patch("commoncontent.common.now") as mock_tz:
            mock_tz.return_value = datetime.fromisoformat("2021-11-22T19:00")
            self.assertEqual(
                upload_to(page, "test.jpg"), "example.com/2021/11/22/test.jpg"
            )


class ArticleModelTest(DjangoTestCase):
    def setUp(self):
        self.section = Section.objects.create(
            site_id=1, slug="section_slug", date_published=timezone.now()
        )
        self.series = ArticleSeries.objects.create(site_id=1, slug="series_slug")
        self.article_with_series = Article.objects.create(
            site_id=1,
            section=self.section,
            series=self.series,
            slug="article-with-series",
            date_published=timezone.now(),
        )
        self.article_without_series = Article.objects.create(
            site_id=1,
            section=self.section,
            slug="article-without-series",
            date_published=timezone.now(),
        )

    def test_get_absolute_url_with_series(self):
        expected_url = reverse(
            "article_series_page",
            kwargs={
                "section_slug": self.section.slug,
                "series_slug": self.series.slug,
                "article_slug": self.article_with_series.slug,
            },
        )
        self.assertEqual(self.article_with_series.get_absolute_url(), expected_url)

    def test_get_absolute_url_without_series(self):
        expected_url = reverse(
            "article_page",
            kwargs={
                "article_slug": self.article_without_series.slug,
                "section_slug": self.section.slug,
            },
        )
        self.assertEqual(self.article_without_series.get_absolute_url(), expected_url)


class TestMenuModel(DjangoTestCase):
    def setUp(self):
        self.site = Site.objects.create(name="Test Site", domain="testsite.com")
        self.menu = Menu.objects.create(
            site=self.site, admin_name="Main Menu", slug="main-menu"
        )

    def test_menu_str(self):
        """Test the string representation of the Menu model."""
        self.assertEqual(str(self.menu), "Main Menu")

    def test_menu_links(self):
        """Test the links property of the Menu model."""
        link1 = Link.objects.create(menu=self.menu, url="/link1", title="Link 1")
        link2 = Link.objects.create(menu=self.menu, url="/link2", title="Link 2")
        self.assertQuerySetEqual(self.menu.links, [link1, link2], ordered=False)


class TestSectionMenu(DjangoTestCase):
    def test_section_menu_links(self):
        """Test the links property when both HomePage and Sections exist."""
        site = Site.objects.get(id=1)
        homepage = HomePage.objects.create(
            site=site, title="Home", slug="home", date_published=timezone.now()
        )
        section1 = Section.objects.create(
            site=site,
            title="Section 1",
            slug="section-1",
            date_published=timezone.now(),
        )
        section2 = Section.objects.create(
            site=site,
            title="Section 2",
            slug="section-2",
            date_published=timezone.now(),
        )
        page1 = Page.objects.create(
            site=site,
            title="Page 1",
            slug="page-1",
            date_published=timezone.now(),
        )
        section_menu = SectionMenu(site=site, pages=[page1])
        self.assertIn(homepage, section_menu.links)
        self.assertIn(section1, section_menu.links)
        self.assertIn(section2, section_menu.links)
        self.assertIn(page1, section_menu.links)

    def test_section_menu_no_homepage(self):
        """Test the links property when no HomePage exists."""
        site = Site.objects.get(id=1)
        section1 = Section.objects.create(
            site=site,
            title="Section 1",
            slug="section-1",
            date_published=timezone.now(),
        )
        section2 = Section.objects.create(
            site=site,
            title="Section 2",
            slug="section-2",
            date_published=timezone.now(),
        )

        section_menu = SectionMenu(site=site)
        self.assertIsInstance(section_menu.links[0], HomePage)
        self.assertEqual(section_menu.links[1], section1)
        self.assertEqual(section_menu.links[2], section2)

    def test_section_menu_no_sections(self):
        """Test the links property when no Sections exist."""
        site = Site.objects.get(id=1)
        homepage = HomePage.objects.create(
            site=site, title="Home", slug="home", date_published=timezone.now()
        )
        section_menu = SectionMenu(site=site)
        self.assertIn(homepage, section_menu.links)
        self.assertEqual(len(section_menu.links), 1)
