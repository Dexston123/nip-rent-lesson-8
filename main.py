"""
Simple CLI report for apartments, tenants and monthly settlements.
"""

import sys
from src.manager import Manager
from src.models import Parameters


def print_section_header(title: str) -> None:
    """Print main section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_subsection_header(title: str) -> None:
    """Print subsection header."""
    print(f"\n  {title}")
    print(f"  {'-' * 40}")


def format_currency(amount: float) -> str:
    """Format number as PLN currency."""
    return f"{amount:,.2f} PLN"


def display_apartments(manager: Manager) -> None:
    """Display apartments with rooms and bills."""
    print_section_header("APARTMENTS")

    for apartment in manager.apartments.values():
        print(f"\n📍 {apartment.name} ({apartment.key})")
        print(f"   Location: {apartment.location}")
        print(f"   Total Area: {apartment.area_m2} m²")

        print_subsection_header("Rooms")
        for room in apartment.rooms.values():
            print(f"      • {room.name:<25} {room.area_m2:>6} m²")

        apartment_bills = [
            bill for bill in manager.bills
            if bill.apartment == apartment.key
        ]

        if apartment_bills:
            print_subsection_header("Bills")
            for bill in apartment_bills:
                period = (
                    f"{bill.settlement_month}/{bill.settlement_year}"
                    if bill.settlement_month and bill.settlement_year
                    else "N/A"
                )
                line = (
                    f"      • {bill.type:<15} "
                    f"{format_currency(bill.amount_pln):>15}  "
                    f"Due: {bill.date_due}  Period: {period}"
                )
                print(line)


def display_tenants(manager: Manager) -> None:
    """Display tenants with transfers."""
    print_section_header("TENANTS")

    for tenant in manager.tenants.values():
        print(f"\n👤 {tenant.name}")
        print(f"   Apartment: {tenant.apartment}")
        print(f"   Room: {tenant.room}")
        print(f"   Rent: {format_currency(tenant.rent_pln)}/month")
        print(f"   Deposit: {format_currency(tenant.deposit_pln)}")
        print(
            f"   Agreement: {tenant.date_agreement_from} "
            f"to {tenant.date_agreement_to}"
        )

        tenant_transfers = [
            transfer for transfer in manager.transfers
            if transfer.tenant == tenant.name
        ]

        if tenant_transfers:
            print_subsection_header("Transfers")
            for transfer in tenant_transfers:
                period = (
                    f"{transfer.settlement_month}/{transfer.settlement_year}"
                    if transfer.settlement_month and transfer.settlement_year
                    else "N/A"
                )
                print(
                    f"      • {format_currency(transfer.amount_pln):>15}  "
                    f"Date: {transfer.date}  Period: {period}"
                )


def display_monthly_settlement(
    manager: Manager,
    apartment_key: str,
    year: int,
    month: int
) -> None:
    """Display monthly settlement for apartment."""
    if apartment_key not in manager.apartments:
        print(f"\nError: apartment '{apartment_key}' not found.")
        return

    apartment = manager.apartments[apartment_key]
    settlement = manager.get_settlement(apartment_key, year, month)

    header = (
        f"MONTHLY SETTLEMENT — {apartment.name} "
        f"({apartment_key}) | {month:02d}/{year}"
    )
    print_section_header(header)

    apartment_bills = [
        bill for bill in manager.bills
        if bill.apartment == apartment_key
        and bill.settlement_year == year
        and bill.settlement_month == month
    ]

    print_subsection_header("Bills")
    if apartment_bills:
        for bill in apartment_bills:
            print(
                f"      • {bill.type:<20} "
                f"{format_currency(bill.amount_pln):>15}  "
                f"Due: {bill.date_due}"
            )
    else:
        print("      (no bills for this period)")

    print(
        f"\n      {'TOTAL BILLS':<20} "
        f"{format_currency(settlement.total_due_pln):>15}"
    )

    tenant_settlements = manager.create_tenants_settlements(settlement)
    tenants_in_apt = {
        t.name: t for t in manager.tenants.values()
        if t.apartment == apartment_key
    }

    print_subsection_header("Tenant Breakdown")

    for ts in tenant_settlements:
        tenant = tenants_in_apt.get(ts.tenant)
        rent = tenant.rent_pln if tenant else 0.0

        transfers = [
            tr for tr in manager.transfers
            if tr.tenant == ts.tenant
            and tr.settlement_year == year
            and tr.settlement_month == month
        ]

        total_paid = sum(tr.amount_pln for tr in transfers)
        total_due = rent + ts.total_due_pln
        balance = total_paid - total_due
        status = "OK" if balance >= 0 else "DEBT"

        print(f"      • {ts.tenant}")
        print(f"          Rent:        {format_currency(rent):>15}")
        print(f"          Bills share: {format_currency(ts.total_due_pln):>15}")
        print(f"          Total due:   {format_currency(total_due):>15}")
        print(f"          Paid:        {format_currency(total_paid):>15}")
        print(
            f"          Balance:     {format_currency(balance):>15} [{status}]"
        )

    all_transfers = [
        tr for tr in manager.transfers
        if tr.tenant in tenants_in_apt
        and tr.settlement_year == year
        and tr.settlement_month == month
    ]

    print_subsection_header("Transfers Received")

    if all_transfers:
        for tr in all_transfers:
            print(
                f"      • {tr.tenant:<25} "
                f"{format_currency(tr.amount_pln):>15}  "
                f"Date: {tr.date}"
            )
    else:
        print("      (no transfers for this period)")

    total_received = sum(tr.amount_pln for tr in all_transfers)
    total_rent = sum(t.rent_pln for t in tenants_in_apt.values())
    total_due_all = total_rent + settlement.total_due_pln
    overall_balance = total_received - total_due_all

    print(f"\n      {'TOTAL RECEIVED':<20} {format_currency(total_received):>15}")
    print(f"      {'TOTAL DUE':<20} {format_currency(total_due_all):>15}")
    print(f"      {'BALANCE':<20} {format_currency(overall_balance):>15}")

    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    parameters = Parameters()
    manager = Manager(parameters)

    if len(sys.argv) == 4:
        display_monthly_settlement(
            manager,
            sys.argv[1],
            int(sys.argv[2]),
            int(sys.argv[3]),
        )
    else:
        display_apartments(manager)
        display_tenants(manager)
        print(f"\n{'=' * 70}\n")
        