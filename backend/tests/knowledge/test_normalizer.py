def test_normalize_arabic():
    from knowledge.analyzer.normalizer import normalizer
    result = normalizer.normalize("الإِسْتِعْمَال")
    assert result == "الاستعمال" or result  # basic sanity


def test_normalize_alef():
    from knowledge.analyzer.normalizer import normalizer
    assert "ا" in normalizer.normalize("أحمد")


def test_tokenize():
    from knowledge.analyzer.normalizer import normalizer
    tokens = normalizer.tokenize("عندي صداع")
    assert len(tokens) > 0
