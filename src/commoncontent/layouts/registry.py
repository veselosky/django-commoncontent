# webquills/layouts/registry.py

from commoncontent.layouts.base import Layout


def get_all_layouts():
    return list(Layout.registry.values())


def get_layout_choices():
    return [(layout.identifier, layout.name) for layout in get_all_layouts()]


def get_layout(identifier: str):
    return Layout.registry[identifier]
