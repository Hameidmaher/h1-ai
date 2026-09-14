def test_loader_products():
    from knowledge.loader import knowledge_loader
    knowledge_loader.load_all()
    assert len(knowledge_loader.products) > 0


def test_loader_interactions():
    from knowledge.loader import knowledge_loader
    knowledge_loader.load_all()
    assert len(knowledge_loader.interactions) > 0


def test_loader_rules():
    from knowledge.loader import knowledge_loader
    knowledge_loader.load_all()
    assert "conditions" in knowledge_loader.medical_rules
