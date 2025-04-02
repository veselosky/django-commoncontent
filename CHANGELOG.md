# Changelog for Django-CommonContent

## 0.4.0

- ADDED: This Changelog.
- ADDED: Support for custom User model. Version 0.3 used hard-coded foreign keys to
  Django's built-in `auth.User` model, making this package unsuitable for Django
  projects using a custom AUTH_USER_MODEL (which is very common). Now it works.
- ADDED: Support for a custom Site model (via `django-sitevars`). Version 0.3 used
  hard-coded foreign keys to Django's built-in `sites.Site` model, making this package
  unsuitable for Django projects that do not use `django.contrib.sites` (which is also
  common). You can now use CommonContent without `django.contrib.sites`, or with a
  custom sites framework. Set the SITE_MODEL setting to your custom site model **before
  running migrations**. See
  [django-sitevars](https://github.com/veselosky/django-sitevars) for details.
- CHANGED: Added Django 5.2 (rc1) and Python 3.13 to test matrix.

## 0.3.1

- ADDED: canonical url template tag

## 0.3.0 First public release

- Implements core functionality
