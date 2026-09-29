def test_bm25_build():
    from knowledge.index.bm25_index import bm25_index
    from knowledge.loader import knowledge_loader
    knowledge_loader.load_all()
    bm25_index.build()
    assert bm25_index._built


def test_bm25_search():
    from knowledge.index.bm25_index import bm25_index
    from knowledge.loader import knowledge_loader
    knowledge_loader.load_all()
    bm25_index.build()
    results = bm25_index.search("paracetamol")
    assert len(results) > 0
