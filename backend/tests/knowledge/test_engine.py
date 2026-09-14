def test_engine_search():
    from knowledge.engine import advisory_engine
    advisory_engine.initialize()
    results = advisory_engine.search("paracetamol", top_k=3)
    assert len(results) > 0


def test_engine_analyze():
    from knowledge.engine import advisory_engine
    advisory_engine.initialize()
    result = advisory_engine.analyze("بانادول")
    assert result.confidence >= 0.0
