from src.manager import Manager
from src.models import Apartment, Parameters


def test_load_data():
    manager = Manager(Parameters())

    assert isinstance(manager.apartments, dict)
    assert isinstance(manager.tenants, dict)
    assert isinstance(manager.transfers, list)
    assert isinstance(manager.bills, list)

    for apartment_key, apartment in manager.apartments.items():
        assert isinstance(apartment, Apartment)
        assert apartment.key == apartment_key


def test_tenants_in_manager():
    manager = Manager(Parameters())

    assert len(manager.tenants) > 0

    names = [tenant.name for tenant in manager.tenants.values()]

    expected = ["Jan Nowak", "Adam Kowalski", "Ewa Adamska"]
    for tenant in expected:
        assert tenant in names


def test_if_tenants_have_valid_apartment_keys():
    manager = Manager(Parameters())

    assert manager.check_tenants_apartment_keys()

    manager.tenants["tenant-1"].apartment = "invalid-key"

    assert not manager.check_tenants_apartment_keys()