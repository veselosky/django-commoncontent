from django.apps import apps
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import get_resolver, get_urlconf
from model_bakery import baker


class SmokeTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(
            username="test_admin",
            password="super-secure",
            is_staff=True,
            is_superuser=True,
        )
        return super().setUpTestData()

    def test_load_pages(self):
        """Load each page we are able to identify proper args for.

        Theory of operation:
        - Iterate over all the installed apps.
        - Enumerate all models in the app.
        - Check if the model has a get_absolute_url method.
        - If the model has a get_absolute_url method, instatiate one and call it.
        - Make a GET request to the URL.
        - Grab the ResovlerMatch object from the response.
        - If the response is 200, test passes. Continue to the next model.
        - If the response is 403, the view is probably marked @login_required.

        """
        # self.client.force_login(self.user)
        # Load a list of all the url patterns in the project.
        url_resolver = get_resolver(get_urlconf())

        # Make a shallow copy of the url patterns so we can pop items.
        self.url_patterns = url_resolver.reverse_dict.copy()

        # Iterate over all the installed apps.
        for app in apps.get_app_configs():
            self._test_app_urls(app)

        # Print out any remaining URL patterns that were not tested.
        for k, v in self.url_patterns.items():
            print(f"{k} = {v}")

    def _test_app_urls(self, app):
        requires_login = []
        for model in app.get_models():
            if not hasattr(model, "get_absolute_url"):
                continue

            with self.subTest(model=model):
                # Create an instance of the model.
                instance = baker.make(model)
                url = instance.get_absolute_url()
                resp = self.client.get(url)
                resolver_match = resp.resolver_match
                if resp.status_code == 200:
                    # url_patterns may contain 2 entries for each URL, one keyed by the URL
                    # name and one keyed by the view func. Pop both if they exist.
                    self.url_patterns.pop(resolver_match.url_name, None)
                    self.url_patterns.pop(resolver_match.func, None)
                elif resp.status_code == 403:
                    requires_login.append(url)
                else:
                    self.fail(
                        f"Failed to load {url} for {model._meta.model_name} with status {resp.status_code}"
                    )
        self.client.force_login(self.user)
        for url in requires_login:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
