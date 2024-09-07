from commoncontent.models import Menu, SectionMenu
from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.utils.html import format_html, mark_safe

register = template.Library()


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
def copyright_notice(context):
    """Return a copyright notice for the current page."""
    obj = context.get("object")
    request = context.get("request")
    site = get_current_site(request)
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
        holder = site.vars.get_value("copyright_holder", site.name)
        return format_html(
            "© Copyright {} {}. All rights reserved.", copyright_year, holder
        )


@register.simple_tag(takes_context=True)
def menu(context, menu_slug):
    """Looks up a Menu object from the database by slug and stores it in the variable named after 'as'.

    ``{% menu "main-nav" as menu %}``
    """
    request = context.get("request")
    site = get_current_site(request)
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
