from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock

from django.template import Context, Template
from django.test import RequestFactory, TestCase as DjangoTestCase

from genericsite.models import Page, Site, SiteVar, Status


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
            published_time=datetime.fromisoformat("2021-11-22T19:00"),
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
            published_time=datetime.fromisoformat("2021-11-22T19:00"),
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
            published_time=datetime.fromisoformat("2021-11-22T19:00"),
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
            published_time=datetime.fromisoformat("2021-11-22T19:00"),
        )
        assert f"2021 example.com. All rights" in page.copyright_notice
