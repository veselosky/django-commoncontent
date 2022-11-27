from pathlib import Path
from unittest import TestCase

from django.template import loader


class TestTemplateSyntax(TestCase):
    def test_template_syntax_html(self):
        project_dir = Path(__file__).parent.parent
        templates_dir = project_dir / "src" / "genericsite" / "templates"
        for tpl_file in templates_dir.glob("**/*.html"):
            tpl_path = tpl_file.relative_to(templates_dir)
            with self.subTest(template=tpl_path):
                # should NOT raise TemplateSyntaxError
                template = loader.get_template(tpl_path)

    def test_template_syntax_txt(self):
        project_dir = Path(__file__).parent.parent
        templates_dir = project_dir / "src" / "genericsite" / "templates"
        for tpl_file in templates_dir.glob("**/*.txt"):
            tpl_path = tpl_file.relative_to(templates_dir)
            with self.subTest(template=tpl_path):
                # should NOT raise TemplateSyntaxError
                template = loader.get_template(tpl_path)
