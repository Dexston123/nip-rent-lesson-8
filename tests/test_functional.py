from src.manager import Manager
from src.models import (
    ApartmentSettlement,
    Bill,
    Parameters,
    TenantBlacklistEntry,
    TenantSettlement,
    Transfer,
)


def test_settlement_due_between_tenants_and_apartment():
    manager = Manager(Parameters())

    settlement: ApartmentSettlement = manager.get_settlement(
        "apart-polanka", 2025, 1
    )

    tenants_settlements: list[TenantSettlement] = (
        manager.create_tenants_settlements(settlement)
    )
    assert len(tenants_settlements) == 3

    total_due = sum(
        tenant_settlement.total_due_pln
        for tenant_settlement in tenants_settlements
    )
    assert total_due == settlement.total_due_pln


def test_debtors_calculation():
    manager = Manager(Parameters())

    debtors = manager.get_debtors("apart-polanka", 2025, 1)
    assert len(debtors) == 0

    debtors = manager.get_debtors("apart-polanka", 2025, 2)
    assert len(debtors) == 3


def test_tax_calculation():
    manager = Manager(Parameters())

    tax = manager.calculate_tax(2025, 1, 0.085)
    assert tax == 638

    tax = manager.calculate_tax(2025, 2, 0.085)
    assert tax == 0


def test_deposits_calculation():
    manager = Manager(Parameters())

    deposit_balance = manager.check_deposits()
    assert deposit_balance == -8700.0

    manager.transfers.append(
        Transfer(
            tenant="tenant-1",
            date="2025-01-01",
            settlement_year=None,
            settlement_month=None,
            amount_pln=1000.0,
            type="deposit",
        )
    )

    deposit_balance = manager.check_deposits()
    assert deposit_balance == -7700.0


def test_annual_balance_calculation():
    manager = Manager(Parameters())

    annual_balance = manager.get_annual_balance(2025)
    assert annual_balance == 6490.0

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2025-02-15",
            settlement_year=2025,
            settlement_month=5,
            amount_pln=500.0,
            type="rent",
        )
    )

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2025-02-15",
            settlement_year=2025,
            settlement_month=5,
            amount_pln=4500.0,
            type="renovation",
        )
    )

    annual_balance = manager.get_annual_balance(2025)
    assert annual_balance == 1490.0


def test_apartment_has_any_bills():
    manager = Manager(Parameters())

    has_bills = manager.has_any_bills("apart-polanka", 2025, 1)
    assert has_bills is True

    has_bills = manager.has_any_bills("apart-polanka", 2025, 3)
    assert has_bills is False


def test_min_max_transfer_amount():
    manager = Manager(Parameters())

    success = manager.check_transfers_amount_range()
    assert success is True

    manager.transfers[-1].amount_pln = 10000
    success = manager.check_transfers_amount_range()
    assert success is False

    manager.transfers[-1].amount_pln = -3000
    success = manager.check_transfers_amount_range()
    assert success is False


def test_tenant_blacklist_check():
    manager = Manager(Parameters())

    is_blacklisted = manager.check_tenant_blacklist("Jan Pawlak")
    assert is_blacklisted is False

    manager.tenants_blacklist.append(
        TenantBlacklistEntry(
            tenant="Jan Pawlak",
            reason="Previous unpaid rent",
        )
    )

    is_blacklisted = manager.check_tenant_blacklist("Jan Pawlak")
    assert is_blacklisted is True


def test_transfer_valid_with_tenant_agreement():
    manager = Manager(Parameters())

    is_valid = manager.check_transfers_tenant()
    assert is_valid is True

    manager.transfers.append(
        Transfer(
            tenant="non-existing-tenant",
            date="2025-01-01",
            settlement_year=2025,
            settlement_month=1,
            amount_pln=1000.0,
            type="rent",
        )
    )

    is_valid = manager.check_transfers_tenant()
    assert is_valid is False

    manager.transfers.pop()
    manager.transfers.append(
        Transfer(
            tenant="tenant-1",
            date="2025-01-01",
            settlement_year=1999,
            settlement_month=1,
            amount_pln=1000.0,
            type="rent",
        )
    )

    is_valid = manager.check_transfers_tenant()
    assert is_valid is False