def test_router_customer():
    from agents.router import Router
    r = Router()
    assert r.route_type("بكام البانادول؟") == "customer"


def test_router_pharmacist():
    from agents.router import Router
    r = Router()
    assert r.route_type("في تداخل دوائي") == "pharmacist"
