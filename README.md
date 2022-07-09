# GenericSite: Rapid website prototyping with Django

Django is famous for being a batteries-included web framework for perfectionists
with deadlines. However, bootstrapping a new website using Django still requires
you to write a significant amount of Python code and HTML templates to generate
the basics needed by most every website.

GenericSite is a Django app designed to get you that first 80% of your website
functionality as quickly as possible. It performs the undifferentiated heavy
lifting so you can focus on the 20% of the work that makes your site special.

GenericSite defines a data model based on the
[open graph protocol](https://ogp.me), extended in some places using fields from
[Schema.org](https://schema.org) or other web standards. It provides both
concrete Django models for common web objects, and abstract Django models if
your prefer full customization of your data model.

GenericSite includes a set of templates using the
[Bootstrap CSS framework](https://getbootstrap.com) based on the examples found
on the bootstrap website. The templates work with any objects that implement the
generic data model, or anything that you can map to an opengraph-like model.
They can easily be coupled with Django's generic class-based views to produce a
clean and professional site quickly and easily. If you use the included concrete
models with the default templates and the included views, you'll be starting
with a basic blog-style site.

The templates are built using Bootstrap 5, and they load the core CSS and
JavaScript from a CDN by default, so there's nothing else to install and little
or no front-end to deal with.

## How to use it

### The base template

The GenericSite base template is divided into major blocks that can be replaced
in your child templates. The blocks, in order of appearance, are:

- `opengraph`: Used to expose the page's open graph metadata in the HTML head.
  This is done in the default template. You won't need to override this unless
  you define custom open graph types that need special handling.
- `extra_head`: Override this if you need to include custom CSS, web fonts, etc.
  in the page's HTML head.
- `body_class`: A block you can override to apply a custom class to the HTML
  body element, if needed by your custom CSS.
- `header`: A block to contain your site's masthead and main navigation, the
  header elements common to every page. Override in your site's base template.
- `precontent`: A block that appears before the main content of the page.
  Override this on home pages or section pages where you need to insert some
  feature above the standard content, such as a call to action, introduction to
  the topic, featured stories, etc.
- `content`: The main content body of the page. By default, will `include` the
  content sub-template specified in the template context. For an Article this
  will be the article text, for a Section page this will be the list of Articles
  in the Section.
- `postcontent`: A block that appears after the main content of the page. Often
  used to include "Read Next" or "Related" recirculation modules or a call to
  action.
- `footer`: A block to contain your site's footer links and blanket copyright
  statements, elements common to every page. Override in your site's base
  template.
- `extra_js`: A block just before the closing body tag. Use this to include
  deferred JavaScript or other elements you want loaded after the main page
  content.

### Basic

For each of your models, create a "opengraph" method that returns an object or
dictionary mapping the models attributes to the extended open graph attributes
supported by GenericSite.

### Advanced

Install the optional dependencies to support GenericSite abstract models. Then
create your models to extend the included abstract models.

## What's included

- [ ] `opengraph` templatetag to include opengraph meta tags given a dict (used
      by default in base template)
- [ ] base template: Generic base template with page divided into logical blocks
- [ ] detail_txt: Generic detail page template for text-based content, with
      opengraph metadata
- [ ] detail_img: Generic detail page template featuring a single large image
- [ ] detail_video: Generic detail page template featuring a single large video
- [ ] detail_audio: Generic detail page template featuring an audio player
- [ ] list_blog_txt: Generic list page featuring text-based entries as for a
      blog (bottom 1/3 of the blog example)
- [ ] list_card_imgtop: Generic list page featuring large landscape image cards
      with text beneath (bottom of album example)
- [ ] list_card_imgright: Generic list page featuring cards with text on the
      left and a portrait image to the right (middle 1/3 of blog example)
- [ ] list_big_img: Generic list page featuring a large image beside text
      (bottom 1/3 of carousel example, "featurette")

## How it works

The included generic templates expect to be called from Django's generic views.
Detail templates expect to have a variable called "object" in the context. List
views expect a variable called "object_list".

Each object is expected to have a property or method "opengraph" which will
return an object or dictionary containing opengraph-compatible metadata
(enhanced with some schema.org data in some cases). For each model you wish to
use with generic templates, you just need to create a mapping between the
model's attributes and standard opengraph attributes. This can be done in the
model itself, or it can be done in the view and attached to the model instance
before the template is called.

## Headers and footers

The generic layout includes many header and footer layouts derived from examples
on the Bootstrap website. These are implemented as template includes. Set the
context variables "header_template" and "footer_template" to use them. If those
variables are not found int the context, no header is included, and a generic
copyright notice is included in the footer.

## Open Graph attributes used by the templates

- title
- url
- type
- description
- locale
- site_name
- fb:app_id
- image.alt
- image.url
- image.secure_url
- image.type
- image.width
- image.height
- audio.url
- audio.secure_url
- audio.type
- video.url
- video.secure_url
- video.type
- video.width
- video.height
