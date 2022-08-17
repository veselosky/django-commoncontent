from django import template
from django.contrib.sites.shortcuts import get_current_site

from genericsite.models import Menu, SectionMenu, SiteVar

register = template.Library()


@register.filter(name="add_classes")
def add_classes(value, arg):
    """
    Add provided classes to form field
    :param value: form field
    :param arg: string of classes seperated by ' '
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


@register.simple_tag(takes_context=True)
def sitevar(context, name, default=""):
    site = get_current_site(context["request"])
    return SiteVar.For(site).get_value(name, default)


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
