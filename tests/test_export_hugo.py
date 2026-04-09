import os
import shutil
import tempfile
from datetime import datetime
from datetime import timezone as dt_timezone
from pathlib import Path

import yaml
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from commoncontent.actions import export_page, export_site
from commoncontent.common import Status
from commoncontent.models import (
    Article,
    Attachment,
    HomePage,
    Image,
    Page,
    PageImage,
    Section,
)

Site = apps.get_app_config("sitevars").Site
TEST_DATA_DIR = Path(__file__).resolve().parent / "testdata"


class ExportPageTestCase(TestCase):
    """Tests for the export_page function."""

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.outdir = tempfile.mkdtemp()
        self.content_dir = Path(self.outdir) / "content"
        self.content_dir.mkdir(parents=True, exist_ok=True)
        # Create a media root for test files
        self.media_root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.outdir, ignore_errors=True)
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _create_test_image(self, filename="test_image.jpg"):
        """Create a test Image object with an actual file."""
        src = TEST_DATA_DIR / "test_image.jpg"
        with open(src, "rb") as f:
            uploaded = SimpleUploadedFile(filename, f.read(), content_type="image/jpeg")
        image = Image.objects.create(
            title="Test Image",
            site=self.site,
            image_file=uploaded,
            alt_text="A test image",
        )
        return image

    def _create_test_attachment(self, filename="test_attachment.txt"):
        """Create a test Attachment object with an actual file."""
        src = TEST_DATA_DIR / "test_attachment.txt"
        with open(src, "rb") as f:
            uploaded = SimpleUploadedFile(filename, f.read(), content_type="text/plain")
        attachment = Attachment.objects.create(
            title="Test Attachment",
            site=self.site,
            file=uploaded,
        )
        return attachment

    def test_export_page_basic(self):
        """Test basic Page export creates correct index file with front matter."""
        page = Page.objects.create(
            title="Test Page",
            slug="test-page",
            status=Status.USABLE,
            site=self.site,
            body="<p>Hello World</p>",
            date_published=datetime(2024, 1, 15, 12, 0, tzinfo=dt_timezone.utc),
        )
        export_page(page, self.content_dir)

        index_path = self.content_dir / "test-page" / "index.html"
        self.assertTrue(index_path.exists())

        content = index_path.read_text()
        # Check YAML front matter delimiters
        self.assertTrue(content.startswith("---\n"))
        # Parse front matter
        parts = content.split("---\n", 2)
        fm = yaml.safe_load(parts[1])
        self.assertEqual(fm["title"], "Test Page")
        self.assertFalse(fm["draft"])
        self.assertIn("2024", fm["publishdate"])
        # Check body
        self.assertIn("<p>Hello World</p>", parts[2])

    def test_export_homepage(self):
        """Test HomePage export creates _index.html at content root."""
        homepage = HomePage.objects.create(
            title="Welcome Home",
            slug="home",
            admin_name="Main Home",
            status=Status.USABLE,
            site=self.site,
            body="<h1>Welcome</h1>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(homepage, self.content_dir)

        # HomePage URL is "/" so bundle is at content root
        index_path = self.content_dir / "_index.html"
        self.assertTrue(index_path.exists())
        content = index_path.read_text()
        self.assertIn("Welcome Home", content)

    def test_export_section(self):
        """Test Section export creates _index.html in section directory."""
        section = Section.objects.create(
            title="Tech",
            slug="tech",
            status=Status.USABLE,
            site=self.site,
            body="<p>Tech section</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(section, self.content_dir)

        index_path = self.content_dir / "tech" / "_index.html"
        self.assertTrue(index_path.exists())
        content = index_path.read_text()
        self.assertIn("Tech", content)
        self.assertIn("<p>Tech section</p>", content)

    def test_export_article(self):
        """Test Article export creates index.html in correct path."""
        section = Section.objects.create(
            title="Blog",
            slug="blog",
            status=Status.USABLE,
            site=self.site,
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        article = Article.objects.create(
            title="My Article",
            slug="my-article",
            section=section,
            status=Status.USABLE,
            site=self.site,
            body="<p>Article body</p>",
            date_published=datetime(2024, 6, 15, 12, 0, tzinfo=dt_timezone.utc),
        )
        export_page(article, self.content_dir)

        # Article URL: /blog/my-article.html -> bundle at blog/my-article/
        index_path = self.content_dir / "blog" / "my-article" / "index.html"
        self.assertTrue(index_path.exists())
        content = index_path.read_text()
        self.assertIn("My Article", content)

    def test_export_draft_page(self):
        """Test that a draft page has draft: true in front matter."""
        page = Page.objects.create(
            title="Draft Page",
            slug="draft-page",
            status=Status.WITHHELD,
            site=self.site,
            body="<p>Draft</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(page, self.content_dir)

        index_path = self.content_dir / "draft-page" / "index.html"
        content = index_path.read_text()
        parts = content.split("---\n", 2)
        fm = yaml.safe_load(parts[1])
        self.assertTrue(fm["draft"])

    def test_export_page_all_front_matter_fields(self):
        """Test that all front matter fields are exported when present."""
        page = Page.objects.create(
            title="Full Page",
            subtitle="A subtitle",
            slug="full-page",
            status=Status.USABLE,
            site=self.site,
            seo_title="SEO Title",
            seo_description="SEO description text",
            body="<p>Body</p>",
            date_created=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
            date_published=datetime(2024, 1, 15, 12, 0, tzinfo=dt_timezone.utc),
            date_modified=datetime(2024, 2, 1, 12, 0, tzinfo=dt_timezone.utc),
            expires=datetime(2025, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
            custom_copyright_notice="(c) {} Test",
            custom_icon="custom-icon",
        )
        export_page(page, self.content_dir)

        index_path = self.content_dir / "full-page" / "index.html"
        content = index_path.read_text()
        parts = content.split("---\n", 2)
        fm = yaml.safe_load(parts[1])
        self.assertEqual(fm["title"], "Full Page")
        self.assertEqual(fm["subtitle"], "A subtitle")
        self.assertEqual(fm["seo_title"], "SEO Title")
        self.assertEqual(fm["description"], "SEO description text")
        self.assertFalse(fm["draft"])
        self.assertIn("2024", fm["dateCreated"])
        self.assertIn("2024", fm["publishdate"])
        self.assertIn("2024", fm["lastmod"])
        self.assertIn("2025", fm["expirydate"])
        self.assertIn("copyright", fm)
        self.assertEqual(fm["icon_name"], "custom-icon")

    def test_export_page_empty_fields_omitted(self):
        """Test that empty/null fields are not in front matter."""
        page = Page.objects.create(
            title="Minimal Page",
            slug="minimal",
            status=Status.USABLE,
            site=self.site,
            body="<p>Body</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(page, self.content_dir)

        index_path = self.content_dir / "minimal" / "index.html"
        content = index_path.read_text()
        parts = content.split("---\n", 2)
        fm = yaml.safe_load(parts[1])
        self.assertNotIn("subtitle", fm)
        self.assertNotIn("seo_title", fm)
        self.assertNotIn("dateCreated", fm)
        self.assertNotIn("lastmod", fm)
        self.assertNotIn("expirydate", fm)
        self.assertNotIn("cover", fm)

    def test_export_page_rich_description(self):
        """Test that rich_description.html is created when description is present."""
        page = Page.objects.create(
            title="Described Page",
            slug="described",
            status=Status.USABLE,
            site=self.site,
            body="<p>Body</p>",
            description="<p>Rich description</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(page, self.content_dir)

        desc_path = self.content_dir / "described" / "rich_description.html"
        self.assertTrue(desc_path.exists())
        self.assertEqual(desc_path.read_text(), "<p>Rich description</p>")

    def test_export_page_no_description(self):
        """Test that rich_description.html is NOT created when no description."""
        page = Page.objects.create(
            title="No Desc",
            slug="no-desc",
            status=Status.USABLE,
            site=self.site,
            body="<p>Body</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(page, self.content_dir)

        desc_path = self.content_dir / "no-desc" / "rich_description.html"
        self.assertFalse(desc_path.exists())

    @override_settings(MEDIA_ROOT=None)
    def test_export_page_with_share_image(self):
        """Test that share_image is exported and metadata file created."""
        with self.settings(MEDIA_ROOT=self.media_root):
            image = self._create_test_image("cover.jpg")
            page = Page.objects.create(
                title="With Image",
                slug="with-image",
                status=Status.USABLE,
                site=self.site,
                body="<p>Body</p>",
                share_image=image,
                date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
            )
            export_page(page, self.content_dir)

            bundle_dir = self.content_dir / "with-image"
            # Check image file was exported
            exported_files = list(bundle_dir.glob("cover*.jpg"))
            self.assertTrue(len(exported_files) > 0, "Image file should be exported")

            # Check metadata YAML was created
            meta_files = list(bundle_dir.glob("cover*.jpg.yaml"))
            self.assertTrue(len(meta_files) > 0, "Image metadata should be exported")

            meta = yaml.safe_load(meta_files[0].read_text())
            self.assertEqual(meta["alt_text"], "A test image")
            self.assertIn("mime_type", meta)

            # Check cover in front matter
            index_content = (bundle_dir / "index.html").read_text()
            parts = index_content.split("---\n", 2)
            fm = yaml.safe_load(parts[1])
            self.assertIn("cover", fm)

    @override_settings(MEDIA_ROOT=None)
    def test_export_page_with_image_collection(self):
        """Test that image collections are exported."""
        with self.settings(MEDIA_ROOT=self.media_root):
            image = self._create_test_image("gallery.jpg")
            page = Page.objects.create(
                title="Gallery Page",
                slug="gallery",
                status=Status.USABLE,
                site=self.site,
                body="<p>Body</p>",
                date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
            )
            PageImage.objects.create(
                page=page,
                image=image,
                title="Gallery Image",
                alt_text="Gallery alt",
            )
            export_page(page, self.content_dir)

            bundle_dir = self.content_dir / "gallery"
            image_files = list(bundle_dir.glob("gallery*.jpg"))
            self.assertTrue(len(image_files) > 0, "Gallery image should be exported")

    @override_settings(MEDIA_ROOT=None)
    def test_export_page_with_attachment(self):
        """Test that attachments are exported with metadata."""
        with self.settings(MEDIA_ROOT=self.media_root):
            attachment = self._create_test_attachment("doc.txt")
            page = Page.objects.create(
                title="Doc Page",
                slug="doc-page",
                status=Status.USABLE,
                site=self.site,
                body="<p>Body</p>",
                date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
            )
            page.attachment_set.add(attachment)
            export_page(page, self.content_dir)

            bundle_dir = self.content_dir / "doc-page"
            att_files = list(bundle_dir.glob("doc*.txt"))
            self.assertTrue(len(att_files) > 0, "Attachment should be exported")

            meta_files = list(bundle_dir.glob("doc*.txt.yaml"))
            self.assertTrue(
                len(meta_files) > 0, "Attachment metadata should be exported"
            )
            meta = yaml.safe_load(meta_files[0].read_text())
            self.assertEqual(meta["title"], "Test Attachment")
            self.assertIn("mime_type", meta)

    def test_export_page_skip_mode(self):
        """Test that skip mode does not overwrite existing files."""
        page = Page.objects.create(
            title="Skip Test",
            slug="skip-test",
            status=Status.USABLE,
            site=self.site,
            body="<p>Original</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(page, self.content_dir)

        index_path = self.content_dir / "skip-test" / "index.html"
        original_content = index_path.read_text()

        # Modify the page content
        page.body = "<p>Modified</p>"
        page.save()

        # Export again in skip mode
        export_page(page, self.content_dir, mode="skip")

        # Content should NOT have changed
        self.assertEqual(index_path.read_text(), original_content)

    def test_export_page_overwrite_mode(self):
        """Test that overwrite mode updates existing files."""
        page = Page.objects.create(
            title="Overwrite Test",
            slug="overwrite-test",
            status=Status.USABLE,
            site=self.site,
            body="<p>Original</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(page, self.content_dir)

        # Modify and force overwrite
        page.body = "<p>Modified</p>"
        page.save()

        export_page(page, self.content_dir, mode="overwrite", force=True)

        index_path = self.content_dir / "overwrite-test" / "index.html"
        content = index_path.read_text()
        self.assertIn("<p>Modified</p>", content)

    def test_export_article_with_series(self):
        """Test that articles in a series export to the correct path."""
        from commoncontent.models import ArticleSeries

        section = Section.objects.create(
            title="Blog",
            slug="blog",
            status=Status.USABLE,
            site=self.site,
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        series = ArticleSeries.objects.create(
            name="Getting Started",
            slug="getting-started",
            site=self.site,
        )
        article = Article.objects.create(
            title="Part One",
            slug="part-one",
            section=section,
            series=series,
            status=Status.USABLE,
            site=self.site,
            body="<p>Part 1</p>",
            date_published=datetime(2024, 6, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_page(article, self.content_dir)

        # Article with series URL: /blog/getting-started/part-one.html
        index_path = (
            self.content_dir / "blog" / "getting-started" / "part-one" / "index.html"
        )
        self.assertTrue(index_path.exists())


class ExportSiteTestCase(TestCase):
    """Tests for the export_site function."""

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.outdir = tempfile.mkdtemp()
        self.media_root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.outdir, ignore_errors=True)
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_export_site_creates_content_dir(self):
        """Test that export_site creates the content directory."""
        export_site(self.site, self.outdir)
        self.assertTrue((Path(self.outdir) / "content").exists())

    def test_export_site_exports_homepage(self):
        """Test that export_site exports the current home page."""
        HomePage.objects.create(
            title="Home",
            slug="home",
            admin_name="Test Home",
            status=Status.USABLE,
            site=self.site,
            body="<p>Home content</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_site(self.site, self.outdir)

        index_path = Path(self.outdir) / "content" / "_index.html"
        self.assertTrue(index_path.exists())
        self.assertIn("Home", index_path.read_text())

    def test_export_site_exports_pages(self):
        """Test that export_site exports all pages."""
        Page.objects.create(
            title="About",
            slug="about",
            status=Status.USABLE,
            site=self.site,
            body="<p>About us</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        Page.objects.create(
            title="Contact",
            slug="contact",
            status=Status.USABLE,
            site=self.site,
            body="<p>Contact us</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_site(self.site, self.outdir)

        content_dir = Path(self.outdir) / "content"
        self.assertTrue((content_dir / "about" / "index.html").exists())
        self.assertTrue((content_dir / "contact" / "index.html").exists())

    def test_export_site_exports_sections_and_articles(self):
        """Test that export_site exports sections and articles."""
        section = Section.objects.create(
            title="News",
            slug="news",
            status=Status.USABLE,
            site=self.site,
            body="<p>News section</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        Article.objects.create(
            title="Breaking News",
            slug="breaking-news",
            section=section,
            status=Status.USABLE,
            site=self.site,
            body="<p>Big news</p>",
            date_published=datetime(2024, 6, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_site(self.site, self.outdir)

        content_dir = Path(self.outdir) / "content"
        self.assertTrue((content_dir / "news" / "_index.html").exists())
        self.assertTrue(
            (content_dir / "news" / "breaking-news" / "index.html").exists()
        )

    def test_export_site_remove_mode(self):
        """Test that remove mode clears the output directory."""
        # Create a pre-existing file
        outdir = Path(self.outdir)
        (outdir / "old_file.txt").write_text("old content")

        export_site(self.site, self.outdir, mode="remove")

        self.assertFalse((outdir / "old_file.txt").exists())
        self.assertTrue((outdir / "content").exists())

    def test_export_site_skip_mode(self):
        """Test that skip mode does not overwrite existing exported content."""
        page = Page.objects.create(
            title="Existing",
            slug="existing",
            status=Status.USABLE,
            site=self.site,
            body="<p>Original body</p>",
            date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_site(self.site, self.outdir, mode="skip")

        index_path = Path(self.outdir) / "content" / "existing" / "index.html"
        original = index_path.read_text()

        page.body = "<p>Updated body</p>"
        page.save()
        export_site(self.site, self.outdir, mode="skip")

        self.assertEqual(index_path.read_text(), original)

    @override_settings(STATIC_ROOT=TEST_DATA_DIR / "static")
    def test_export_site_static_files(self):
        """Test that static files from static/$domain/ are copied to assets."""
        export_site(self.site, self.outdir)

        assets_dir = Path(self.outdir) / "assets"
        css_file = assets_dir / "css" / "style.css"
        self.assertTrue(css_file.exists())
        self.assertIn("color: red", css_file.read_text())

    def test_export_site_only_current_homepage(self):
        """Test that only the most recently published live homepage is exported."""
        # Create two homepages - only the most recent live one should be exported
        HomePage.objects.create(
            title="Old Home",
            slug="old-home",
            admin_name="Old Home",
            status=Status.USABLE,
            site=self.site,
            body="<p>Old home</p>",
            date_published=datetime(2023, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        HomePage.objects.create(
            title="New Home",
            slug="new-home",
            admin_name="New Home",
            status=Status.USABLE,
            site=self.site,
            body="<p>New home</p>",
            date_published=datetime(2024, 6, 1, 0, 0, tzinfo=dt_timezone.utc),
        )
        export_site(self.site, self.outdir)

        index_path = Path(self.outdir) / "content" / "_index.html"
        self.assertTrue(index_path.exists())
        content = index_path.read_text()
        self.assertIn("New Home", content)

    def test_export_site_nonexistent_outdir(self):
        """Test that export_site creates the outdir if it doesn't exist."""
        new_outdir = os.path.join(self.outdir, "new", "nested", "dir")
        export_site(self.site, new_outdir)
        self.assertTrue(Path(new_outdir).exists())
        self.assertTrue((Path(new_outdir) / "content").exists())


class ExportMediaMetadataTestCase(TestCase):
    """Tests for media metadata export."""

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.outdir = tempfile.mkdtemp()
        self.content_dir = Path(self.outdir) / "content"
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.media_root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.outdir, ignore_errors=True)
        shutil.rmtree(self.media_root, ignore_errors=True)

    @override_settings(MEDIA_ROOT=None)
    def test_image_metadata_fields(self):
        """Test that image metadata contains expected fields."""
        with self.settings(MEDIA_ROOT=self.media_root):
            src = TEST_DATA_DIR / "test_image.jpg"
            with open(src, "rb") as f:
                uploaded = SimpleUploadedFile(
                    "meta_test.jpg", f.read(), content_type="image/jpeg"
                )
            image = Image.objects.create(
                title="Meta Test Image",
                site=self.site,
                image_file=uploaded,
                alt_text="Alt for meta",
            )
            page = Page.objects.create(
                title="Meta Page",
                slug="meta-page",
                status=Status.USABLE,
                site=self.site,
                body="<p>Body</p>",
                share_image=image,
                date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
            )
            export_page(page, self.content_dir)

            bundle_dir = self.content_dir / "meta-page"
            meta_files = list(bundle_dir.glob("*.jpg.yaml"))
            self.assertTrue(len(meta_files) > 0)

            meta = yaml.safe_load(meta_files[0].read_text())
            self.assertEqual(meta["title"], "Meta Test Image")
            self.assertEqual(meta["alt_text"], "Alt for meta")
            self.assertIn("mime_type", meta)
            self.assertIn("upload_date", meta)
            # Width and height should be set from the actual image
            self.assertIn("width", meta)
            self.assertIn("height", meta)

    @override_settings(MEDIA_ROOT=None)
    def test_attachment_metadata_fields(self):
        """Test that attachment metadata contains expected fields."""
        with self.settings(MEDIA_ROOT=self.media_root):
            src = TEST_DATA_DIR / "test_attachment.txt"
            with open(src, "rb") as f:
                uploaded = SimpleUploadedFile(
                    "attach_meta.txt", f.read(), content_type="text/plain"
                )
            attachment = Attachment.objects.create(
                title="Attach Meta Test",
                site=self.site,
                file=uploaded,
            )
            page = Page.objects.create(
                title="Attach Page",
                slug="attach-page",
                status=Status.USABLE,
                site=self.site,
                body="<p>Body</p>",
                date_published=datetime(2024, 1, 1, 0, 0, tzinfo=dt_timezone.utc),
            )
            page.attachment_set.add(attachment)
            export_page(page, self.content_dir)

            bundle_dir = self.content_dir / "attach-page"
            meta_files = list(bundle_dir.glob("*.txt.yaml"))
            self.assertTrue(len(meta_files) > 0)

            meta = yaml.safe_load(meta_files[0].read_text())
            self.assertEqual(meta["title"], "Attach Meta Test")
            self.assertIn("mime_type", meta)
            self.assertIn("upload_date", meta)
            # Attachment should NOT have image-specific fields
            self.assertNotIn("alt_text", meta)
            self.assertNotIn("width", meta)
            self.assertNotIn("height", meta)
