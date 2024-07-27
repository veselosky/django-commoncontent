import datetime
import unittest

from commoncontent.schemas import (
    AudioProp,
    CreativeWorkSchema,
    ImageProp,
    OGArticle,
    ThingSchema,
)


class TestOpenGraphSchemas(unittest.TestCase):
    def test_audio_schema(self):
        url = "https://example.com/audio.mp3"
        a = AudioProp(url=url, secure_url=url, type="audio/mp3")
        self.assertNotIn("_prefix", a.__str__())
        self.assertNotIn("audio:url", a.__str__())
        self.assertIn('property="og:audio"', a.__str__())
        self.assertIn("og:audio:secure_url", a.__str__())
        self.assertIn("og:audio:type", a.__str__())

    def test_article_schema(self):
        a = OGArticle(
            title="My First Article",
            description="An article about the first opengraph object",
            url="https://example.com/",
            published_time="2022-06-30T12:00:00Z",
            author=["https://vince.veselosky.me"],
            tag=["testpost", "ignoreme"],
        )
        self.assertIn('property="og:type" content="article"', str(a))
        self.assertIn('property="article:tag" content="testpost"', str(a))
        self.assertIn('property="article:tag" content="ignoreme"', str(a))
        self.assertIn(
            'property="article:author" content="https://vince.veselosky.me"',
            str(a),
        )
        self.assertIn("2022-06-30T12:00:00Z", str(a))

    def test_article_schema_with_image(self):
        img = ImageProp(
            url="https://example.com/image.jpg",
            type="image/jpeg",
            width=1280,
            height=720,
            alt="alt text here",
        )
        a = OGArticle(
            title="Article With Image",
            description="An article about the first opengraph object",
            url="https://example.com/",
            published_time="2022-06-30T12:00:00Z",
            author=["https://vince.veselosky.me"],
            tag=["testpost", "ignoreme"],
            image=[img],
        )
        self.assertIn('property="og:type" content="article"', str(a))
        self.assertIn('property="article:tag" content="testpost"', str(a))
        self.assertIn('property="article:tag" content="ignoreme"', str(a))
        self.assertIn(
            'property="article:author" content="https://vince.veselosky.me"',
            str(a),
        )
        self.assertIn("2022-06-30T12:00:00Z", str(a))
        self.assertIn(
            'property="og:image" content="https://example.com/image.jpg"', str(a)
        )
        self.assertIn('property="og:image:type" content="image/jpeg"', str(a))
        self.assertIn('property="og:image:width" content="1280"', str(a))
        self.assertIn('property="og:image:height" content="720"', str(a))
        self.assertIn('property="og:image:alt" content="alt text here"', str(a))

    def test_article_schema_using_datetime(self):
        a = OGArticle(
            title="Article With datetime object",
            description="An article about the first opengraph object",
            url="https://example.com/",
            published_time=datetime.datetime(2022, 6, 30, 12, 0, 0),
            author=["https://vince.veselosky.me"],
            tag=["testpost", "ignoreme"],
        )
        self.assertIn("2022-06-30T12:00:00", str(a))

    def test_article_schema_using_date(self):
        a = OGArticle(
            title="Article With date object",
            description="An article about the first opengraph object",
            url="https://example.com/",
            published_time=datetime.date(2022, 6, 30),
            author=["https://vince.veselosky.me"],
            tag=["testpost", "ignoreme"],
        )
        # When set to a date, value is converted to isoformat
        self.assertIn("2022-06-30", str(a))


class TestThingSchema(unittest.TestCase):
    def test_thing_schema_registry(self):
        klass = ThingSchema.get_class_for_label("Thing")
        self.assertEqual(klass, ThingSchema)
        klass = ThingSchema.get_class_for_label("CreativeWork")
        self.assertEqual(klass, CreativeWorkSchema)

    def test_thing_schema_string(self):
        t = ThingSchema(
            name="My Thing",
            description="A thing that is mine",
            url="https://example.com/mything",
        )
        out = str(t)
        expected = (
            """<script id="schema-data" type="application/ld+json">"""
            """{"name": "My Thing", "description": "A thing that is mine","""
            """ "url": "https://example.com/mything", "@context": "https://schema.org","""
            """ "@type": "Thing"}</script>"""
        )
        self.assertEqual(out, expected)
