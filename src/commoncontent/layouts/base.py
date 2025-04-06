"""
A Layout is an encapsulation of a template and a definition of its context.
"""

from __future__ import annotations


class Layout:
    registry = {}

    identifier: str  # must be overridden
    name: str  # human-readable name
    template_name: str  # template path

    def __init_subclass__(cls, **kwargs):
        """Auto-register all subclasses."""
        super().__init_subclass__(**kwargs)
        if cls.identifier:
            Layout.registry[cls.identifier] = cls

    @classmethod
    def get_context_data(cls, **kwargs):
        """
        Return the context data for the template. Views will process their context
        before passing it to the Layout for further processing, so you can expect the
        kwargs to include `view`, `object`, and `request` keys.
        """
        return kwargs

    @classmethod
    def get_forms(cls):
        """Return a list of Django Form classes."""
        return []

    def get_template_name(self):
        """
        Return the name of the template to be used for rendering. Django will look it up
        in the usual manner.
        """
        if not self.template_name:
            raise NotImplementedError("Layouts must define a template_name.")
        return self.template_name
