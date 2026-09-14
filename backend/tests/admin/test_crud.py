def test_crud_list_products():
    from admin.services.crud_service import crud_service
    products = crud_service.list_products(skip=0, limit=10)
    assert len(products) > 0


def test_crud_count_products():
    from admin.services.crud_service import crud_service
    count = crud_service.count_products()
    assert count > 0


def test_crud_get_product():
    from admin.services.crud_service import crud_service
    product = crud_service.get_product("1001")
    assert product is not None
    assert product.get("ItemName") == "Paracetamol 500mg"


def test_crud_stats():
    from admin.services.crud_service import crud_service
    stats = crud_service.get_stats()
    assert stats["products_count"] > 0
    assert "drugs_count" in stats
