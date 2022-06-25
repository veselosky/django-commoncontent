# GenericSite: Rapid website prototyping with Django

Django is famous for being a batteries-included web framework. But there's one
battery that Django doesn't include: a default set of website templates.

GenericSite is a Django app that provides a set of basic templates designed to
work with Django's generic views to produce a decent-looking website with
minimal effort. When you just need to publish some information and don't really
care about the visual design, you can use GenericSite to produce a site that
looks clean and professional without having to hire a designer or hand code new
templates.

The templates are built using Bootstrap 5, and they load the core CSS and
JavaScript from a CDN by default, so there's nothing else to install and little
or no front-end to deal with. Just use Django's generic views, set your view's
template to one included with GenericSite, and you have the basics. GenericSite
can also handle more complex sites with just a little glue code added to your
view or model.

For completeness, GenericSite also includes some abstract models that implement
the basic, generic web page elements. Your models can inherit one or more of
these to quickly bootstrap your model layer.
