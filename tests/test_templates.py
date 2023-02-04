from pathlib import Path
from unittest import TestCase

from django.template import loader


class TestTemplateSyntax(TestCase):
    def _load_templates_for_glob(self, glob: str):
        project_dir = Path(__file__).parent.parent
        templates_dir = project_dir / "src" / "genericsite" / "templates"
        for tpl_file in templates_dir.glob(glob):
            tpl_path = tpl_file.relative_to(templates_dir)
            with self.subTest(template=tpl_path):
                # should NOT raise TemplateSyntaxError
                template = loader.get_template(tpl_path)

    def test_template_syntax_html(self):
        return self._load_templates_for_glob("**/*.html")

    def test_template_syntax_txt(self):
        return self._load_templates_for_glob("**/*.txt")
