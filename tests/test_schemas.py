import datetime
import unittest

from genericsite.schemas import AudioProp, ImageProp, OGArticle, OGProfile


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
