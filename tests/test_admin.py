from django.apps import apps
from django.contrib.admin import site
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

        app_label = "commoncontent"
        commoncontent = apps.get_app_config(app_label)
        for model in commoncontent.get_models():
            if not site.is_registered(model):
                continue

            with self.subTest(model=model):
                changelist_url = reverse(
                    f"admin:{app_label}_{model._meta.model_name}_changelist"
                )
                add_url = reverse(f"admin:{app_label}_{model._meta.model_name}_add")
                resp_changelist = self.client.get(changelist_url)
                resp_add = self.client.get(add_url)
                self.assertEqual(resp_changelist.status_code, 200)
                self.assertEqual(resp_add.status_code, 200)
