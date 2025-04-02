from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from commoncontent.models import Article, Section

base_path = Path(__file__).resolve().parent
Site = apps.get_app_config("sitevars").Site


class TestImportMarkdownCommand(TestCase):
    def test_markdown_with_frontmatter(self):
        # Call the command
        call_command(
            "import_markdown",
            "Test Section",
            str(base_path / "test_import_markdown_with_frontmatter.md"),
            site=1,
        )

        article = Article.objects.first()

        # Assertions
        self.assertEqual(Section.objects.count(), 1)
        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(Site.objects.count(), 1)

        # Title should come from front matter
        self.assertEqual(article.title, "Test Article with Front Matter")
        # Slug should come from file name
        self.assertEqual(article.slug, "test_import_markdown_with_frontmatter")
        self.assertEqual(
            article.description, "A markdown file with front matter for testing."
        )
        # Section should have been generated
        self.assertEqual(article.section.title, "Test Section")
        # Tags should be extracted from front matter
        self.assertListEqual(
            sorted(list(article.tags.names())),
            [
                "bash",
                "cli",
                "linux",
                "shell",
            ],
        )
        # Content should be extracted from markdown
        expected = """
        <h2>What is this "shell"?</h2>
        <p>The "shell" is another name for the command shell or command interpreter. This is the
        program that gives you a command prompt, accepts the commands you type there, and
        basically makes the computer do what you tell it to. In DOS the program that did this
        was command.com (unless you were a real technogeek and used
        <a href="http://en.wikipedia.org/wiki/4DOS">4dos</a> or something). In Linux, the shell is the
        first program that starts when you log in, and it keeps running until you log out,
        waiting to do your bidding. Linux is able to use any of several different shells, but
        the default Linux shell is called bash and is the only one I will discuss.</p>
        """
        self.assertHTMLEqual(article.body, expected)

    def test_markdown_without_frontmatter(self):
        # Call the command
        call_command(
            "import_markdown",
            "Test Section",
            str(base_path / "test_import_markdown_no_frontmatter.md"),
            site="example.com",
        )

        article = Article.objects.first()

        # Assertions
        self.assertEqual(Section.objects.count(), 1)
        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(Site.objects.count(), 1)

        # Title should come from file name
        self.assertEqual(article.title, "A Markdown File with No Front Matter")
        # Slug should come from file name
        self.assertEqual(article.slug, "test_import_markdown_no_frontmatter")
        self.assertEqual(article.description, "")
        # Section should have been generated
        self.assertEqual(article.section.title, "Test Section")
        # Tags should be empty
        self.assertListEqual(list(article.tags.names()), [])
        # Content should be extracted from markdown
        # Note the H1 tag is removed because it is assumed to be the title
        expected = """
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur fermentum velit non
        nisi dapibus, ut dapibus neque viverra. Proin ut nunc sed odio ullamcorper pharetra. Ut
        convallis, justo eu ullamcorper lacinia, felis nisi malesuada enim, at tristique elit
        nulla vel magna. Suspendisse potenti. Mauris fermentum leo et malesuada viverra. Vivamus
        eget lectus vel libero tempus interdum nec sed felis. Fusce scelerisque purus in cursus
        scelerisque. Pellentesque habitant morbi tristique senectus et netus et malesuada fames
        ac turpis egestas.</p>
        <p>Pellentesque vel nisi eu justo finibus vestibulum. Integer consectetur, eros ut luctus
        scelerisque, leo libero porttitor erat, sed auctor lacus lorem non nulla. Nulla
        facilisi. Nam aliquet dui ut eros vulputate, non sodales tortor sagittis. Aliquam erat
        volutpat. Suspendisse accumsan lacus in justo tincidunt, ac bibendum turpis ullamcorper.
        Integer condimentum leo sed nisl convallis, vel lobortis purus tincidunt. Praesent
        cursus risus quis suscipit vehicula. In consequat urna sit amet turpis interdum, nec
        fringilla ligula convallis.</p>
        <p>Sed tincidunt, odio vel congue fermentum, dui risus tristique nulla, nec commodo lorem
        risus ut nulla. Praesent ut felis et odio rhoncus laoreet non id justo. Aenean in lectus
        eget urna elementum sollicitudin. Cras faucibus dui nec eros ullamcorper, non eleifend
        sem dapibus. In ut sapien id felis viverra facilisis. Donec fringilla orci sit amet arcu
        efficitur, vel efficitur sapien elementum. Nulla facilisi. Integer vitae enim vel nulla
        venenatis malesuada ut sit amet odio. Vivamus nec dictum elit, eget gravida ex.</p>
        """
        self.assertHTMLEqual(article.body, expected)
