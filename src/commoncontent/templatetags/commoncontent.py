import re

from django import template
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from django.utils.html import format_html, mark_safe

from commoncontent.models import Menu, SectionMenu

register = template.Library()
sitevars = apps.get_app_config("sitevars")
Site = sitevars.Site


#######################################################################################
# Filters
#######################################################################################
@register.filter(name="add_classes")
def add_classes(value, arg):
    """
    Add provided classes to form field
    https://stackoverflow.com/a/60267589/15428550
    because good programmers steal.

    ``{{ form.username|add_classes:"form-control" }}``
    """
    css_classes = value.field.widget.attrs.get("class", "")
    # check if class is set or empty and split its content to list (or init list)
    if css_classes:
        css_classes = css_classes.split(" ")
    else:
        css_classes = []
    # prepare new classes to list
    args = arg.split(" ")
    for a in args:
        if a not in css_classes:
            css_classes.append(a)
    # join back to single string
    return value.as_widget(attrs={"class": " ".join(css_classes)})


@register.filter
def elided_range(value):
    """
    Filter applied only to Page objects (from Paginator). Calls ``get_elided_page_range``
    on the paginator, passing the current page number as the first argument, and
    returns the result.

    ``{% for num in page_obj|elided_range %}{{num}} {% endfor %}``

    1 2 … 7 8 9 10 11 12 13 … 19 20
    """
    page_obj = value
    return page_obj.paginator.get_elided_page_range(page_obj.number)


#######################################################################################
# Tags
#######################################################################################
@register.simple_tag(takes_context=True)
def canonical_url_link(context, include_query=None):
    """Return a rel=canonical link tag for the current page.

    Note: This tag is called by default in the ``base.html`` template inside a block
    named "canonical_url". Override that block in your template to customize.

    The generated URL does not include the query string by default. If you want to
    include the query string, pass ``include_query=True``. If a view wants to specify
    that the query string should be included, it can set a ``query_is_canonical``
    attribute on the view to True (but you can override this by passing
    ``include_query=False``).

    If ``SECURE_SSL_REDIRECT`` is True, the canonical URL will use 'https', unless the
    current path matches one of the regular expressions in ``SECURE_REDIRECT_EXEMPT``.

    If your site supports both http and https, you can set ``CANONICAL_USE_HTTPS=True``
    in your settings.py (or set a SiteVar of the same name) to force the canonical URL
    to use 'https'. Otherwise, it will use 'http'.

    If your site displays the same content at more than one path, you can specify a
    ``canonical_path`` in the context to override the current path. But you really should
    avoid doing this, it's bad for SEO.
    """
    # https://moz.com/learn/seo/canonicalization
    # https://support.google.com/webmasters/answer/139066?hl=en
    # https://www.searchenginejournal.com/seo-101/canonical-urls/
    # https://developers.google.com/search/docs/advanced/crawling/consolidate-duplicate-urls
    # https://developers.google.com/search/docs/advanced/crawling/rel-canonical

    request = context.get("request")
    site = sitevars.get_site_for_request(request)

    # Calculating canonical URL is not as straightforward as it seems. A naive approach
    # would be to use request.build_absolute_uri(request.path), but that doesn't take
    # into account several factors.
    # `request.scheme` will return the scheme of the current request, unless
    # SECURE_SSL_REDIRECT==True, in which case it will always return 'https'.
    # This is not necessarily accurate for the canonical URL. If it's False, we may
    # still want to use 'https' for the canonical URL. Even if it's true, paths in the
    # SECURE_REDIRECT_EXEMPT list will not be redirected to 'https', and that's not
    # accounted for (as of Django 5.1). (And redirects won't happen if
    # SecurityMiddleware is not installed, but that is probably an error.)
    scheme = "http"
    force_https = getattr(
        settings, "CANONICAL_USE_HTTPS", False
    ) or site.vars.get_value("CANONICAL_USE_HTTPS", asa=bool)

    # See also SecurityMiddleware
    redirect_exempt = [re.compile(r) for r in settings.SECURE_REDIRECT_EXEMPT]
    if force_https and not settings.SECURE_SSL_REDIRECT:
        scheme = "https"
    elif settings.SECURE_SSL_REDIRECT and not any(
        pattern.search(request.path) for pattern in redirect_exempt
    ):
        scheme = "https"

    # Note that Django uses SECURE_SSL_HOST to specify a different domain for HTTPS
    # requests. However, if that host is canonical, we should have been redirected
    # there by the security middleware, so get_host() should be correct.
    domain = request.get_host()

    # In some cases, we want to include query parameters in the canonical URL. In
    # other cases we do not. Users can specify which by passing the include_query
    # argument to the template tag. If they don't, the view itself can specify
    # a query_is_canonical attribute to say which behavior is correct for this view.
    if include_query is None:
        view = context.get("view")
        # To simplify class based views, you can just set query_is_canonical on the
        # class itself, rather than bending over backwards to set it on the function.
        if view:
            if hasattr(view, "view_class") and hasattr(
                view.view_class, "query_is_canonical"
            ):
                include_query = view.view_class.query_is_canonical
            else:
                include_query = getattr(view, "query_is_canonical", False)

    query = ""
    if include_query:
        query = request.META.get("QUERY_STRING")
        if query:
            query = "?" + query

    # Finally, if the project has mapped multiple paths to the same view and wants one
    # of them to be canonical, it can specify a canonical_path in the context. But
    # don't do this. Seriously, it's a bad idea.
    canonical_path = context.get("canonical_path", request.path)
    return format_html(
        '<link rel="canonical" href="{}://{}{}{}" />',
        scheme,
        domain,
        canonical_path,
        query,
    )


