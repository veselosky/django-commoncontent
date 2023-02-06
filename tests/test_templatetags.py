from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock

from django.core.paginator import Paginator
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase as DjangoTestCase

from genericsite.models import Page, Site, SiteVar, Status


class TestAddClassesFilter(SimpleTestCase):
    def test_add_classes_classless(self):
        mock = Mock()
        mock.field.widget.attrs = {}
        output = Template(
            '{% load genericsite %}{{ fakefield|add_classes:"newclass" }} '
        ).render(Context({"fakefield": mock}))
        print(output)
        assert mock.as_widget.called_with({"class": "newclass"})

    def test_add_classes_append(self):
        mock = Mock()
        mock.field.widget.attrs = {"class": "class1 classB"}
        output = Template(
            '{% load genericsite %}{{ fakefield|add_classes:"newclass secondclass" }} '
        ).render(Context({"fakefield": mock}))
        print(output)
        assert mock.as_widget.called_with(
            {"class": "class1 classB newclass secondclass"}
        )


class TestElidedRangeFilter(SimpleTestCase):
    def test_elided_range_large(self):
        pn = Paginator(object_list="abcdefghijklmnopqrstuvwxyz", per_page=1)
        output = Template(
            "{% load genericsite %}{% for num in page_obj|elided_range %}{{num}} {% endfor %}"
        ).render(Context({"page_obj": pn.get_page(10)}))
        self.assertEqual(output, "1 2 … 7 8 9 10 11 12 13 … 25 26 ")

    def test_elided_range_medium(self):
        pn = Paginator(object_list="abcdefghijklmnopqrstuvwxyz", per_page=2)
        output = Template(
            "{% load genericsite %}{% for num in page_obj|elided_range %}{{num}} {% endfor %}"
        ).render(Context({"page_obj": pn.get_page(10)}))
        self.assertEqual(output, "1 2 … 7 8 9 10 11 12 13 ")

    def test_elided_range_small(self):
        pn = Paginator(object_list="abcdefghijklmnopqrstuvwxyz", per_page=3)
        output = Template(
            "{% load genericsite %}{% for num in page_obj|elided_range %}{{num}} {% endfor %}"
        ).render(Context({"page_obj": pn.get_page(1)}))
        self.assertEqual(output, "1 2 3 4 5 6 7 8 9 ")


class TestCopyrightNoticeTag(DjangoTestCase):
    def test_copyright_notice_obj_has_custom(self):
        """Context contains an 'object' that has a copyright_notice method.
        Should return the value of object.copyright_notice.
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
        output = Template("{% load genericsite %}{% copyright_notice %} ").render(
            Context({"object": page})
        )
        print(output)
        assert page.copyright_notice in output
        assert "2021 custom copyright notice" in output

    def test_copyright_notice_site_has_fallback(self):
        """Context contains an object that has no copyright_notice prop.
        Site has a SiteVar setting the site-wide copyright notice. Current year
        should be interpolated into the site-wide notice.
        """
        site = Site.objects.get(id=1)
        SiteVar.objects.create(
            site=site, name="copyright_notice", value="{} sitewide copyright"
        )
        request = RequestFactory().get("/page.html")
        request.site = site
        year = datetime.now().year
        output = Template("{% load genericsite %}{% copyright_notice %} ").render(
            Context({"request": request, "object": object()})
        )
        print(output)
        assert f"{year} sitewide copyright" in output

    def test_copyright_notice_site_has_holder(self):
        """Context contains an object that has no copyright_notice prop.
        Site has a SiteVar setting the copyright holder. Var copyright_holder
        should be interpolated into the default notice.
        """
        site = Site.objects.get(id=1)
        SiteVar.objects.create(
            site=site, name="copyright_holder", value="custom holder"
        )
        request = RequestFactory().get("/page.html")
        request.site = site
        year = datetime.now().year
        output = Template("{% load genericsite %}{% copyright_notice %} ").render(
            Context({"request": request, "object": object()})
        )
        print(output)
        assert f"{year} custom holder. All rights" in output

    def test_copyright_notice_site_default(self):
        """Context contains an object that has no copyright_notice prop.
        Site has no copyright SiteVars. Should output the default notice.
        """
        site = Site.objects.get(id=1)
        request = RequestFactory().get("/page.html")
        request.site = site
        year = datetime.now().year
        output = Template("{% load genericsite %}{% copyright_notice %} ").render(
            Context({"request": request, "object": object()})
        )
        print(output)
        assert f"{year} example.com. All rights" in output
