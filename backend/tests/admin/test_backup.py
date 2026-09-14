def test_backup_create():
    from admin.services.backup_service import backup_service
    result = backup_service.backup_file("products.csv")
    assert result is True


def test_backup_list():
    from admin.services.backup_service import backup_service
    backups = backup_service.list_backups()
    assert isinstance(backups, list)
