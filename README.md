# Common Content: A reusable content app for Django

Common Content provides models, views, and templates for common web content in a
reusable Django app, giving you a blog-like web site out of the box.

Django ships with `flatpages`, the most simplistic content model possible. Third party
tools like [Wagtail](https://wagtail.org/) or [DjangoCMS](https://www.django-cms.org/)
provide flexible and complex content management workflows, but require a lot of custom
code. Common Content is designed to fill the gap between these options. If you need
pages and feeds for your Django site, but don't need (or want) the power and complexity
of a full content management system, Common Content may be the right tool.

Common Content includes a set of templates using the
[Bootstrap CSS framework](https://getbootstrap.com) based on the examples found on the
bootstrap website. The templates work with any objects that implement the common data
model. They can easily be coupled with Django's generic class-based views to produce a
clean and professional site quickly and easily. If you use the included concrete models
with the default templates and the included views, you'll be starting with a basic
blog-style site.

## Project Status: Alpha

Common Content is still Alpha-level software. It has many completed features that are
usable in production. However, test coverage is not yet complete, the feature set is
still growing, and there are likely to be breaking changes before the software reaches a
stable 1.0 release. Be aware that migrating to newer versions may require some work.

**BREAKING CHANGE in 0.4.0:** A through-model has been added to `Article.image_set`.
This operation requires dropping and recreating the field, which **will result in data
loss**. If you are migrating from an earlier version, you will need to create a custom
script to back up and restore your image relations. (This applies only to the ManyToMany
`image_set`, the `share_image` Foreign Key is not affected.)

## Custom User and Site models

Common Content now supports
[custom AUTH_USER_MODEL (via Django)](https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#substituting-a-custom-user-model)
as well as a
[custom SITE_MODEL (via django-sitevars)](https://github.com/veselosky/django-sitevars?tab=readme-ov-file#using-with-an-alternate-site-model).
Follow the links for documentation on setting them up for your project.

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
with a few different options for list display. The templates include Open Graph metadata
and Schema.org metadata for social sharing and SEO. The templates load the Bootstrap CSS
and JavaScript from a CDN by default, so there's nothing else to install and little or
no front-end to deal with (but you can override this in your own templates, see the
`bootstrap_styles` block below).

In addition to the content pages, Common Content also provides:

- `Menu` and `Link` - These models define a list of links that can be used to implement
  site navigation menus, footer links, etc.
- Redirects - Includes the Django redirects app, with a custom middleware to support
  temporary redirects.
- `AbstractCreativeWork` and `BasePage` - These are abstract Django models that you can
  subclass to create new content types that are compatible with Common Content templates
  and tools.
- Admin Support - Common Content provides admin pages for its models, and documentation
  for use by the `admindocs` app.
- `django-sitevars` - Site variables store bits of information that are reused across
  the site. Things like the default copyright notice, site tagline, analytics IDs, etc.
  can be stored in SiteVars. All variables for a site are injected into every template
  context using the SiteVars Context Processor so they are available on every page, even
  pages not provided by Common Content.
- `django-tinymce` Support - If `django-tinymce` is installed, Common Content will use
  its WYSISYG editor in its admin pages. There is an optional JSON view that exposes a
  list of recently upload images for use by the TinyMCE editor.

## Development

This project uses [uv from Astral](https://docs.astral.sh/uv/) for managing development.
Install uv before working with this repo.

After checking out the code, you can bootstrap a development environment by running:

```bash
uv sync
uv run ./manage.py migrate
```

## Installation

Add the following to your `settings.py`:

```python
import commoncontent.apps
INSTALLED_APPS = [
  *commoncontent.apps.CONTENT,  # commoncontent, django_bootstrap_icons, imagekit, taggit
  # Optionally use tinymce in the admin
  "tinymce",
  # Other Django apps here
  "django.contrib.sites",  # Optional
  # sitevars must come AFTER contrib.sites for admin to work
  "sitevars", # Required
]

# Ensure your middleware includes the following:
MIDDLEWARE += [
  # If using django.contrib.sites:
  "django.contrib.sites.middleware.CurrentSiteMiddleware",
  # If using django.contrib.redirects:
  "commoncontent.redirects.TemporaryRedirectFallbackMiddleware",
]

# If using tinymce
TINYMCE_DEFAULT_CONFIG = commoncontent.apps.TINYMCE_CONFIG

# Add `commoncontent.apps.context_defaults` to your context processors. You will also
# need to add the request, auth, and messages context processors if not already there.
# The inject_sitevars processor should come after context_defaults so you can override
# the default values using sitevars.
# Probably looks like this:

TEMPLATES = [
  { "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {
      "context_processors": [
        "django.template.context_processors.request",  # Required
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        # These are both required for commoncontent templates to work properly:
        "commoncontent.apps.context_defaults",
        "sitevars.context_processors.inject_sitevars",
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
  # You need to add the admin yourself. Remember to add the docs!
  path('admin/doc/', include('django.contrib.admindocs.urls')),
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
- `schema`: Holds the schema.org metadata.
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
- `bootstrap_js`: Loads the Bootstrap JS bundle. Override if needed.
- `extra_js`: A block just before the closing body tag. Use this to include deferred
  JavaScript or other elements you want loaded after the main page content.

### Block Templates

Common Content ships with several partial templates that can be included as the content
of the base blocks to construct a page quickly from reusable modules. These can be
loaded from the `commoncontent/blocks/` template directory.

NOTE: Although the Common Content base template is an excellent starter, these block
templates are very basic. This is an area for future expansion. For now, they are
usable, but you probably will want to build your own.

The available block templates are:

- `article_list_album.html`: Displays Articles' image, title, and description as an
  array of cards. Useful for Section pages and home pages.
- `article_list_blog.html`: Displays Articles' title and excerpt in a news feed style,
  like an old-school blog home page.
- `article_text.html`: Displays the title, featured image, and full text of an Article.
  Used on the Article detail page.
- `author_list_album.html`: Displays a profile image and short bio for each author. Used
  on the Author list page.
- `author_profile.html`: Displays the author profile photo and full bio. Used on the
  Author detail page.
- `empty.html`: An empty template to leave a block empty.
- `footer_simple.html`: A very simple footer.
- `header_simple.html`: A very simple header.

### Site Vars

We depend on [django-sitevars](https://pypi.org/project/django-sitevars/) for storing
site-specific variables or chunks of content. You can also store any variable for use
with your own templates. Variable can be injected into template contexts using the
context processor in `sitevars.context_processors.inject_sitevars`, or using the
`{% sitevar "name" %}` template tag. Variables used by the default templates/models are
listed below. Defaults for these variables are injected in the template contexts by
`commoncontent.apps.context_defaults`.

- `base_template` - The base template to use for generic pages. Defaults to
  `commoncontent/base.html`.
- `brand` - Site's brand name. Uses `site.name` if not set.
- `copyright_holder` - Custom name for the copyright holder if using the default
  copyright notice. Falls back to `site.name` if not provided.
- `copyright_notice` - Text to include in the copyright notice section of the footer
  (replaces the default copyright notice).
- `custom_stylesheet` - A site-specific CSS file. This is pulled into the `extra_head`
  block after bootstrap and Common Content's CSS, so you can use it to override default
  styles and customize the look and feel of each site. It is included using
  `{% static custom_stylesheet %}` so the value should be relative to the STATIC_ROOT.
- `default_icon` - Name of a Bootstrap icon to use by default if the object provides
  none.
- `detail_precontent_template` - Default template to use for the `precontent` block for
  detail pages.
- `detail_content_template` - Default template to use for the `content` block for detail
  pages.
- `detail_postcontent_template` - Default template to use for the `postcontent` block
  for detail pages.
- `footer_template` - Default template to use for the `footer` block.
- `header_template` - Default template to use for the `header` block.
- `list_postcontent_template` - Default template to use for the `postcontent` block for
  list pages.
- `list_precontent_template` - Default template to use for the `precontent` block for
  list pages.
- `list_content_template` - Default template to use for the `content` block for list
  pages.
- `paginate_by` - Items per page on list pages, same as Django's ListView, see
  [pagination](https://docs.djangoproject.com/en/dev/ref/paginator/) in the Django docs.
- `paginate_orphans` - Same as Django's ListView, see
  [pagination](https://docs.djangoproject.com/en/dev/ref/paginator/) in the Django docs.

### Images and Media

Common Content takes advantage of
[django-imagekit](https://pypi.org/project/django-imagekit/) to manage images. Models
are provided for storing file metadata including copyright information.

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
