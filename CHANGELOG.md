# Changelog for Django-CommonContent

## 0.4.0

- BREAKING CHANGE: A through-model has been added to `Article.image_set`. This operation
  requires dropping and recreating the field, which **will result in data loss**. If you
  are migrating from an earlier version, you will need to create a custom script to back
  up and restore your image relations. (This applies only to the ManyToMany `image_set`,
  the `share_image` Foreign Key is not affected.)
- ADDED: `image_set` ManyToMany fields have been added to all subclasses of
  `AbstractCreativeWork` using a through-model to store relationship information,
  including ordering. This should allow you to present a page as a Slideshow or Image
  Gallery using a custom template (no such template is provided in this release, sorry).
- ADDED: `attachment_set` ManyToMany fields have been added to all subclasses of
  `AbstractCreativeWork`.
- ADDED: A new `WebContent` abstract base model has been inserted into the inheritance
  chain as a peer to `MediaObject`. This should make it easier to add models that are
  not pages but contain HTML content. It has no effect otherwise.
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
