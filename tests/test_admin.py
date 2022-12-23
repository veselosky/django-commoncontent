from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AdminSmokeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(
            username="test_admin",
            password="super-secure",
            is_staff=True,
            is_superuser=True,
        )
        return super().setUpTestData()

    def test_load_admin_pages(self):
        """Load each admin change and add page to check syntax in the admin classes."""
        self.client.force_login(self.user)

        views = [
            "admin:genericsite_sitevar_changelist",
            "admin:genericsite_sitevar_add",
            "admin:genericsite_article_changelist",
            "admin:genericsite_article_add",
            "admin:genericsite_section_changelist",
            "admin:genericsite_section_add",
            "admin:genericsite_page_changelist",
            "admin:genericsite_page_add",
            "admin:genericsite_homepage_changelist",
            "admin:genericsite_homepage_add",
            "admin:genericsite_menu_changelist",
            "admin:genericsite_menu_add",
        ]

        for view in views:
            with self.subTest(view=view):
                resp = self.client.get(reverse(view))
                self.assertEqual(resp.status_code, 200)
