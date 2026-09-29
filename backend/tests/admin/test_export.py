def test_export_products_csv():
    from admin.services.export_service import export_service
    csv_data = export_service.products_csv()
    assert len(csv_data) > 0
    assert "ItemCode" in csv_data


def test_export_full():
    from admin.services.export_service import export_service
    data = export_service.full_backup()
    assert "products" in data
    assert "drugs" in data
