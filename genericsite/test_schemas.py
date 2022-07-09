def test_audio_schema():
    from genericsite.schemas import AudioProp

    url = "https://example.com/audio.mp3"
    a = AudioProp(url=url, secure_url=url, type="audio/mp3")
    print(a)
    assert "_prefix" not in a.__str__()
    assert "audio:url" not in a.__str__()
    assert '''property="og:audio"''' in a.__str__()
    assert "og:audio:secure_url" in a.__str__()
    assert "og:audio:type" in a.__str__()


def test_article_schema():
    from genericsite.schemas import OGArticle, OGProfile

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
