from datetime import datetime
from unittest import mock

from django.test import TestCase as DjangoTestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from genericsite.common import upload_to
from genericsite.models import (
    Article,
    ArticleSeries,
    Page,
    Section,
    Site,
    SiteVar,
    Status,
)


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
        assert "2021 custom copyright notice" in page.copyright_notice

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
        assert f"2021 sitewide copyright" in page.copyright_notice

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
        assert f"2021 custom holder. All rights" in page.copyright_notice

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
        assert f"2021 example.com. All rights" in page.copyright_notice

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
        assert f"First paragraph." in page.excerpt
        assert f"Second paragraph." not in page.excerpt

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
        assert f"First paragraph." in page.excerpt
        assert f"Second paragraph." in page.excerpt


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
        with override_settings(GENERICSITE_UPLOAD_TO=upload_to_target_for_test):
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
            GENERICSITE_UPLOAD_TO="tests.test_models.upload_to_target_for_test"
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
        with mock.patch("genericsite.common.now") as mock_tz:
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
