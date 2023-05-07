from unittest import TestCase

from django.core.paginator import Paginator
from django.template import loader


class TestPaginationTemplate(TestCase):
    "Test various outputs of the pagination template."

    @classmethod
    def setUpClass(cls):
        cls.pager = loader.get_template("genericsite/includes/pagination.html")
        cls.object_list = "abcdefghijklmnopqrstuvwxyz"

    def test_no_other_pages(self):
        "When only one page, should render as empty"
        pn = Paginator(self.object_list, per_page=50)
        output = self.pager.render({"paginator": pn, "page_obj": pn.get_page(1)})
        self.assertEqual(output.strip(), "")

    def test_no_previous(self):
        "When no previous page, should render first and previous as disabled (not links)"
        pn = Paginator(self.object_list, per_page=7)
        output = self.pager.render({"paginator": pn, "page_obj": pn.get_page(1)})
        # Current page should be marked active and aria-current, and not a link
        self.assertIn(
            '<li class="page-item active" aria-current="page"><span class="page-link">1</span></li>',
            output,
        )
        # Previous should be a span, not a link
        self.assertIn(
            """<span class="page-link"><span aria-hidden="true">&lt;</span> Previous </span>""",
            output,
        )
        # First should be a span, not a link
        self.assertIn(
            """<span class="page-link"><span aria-hidden="true">&laquo;</span> First </span>""",
            output,
        )
        # Next should be a link to page 2
        self.assertIn(
            """<a class="page-link" rel="next" href="?page=2"> Next <span aria-hidden="true">&gt;</span></a>""",
            output,
        )
        # Last should be a link to page 4
        self.assertIn(
            """<a class="page-link" href="?page=4"> Last <span aria-hidden="true">&raquo;</span></a>""",
            output,
        )

    def test_no_next(self):
        "When no previous page, should render first and previous as disabled (not links)"
        pn = Paginator(self.object_list, per_page=7)
        output = self.pager.render({"paginator": pn, "page_obj": pn.get_page(4)})
        # Current page should be marked active and aria-current, and not a link
        self.assertIn(
            '<li class="page-item active" aria-current="page"><span class="page-link">4</span></li>',
            output,
        )
        # First should be a link to page 1
        self.assertIn(
            """<a class="page-link" href="?page=1"><span aria-hidden="true">&laquo;</span> First </a>""",
            output,
        )
        # Previous should be a link to page 3
        self.assertIn(
            """<a class="page-link" rel="prev" href="?page=3"><span aria-hidden="true">&lt;</span> Previous </a>""",
            output,
        )
        # Next should be a span, not a link
        self.assertIn(
            """<span class="page-link"> Next <span aria-hidden="true">&gt;</span></span>""",
            output,
        )
        # Last should be a span, not a link
        self.assertIn(
            """<span class="page-link"> Last <span aria-hidden="true">&raquo;</span></span>""",
            output,
        )

    def test_many_pages(self):
        "When no previous page, should render first and previous as disabled (not links)"
        pn = Paginator(self.object_list, per_page=1)
        output = self.pager.render({"paginator": pn, "page_obj": pn.get_page(13)})
        # Current page should be marked active and aria-current, and not a link
        self.assertIn(
            '<li class="page-item active" aria-current="page"><span class="page-link">13</span></li>',
            output,
        )
        # First should be a link to page 1
        self.assertIn(
            """<a class="page-link" href="?page=1"><span aria-hidden="true">&laquo;</span> First </a>""",
            output,
        )
        # Previous should be a link to page 12
        self.assertIn(
            """<a class="page-link" rel="prev" href="?page=12"><span aria-hidden="true">&lt;</span> Previous </a>""",
            output,
        )
        # Next should be a link to page 14
        self.assertIn(
            """<a class="page-link" rel="next" href="?page=14"> Next <span aria-hidden="true">&gt;</span></a>""",
            output,
        )
        # Last should be a link to page 26
        self.assertIn(
            """<a class="page-link" href="?page=26"> Last <span aria-hidden="true">&raquo;</span></a>""",
            output,
        )
        # Some pages should have been elided from the link list
        self.assertIn(
            '<li class="page-item disabled"><span class="page-link">…</span></li>',
            output,
        )
