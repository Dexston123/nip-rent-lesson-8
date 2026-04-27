import pytest

from src.manager import Manager
from src.models import ApartmentSettlement, Bill, Parameters, TenantSettlement


def test_apartment_costs():
    manager = Manager(Parameters())

    costs = manager.get_apartment_costs("apartment-1", 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs("apart-polanka", 2024, 1)
    assert costs == 0.0

    costs = manager.get_apartment_costs("apart-polanka", 2025, 1)
    assert costs == 910.0

    with pytest.raises(ValueError):
        manager.get_apartment_costs("apart-polanka", 2024, 13)

    with pytest.raises(ValueError):
        manager.get_apartment_costs("apart-polanka", 2024, 0)


def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2025-03-15",
            settlement_year=2025,
            settlement_month=2,
            amount_pln=1250.0,
            type="rent",
        )
    )

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2024-03-15",
            settlement_year=2024,
            settlement_month=2,
            amount_pln=1150.0,
            type="rent",
        )
    )

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2024-02-02",
            settlement_year=2024,
            settlement_month=1,
            amount_pln=222.0,
            type="electricity",
        )
    )

    costs = manager.get_apartment_costs("apartment-1", 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs("apart-polanka", 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs("apart-polanka", 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs("apart-polanka", 2025, 1)
    assert costs == 910.0

    costs = manager.get_apartment_costs("apart-polanka", 2024)
    assert costs == 1372.0

    costs = manager.get_apartment_costs("apart-polanka")
    assert costs == 3632.0


def test_settlement_creation():
    manager = Manager(Parameters())

    apartment_settlement = manager.get_settlement("apart-polanka", 2025, 1)
    assert isinstance(apartment_settlement, ApartmentSettlement)
    assert apartment_settlement.key == "apart-polanka-2025-1"
    assert apartment_settlement.apartment == "apart-polanka"
    assert apartment_settlement.month == 1
    assert apartment_settlement.year == 2025
    assert apartment_settlement.total_due_pln == 910.0

    apartment_settlement = manager.get_settlement("apart-polanka", 2024, 1)
    assert isinstance(apartment_settlement, ApartmentSettlement)
    assert apartment_settlement.key == "apart-polanka-2024-1"
    assert apartment_settlement.apartment == "apart-polanka"
    assert apartment_settlement.month == 1
    assert apartment_settlement.year == 2024
    assert apartment_settlement.total_due_pln == 0.0


def test_tenants_settlements_creation():
    manager = Manager(Parameters())

    apartment_settlement = manager.get_settlement("apart-polanka", 2025, 1)
    tenants_settlements = manager.create_tenants_settlements(
        apartment_settlement
    )

    assert isinstance(tenants_settlements, list)
    assert len(tenants_settlements) == 3

    for tenant_settlement in tenants_settlements:
        assert isinstance(tenant_settlement, TenantSettlement)
        assert (
            tenant_settlement.apartment_settlement
            == apartment_settlement.key
        )
        assert tenant_settlement.month == apartment_settlement.month
        assert tenant_settlement.year == apartment_settlement.year
        assert (
            tenant_settlement.total_due_pln
            == apartment_settlement.total_due_pln / 3
        )

    del manager.tenants["tenant-1"]
    del manager.tenants["tenant-2"]

    apartment_settlement = manager.get_settlement("apart-polanka", 2025, 1)
    tenants_settlements = manager.create_tenants_settlements(
        apartment_settlement
    )

    assert isinstance(tenants_settlements, list)
    assert len(tenants_settlements) == 1

    tenant_settlement = tenants_settlements[0]
    assert isinstance(tenant_settlement, TenantSettlement)
    assert tenant_settlement.apartment_settlement == apartment_settlement.key
    assert tenant_settlement.month == apartment_settlement.month
    assert tenant_settlement.year == apartment_settlement.year
    assert tenant_settlement.total_due_pln == apartment_settlement.total_due_pln

    del manager.tenants["tenant-3"]

    apartment_settlement = manager.get_settlement("apart-polanka", 2025, 1)
    tenants_settlements = manager.create_tenants_settlements(
        apartment_settlement
    )

    assert isinstance(tenants_settlements, list)
    assert len(tenants_settlements) == 0