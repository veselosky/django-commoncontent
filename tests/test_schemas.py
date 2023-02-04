from genericsite.schemas import AudioProp, ImageProp, OGArticle, OGProfile


def test_audio_schema():
    url = "https://example.com/audio.mp3"
    a = AudioProp(url=url, secure_url=url, type="audio/mp3")
    print(a)
    assert "_prefix" not in a.__str__()
    assert "audio:url" not in a.__str__()
    assert '''property="og:audio"''' in a.__str__()
    assert "og:audio:secure_url" in a.__str__()
    assert "og:audio:type" in a.__str__()


def test_article_schema():
    a = OGArticle(
        title="My First Article",
        description="An article about the first opengraph object",
        url="https://example.com/",
        published_time="2022-06-30T12:00:00Z",
        author=["https://vince.veselosky.me"],
        tag=["testpost", "ignoreme"],
    )
    print(a)
    assert '''property="og:type" content="article"''' in str(a)
    assert '''property="article:tag" content="testpost"''' in str(a)
    assert '''property="article:tag" content="ignoreme"''' in str(a)
    assert '''property="article:author" content="https://vince.veselosky.me"''' in str(
        a
    )
    assert "2022-06-30 12:00:00+00:00" in str(a)


def test_article_schema_with_image():
    img = ImageProp(
        url="https://example.com/image.jpg",
        type="image/jpeg",
        width=1280,
        height=720,
        alt="alt text here",
    )
    a = OGArticle(
        title="My First Article",
        description="An article about the first opengraph object",
        url="https://example.com/",
        published_time="2022-06-30T12:00:00Z",
        author=["https://vince.veselosky.me"],
        tag=["testpost", "ignoreme"],
        image=[img],
    )
    print(a)
    assert '''property="og:type" content="article"''' in str(a)
    assert '''property="article:tag" content="testpost"''' in str(a)
    assert '''property="article:tag" content="ignoreme"''' in str(a)
    assert '''property="article:author" content="https://vince.veselosky.me"''' in str(
        a
    )
    assert "2022-06-30 12:00:00+00:00" in str(a)
    assert 'property="og:image" content="https://example.com/image.jpg"' in str(a)
    assert 'property="og:image:type" content="image/jpeg"' in str(a)
    assert 'property="og:image:width" content="1280"' in str(a)
    assert 'property="og:image:height" content="720"' in str(a)
    assert 'property="og:image:alt" content="alt text here"' in str(a)
