# Common Content: A reusable content app for Django

Common Content provides models, views, and templates for common web content in a
reusable Django app. Django ships with `flatpages`, the most simplistic content model
possible. Third party tools like Wagtail or DjangoCMS provide flexible and complex
content management workflows. Common Content is designed to fill the gap between these
options. If you need pages and feeds for your Django site, but don't need the power and
complexity of a full content management system, Common Content may be the right tool.

## Project Status: Alpha

Common Content is still Alpha-level software. It has many completed features that are
usable in production. However, test coverage is not yet complete, the feature set is
still growing, and there are likely to be breaking changes before the software reaches a
stable 1.0 release. Be aware that migrating to newer versions may require some work.

## Included Content Models, Views, and Templates

Common Content defines a data model based on [Schema.org](https://schema.org), extended
in some places using fields from the [open graph protocol](https://ogp.me), or other web
standards. It provides concrete Django models for common web objects, as well as an
abstract CreativeWork and BasePage model for extending the available page types.

Common Content provides the following Content:

- `HomePage` - A dedicated model for site home pages. Sites can have multiple HomePages
  with different publication dates, allowing for scheduled updates.
- Generic `Page` - A model for evergreen pages like "About".
- `Article` - Like a Post in Wordpress, the Article is the main content type of the
  site. Articles can also be linked together in a Series.
- `Section` - Articles are contained in sections. A section is like a category.
- RSS Feeds - Common Content provides a site RSS Feed of published articles, and a
  separate RSS feed for each Section.
- Sitemaps - Common Content also provides Sitemaps for use with Django's sitemap
  framework.
- `Image` - An Image model is provided to house image uploads and their metadata,
  including copyright information. Resized renditions of each image are provided by
  `django-imagekit` (see the section below on Images).
- `Attachment` - A model for storing non-image file uploads and their metadata.
- `Author` - A model to encapsulate author information, including default copyright
  information. Authors are optional. Author pages show a profile and list of authored
  Articles. Each Author also has an RSS Feed.

Common Content provides views and templates (using Bootstrap 5) for each type, along
with a few different options for list display.

In addition to the content pages, Common Content also provides:

- `Menu` and `Link` - These models define a list of links that can be used to implement
  site navigation menus, footer links, etc.
- `SiteVar` - Site variables store bits of information that are reused across the site.
  Things like the default copyright notice, site tagline, analytics IDs, etc. can be
  stored in SiteVars. All variables for a site are injected into every template context
  using the Common Content Context Processor so they are available on every page, even
  pages not provided by Common Content.
- Redirects - Includes the Django redirects app, with a custom middleware to support
  temporary redirects.
- `AbstractCreativeWork` and `BasePage` - These are abstract Django models that you can
  subclass to create new content types that are compatible with Common Content templates
  and tools.
- Admin Support - Common Content provides admin pages for its models, and documentation
  for use by the `admindocs` app.
- `django-tinymce` Support - If `django-tinymce` is installed, Common Content will use
  its WYSISYG editor in its admin pages. There is an optional JSON view that exposes a
  list of recently upload images for use by the TinyMCE editor.

Common Content includes a set of templates using the
[Bootstrap CSS framework](https://getbootstrap.com) based on the examples found on the
bootstrap website. The templates work with any objects that implement the common data
model. They can easily be coupled with Django's generic class-based views to produce a
clean and professional site quickly and easily. If you use the included concrete models
with the default templates and the included views, you'll be starting with a basic
blog-style site.

The templates are built using Bootstrap 5, and they load the core CSS and JavaScript
from a CDN by default, so there's nothing else to install and little or no front-end to
deal with.

## Development

After checking out the code, you can bootstrap a development environment by running:

```sh
python manage.py devsetup
```

Note that the Python used to run this script will be the one used in your virtualenv.

## Installation

Add the following to your `settings.py`:

```python
import commoncontent.apps
INSTALLED_APPS = [
  *commoncontent.apps.CONTENT
  # Optionally use tinymce in the admin
  "tinymce",
  # Other Django apps here
  # ADMIN apps must be added AFTER the Django admin and sites apps
  *commoncontent.apps.ADMIN
]
# Ensure your middleware includes the following:
MIDDLEWARE += [
  "django.contrib.sites.middleware.CurrentSiteMiddleware",
  "commoncontent.redirects.TemporaryRedirectFallbackMiddleware",
]
# If using tinymce
TINYMCE_DEFAULT_CONFIG = commoncontent.apps.TINYMCE_CONFIG

# Add `commoncontent.apps.context_defaults` to your context processors. You will also
# need to add the request, auth, and messages context processors if not already there.
# Probably looks like this:
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "commoncontent.apps.context_defaults",
            ],
        },
    },
]

```

In your project's `urls.py`, insert the Common Content URLs where you want them. To have
Common Content manage your home page and top-level pages, make it the LAST url pattern,
and list it like this:

```python
from commoncontent import views as generic

urlpatterns = [
    # Common Content provides templates for auth pages
    path("accounts/", include("django.contrib.auth.urls")),
    # You need to add the admin yourself:
    path("admin/", admin.site.urls),
    # TinyMCE urls if desired
    path("tinymce/", include("tinymce.urls")),
    # All other urls are handed to Common Content
    path("", include("commoncontent.urls")),
]
```

## Usage

The following documentation should help you use Common Content.

### The base template

The Common Content base template is divided into major blocks that can be replaced in
your child templates. The blocks, in order of appearance, are:

- `title`: The content of the HTML page title tag.
- `bootstrap_styles`: An HTML block that by default pulls in the bootstrap stylesheet.
  You can override it to customize your version of bootstrap (e.g. with BootSwatch) or
  include `{{ block.super }}` and then add some tweaks.
- `opengraph`: Used to expose the page's open graph metadata in the HTML head. This is
  done in the default template. You won't need to override this unless you define custom
  open graph types that need special handling.
- `extra_head`: Override this if you need to include custom CSS, web fonts, etc. in the
  page's HTML head.
- `body_class`: A block you can override to apply a custom class to the HTML body
  element, if needed by your custom CSS.
- `header`: A block to contain your site's masthead and main navigation, the header
  elements common to every page. Override in your site's base template.
- `precontent`: A block that appears before the main content of the page. Override this
  on home pages or section pages where you need to insert some feature above the
  standard content, such as a call to action, introduction to the topic, featured
  stories, etc.
- `content`: The main content body of the page. By default, will `include` the content
  sub-template specified in the template context. For an Article this will be the
  article text, for a Section page this will be the list of Articles in the Section.
- `postcontent`: A block that appears after the main content of the page. Often used to
  include "Read Next" or "Related" recirculation modules or a call to action.
- `footer`: A block to contain your site's footer links and blanket copyright
  statements, elements common to every page. Override in your site's base template.
- `bootstrap_js`: An HTML that by default loads the Bootstrap JS bundle. Override if
  needed.
- `extra_js`: A block just before the closing body tag. Use this to include deferred
  JavaScript or other elements you want loaded after the main page content.

### Block Templates

Genericsite ships with several partial templates that can be included as the content of
the base blocks to construct a page quickly from reusable modules.

TODO: Document available block templates.

### Site Vars

The app comes with a SiteVar model for storing site-specific variables or chunks of
content. You can store any variable for use with your own templates. Variables used by
the default templates/models can be found on the Admin Documentation page for SiteVar.

### Images and Media

Common Content takes advantage of Django Imagekit to manage images. Models are provided
for storing file metadata including copyright information.

Common Content uses presets to produce images in specific sizes as recommended by
[Buffer's Social Media Image Guidelines](https://buffer.com/library/ideal-image-sizes-social-media-posts/).

These named image presets are available:

- small: 160x90
- medium: 400x225
- large: 960x540
- opengraph: 1200x630
- hd720p: 1280x720
- hd1080p: 1920x1080
- portrait_small: 90x160
- portrait_medium: 225x400
- portrait_large: 540x960
- portrait_cover: 1000x1500
- portrait_social: 1080x1350
- portrait_hd: 1080x1920