@register.simple_tag(takes_context=True)
def copyright_notice(context):
    """Return a copyright notice for the current page."""
    obj = context.get("object")
    request = context.get("request")
    site = sitevars.get_site_for_request(request)
    notice = ""
    # First we check if the "object" (for detail views) knows its own copyright.
    if obj and hasattr(obj, "copyright_year"):
        copyright_year = obj.copyright_year
    else:
        copyright_year = timezone.now().year

    if obj and hasattr(obj, "copyright_notice"):
        notice = obj.copyright_notice
    if notice:
        return format_html(notice, copyright_year)

    # Otherwise, we fall back to the site's copyright. Is one explicitly set?
    if notice := site.vars.get_value("copyright_notice"):
        return format_html(notice, copyright_year)
    else:
        holder = site.vars.get_value("copyright_holder", getattr(site, "name", ""))
        return format_html(
            "© Copyright {} {}. All rights reserved.", copyright_year, holder
        )


@register.simple_tag(takes_context=True)
def menu(context, menu_slug):
    """Looks up a Menu object from the database by slug and stores it in the variable named after 'as'.

    ``{% menu "main-nav" as menu %}``
    """
    request = context.get("request")
    site = sitevars.get_site_for_request(request)
    menu = None
    try:
        menu = Menu.objects.get(site=site, slug=menu_slug)
    except Menu.DoesNotExist:
        # Special case for the magic slug "main-nav"
        if menu_slug == "main-nav":
            menu = SectionMenu(site)
    return menu


@register.simple_tag(takes_context=True)
def menu_active(context, menuitem: str):
    """Returns 'active' if the current URL is "under" the given URL.

    Used to style menu links to mark the current section.

    ``<a href="{{ url }}" class="nav-link {% menu_active url %}" {% menu_aria_current url %}>``
    """
    path = str(context["request"].path)
    # Special case because every url starts with /
    if menuitem == "/":
        if path == "/":
            return "active"
        return ""
    # Otherwise, if the page is under the menupage's directory, it is active
    if path.startswith(menuitem):
        return "active"
    return ""


@register.simple_tag(takes_context=True)
def menu_aria_current(context, menuitem: str):
    """Adds ``aria-current="page"`` if the current URL is "under" the given URL.

    Used to style menu links to mark the current section.

    ``<a href="{{ url }}" class="nav-link {% menu_active url %}" {% menu_aria_current url %}>``
    """
    path = str(context["request"].path)
    if path == menuitem:
        return mark_safe('aria-current="page" ')
    elif path.startswith(menuitem):
        return mark_safe('aria-current="section" ')
    return ""


@register.simple_tag(takes_context=True)
def opengraph_image(context, og):
    """For an Open Graph compatible item, return an Image instance suitable to
    represent the item in a visual context.

    ``{% opengraph_image article as img %}``
    """
    if img := getattr(og, "share_image", None):
        return img
    if hasattr(og, "image_set"):
        if img := og.image_set.first():
            return img
    if hasattr(og, "section"):
        if img := og.section.share_image:
            return img
    return None
