from datetime import datetime
from unittest.mock import Mock

from commoncontent.models import Menu, Page, Status
from django.contrib.sites.models import Site
from django.core.paginator import Paginator
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.test import TestCase as DjangoTestCase
from sitevars.models import SiteVar


class TestAddClassesFilter(SimpleTestCase):
    def test_add_classes_classless(self):
        mock = Mock()
        mock.field.widget.attrs = {}
        Template(
            '{% load commoncontent %}{{ fakefield|add_classes:"newclass" }} '
        ).render(Context({"fakefield": mock}))
        mock.as_widget.assert_called_with(attrs={"class": "newclass"})

    def test_add_classes_append(self):
        mock = Mock()
        mock.field.widget.attrs = {"class": "class1 classB"}
        Template(
            '{% load commoncontent %}{{ fakefield|add_classes:"newclass secondclass" }} '
        ).render(Context({"fakefield": mock}))
        mock.as_widget.assert_called_with(
            attrs={"class": "class1 classB newclass secondclass"}
        )


class TestElidedRangeFilter(SimpleTestCase):
    def test_elided_range_large(self):
        pn = Paginator(object_list="abcdefghijklmnopqrstuvwxyz", per_page=1)
        output = Template(
            "{% load commoncontent %}{% for num in page_obj|elided_range %}{{num}} {% endfor %}"
        ).render(Context({"page_obj": pn.get_page(10)}))
        self.assertEqual(output, "1 2 … 7 8 9 10 11 12 13 … 25 26 ")

    def test_elided_range_medium(self):
        pn = Paginator(object_list="abcdefghijklmnopqrstuvwxyz", per_page=2)
        output = Template(
            "{% load commoncontent %}{% for num in page_obj|elided_range %}{{num}} {% endfor %}"
        ).render(Context({"page_obj": pn.get_page(10)}))
        self.assertEqual(output, "1 2 … 7 8 9 10 11 12 13 ")

    def test_elided_range_small(self):
        pn = Paginator(object_list="abcdefghijklmnopqrstuvwxyz", per_page=3)
        output = Template(
            "{% load commoncontent %}{% for num in page_obj|elided_range %}{{num}} {% endfor %}"
        ).render(Context({"page_obj": pn.get_page(1)}))
        self.assertEqual(output, "1 2 3 4 5 6 7 8 9 ")


@override_settings(SITEVARS_USE_CACHE=False)
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
            date_published=datetime.fromisoformat("2021-11-22T19:00"),
            custom_copyright_notice="{} custom copyright notice",
        )
        output = Template("{% load commoncontent %}{% copyright_notice %} ").render(
            Context({"object": page})
        )
        self.assertIn(page.copyright_notice, output)
        self.assertIn("2021 custom copyright notice", output)

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
        output = Template("{% load commoncontent %}{% copyright_notice %} ").render(
            Context({"request": request, "object": object()})
        )

        self.assertIn(f"{year} sitewide copyright", output)

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
        output = Template("{% load commoncontent %}{% copyright_notice %} ").render(
            Context({"request": request, "object": object()})
        )

        self.assertIn(f"{year} custom holder. All rights", output)

    def test_copyright_notice_site_default(self):
        """Context contains an object that has no copyright_notice prop.
        Site has no copyright SiteVars. Should output the default notice.
        """
        site = Site.objects.get(id=1)
        request = RequestFactory().get("/page.html")
        request.site = site
        year = datetime.now().year
        output = Template("{% load commoncontent %}{% copyright_notice %} ").render(
            Context({"request": request, "object": object()})
        )
        self.assertIn(f"{year} example.com. All rights", output)


class TestMenuTags(DjangoTestCase):
    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.request = RequestFactory().get("/")
        self.request.site = self.site
        self.context = Context({"request": self.request})

    def test_menu_exists(self):
        Menu.objects.create(
            site=self.site, slug="main-nav", admin_name="Main Navigation"
        )
        output = Template(
            '{% load commoncontent %}{% menu "main-nav" as menu %}{{ menu }}'
        ).render(self.context)
        self.assertIn("Main Navigation", output)

    def test_menu_does_not_exist(self):
        output = Template(
            '{% load commoncontent %}{% menu "non-existent" as menu %}{{ menu }}'
        ).render(self.context)
        self.assertEqual(output.strip(), "None")

    def test_menu_main_nav_special_case(self):
        output = Template(
            '{% load commoncontent %}{% menu "main-nav" as menu %}{{ menu }}'
        ).render(self.context)
        self.assertIn("SectionMenu", output)

    def test_menu_active_root_url(self):
        self.request.path = "/"
        output = Template('{% load commoncontent %}{% menu_active "/" %}').render(
            self.context
        )
        self.assertEqual(output.strip(), "active")

    def test_menu_active_subdirectory_url(self):
        self.request.path = "/subdir/"
        output = Template('{% load commoncontent %}{% menu_active "/subdir" %}').render(
            self.context
        )
        self.assertEqual(output.strip(), "active")

    def test_menu_active_non_matching_url(self):
        self.request.path = "/other/"
        output = Template('{% load commoncontent %}{% menu_active "/subdir" %}').render(
            self.context
        )
        self.assertEqual(output.strip(), "")

    def test_menu_aria_current_exact_match(self):
        self.request.path = "/exact/"
        output = Template(
            '{% load commoncontent %}{% menu_aria_current "/exact/" %}'
        ).render(self.context)
        self.assertEqual(output.strip(), 'aria-current="page"')

    def test_menu_aria_current_section_match(self):
        self.request.path = "/section/subsection/"
        output = Template(
            '{% load commoncontent %}{% menu_aria_current "/section/" %}'
        ).render(self.context)
        self.assertEqual(output.strip(), 'aria-current="section"')

    def test_menu_aria_current_no_match(self):
        self.request.path = "/other/"
        output = Template(
            '{% load commoncontent %}{% menu_aria_current "/section/" %}'
        ).render(self.context)
        self.assertEqual(output.strip(), "")
