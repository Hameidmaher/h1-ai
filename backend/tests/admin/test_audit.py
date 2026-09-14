def test_audit_log():
    from admin.services.audit_service import audit_service
    audit_service.log(user="test", action="TEST", entity="test")
    entries = audit_service.read_recent(limit=10)
    assert len(entries) > 0
    assert entries[0]["action"] == "TEST"
