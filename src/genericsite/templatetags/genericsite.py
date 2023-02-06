from django import template
from django.contrib.sites.shortcuts import get_current_site
from django.utils.html import format_html
from django.utils import timezone

from genericsite.models import Menu, SectionMenu, SiteVar

register = template.Library()


#######################################################################################
# Filters
#######################################################################################


@register.filter(name="add_classes")
def add_classes(value, arg):
    """
    Add provided classes to form field
    :param value: form field
    :param arg: string of classes separated by ' '
    :return: edited field
    https://stackoverflow.com/a/60267589/15428550
    because good programmers steal.
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
    Filter applied only to Page objects (from Paginator). Calls `get_elided_page_range`
    on the paginator, passing the current page number as the first argument, and
    returns the result.

    `{% for num in page_obj|elided_range %}{{num}} {% endfor %}`
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
    path = str(context["request"].path)
    if path == menuitem:
        return 'aria-current="page" '
    elif path.startswith(menuitem):
        return 'aria-current="section" '
    return ""


@register.simple_tag(takes_context=True)
def opengraph_image(context, og):
    "For an Open Graph compatible item, return an open graph image."
    if img := getattr(og, "og_image"):
        return img
    if hasattr(og, "image_set"):
        if img := og.image_set.first():
            return img
    if hasattr(og, "section"):
        if img := og.section.og_image:
            return img
    return None


@register.simple_tag(takes_context=True)
def sitevar(context, name, default=""):
    site = get_current_site(context["request"])
    return SiteVar.For(site).get_value(name, default)
