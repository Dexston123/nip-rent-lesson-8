"""Manager module responsible for apartment rental logic."""

from datetime import datetime
from typing import List

from src.models import (
    Apartment,
    ApartmentEvent,
    ApartmentSettlement,
    Bill,
    Parameters,
    Tenant,
    TenantBlacklistEntry,
    TenantSettlement,
    Transfer,
)


class Manager:
    """Main service class handling apartments, tenants, bills and settlements."""

    def __init__(self, parameters: Parameters):
        self.parameters = parameters
        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
        self.tenants_blacklist = []
        self.apartment_events = []
        self.load_data()

    def load_data(self):
        """Load base data from JSON files."""
        self.apartments = Apartment.from_json_file(
            self.parameters.apartments_json_path
        )
        self.tenants = Tenant.from_json_file(
            self.parameters.tenants_json_path
        )
        self.transfers = Transfer.from_json_file(
            self.parameters.transfers_json_path
        )
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)
        self.tenants_blacklist = TenantBlacklistEntry.from_json_file(
            self.parameters.tenants_blacklist_json_path
        )

    def load_additional_data(self):
        """Load additional apartment events."""
        self.apartment_events = ApartmentEvent.from_json_file(
            self.parameters.apartment_events_json_path
        )

    def generate_apartment_events_report(
        self, apartment_key: str, only_unsolved: bool = True
    ) -> List[ApartmentEvent]:
        """Return apartment events filtered by status."""
        if apartment_key not in self.apartments:
            raise ValueError("Apartment key does not exist")

        return [
            event
            for event in self.apartment_events
            if event.apartment == apartment_key
            and (not event.solved or not only_unsolved)
        ]

    def check_tenants_apartment_keys(self) -> bool:
        """Validate that all tenants reference existing apartments."""
        return all(
            tenant.apartment in self.apartments
            for tenant in self.tenants.values()
        )

    def get_apartment(self, apartment_key: str) -> Apartment | None:
        """Return apartment by key."""
        return self.apartments.get(apartment_key)

    def get_apartment_costs(
        self,
        apartment_key: str,
        year: int = None,
        month: int = None,
    ) -> float | None:
        """Calculate total costs for an apartment."""
        if month is not None and not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12")

        if apartment_key not in self.apartments:
            return None

        return sum(
            bill.amount_pln
            for bill in self.bills
            if bill.apartment == apartment_key
            and (year is None or bill.settlement_year == year)
            and (month is None or bill.settlement_month == month)
        )

    def get_settlement(
        self, apartment_key: str, year: int, month: int
    ) -> ApartmentSettlement | None:
        """Create apartment settlement."""
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12")

        if apartment_key not in self.apartments:
            return None

        total_cost = self.get_apartment_costs(
            apartment_key, year, month
        )

        if total_cost is None:
            return None

        return ApartmentSettlement(
            key=f"{apartment_key}-{year}-{month}",
            apartment=apartment_key,
            year=year,
            month=month,
            total_due_pln=total_cost,
        )

    def create_tenants_settlements(
        self, apartment_settlement: ApartmentSettlement
    ) -> List[TenantSettlement] | None:
        """Split apartment costs between tenants."""
        if not 1 <= apartment_settlement.month <= 12:
            raise ValueError("Month must be between 1 and 12")

        if apartment_settlement.apartment not in self.apartments:
            return None

        tenants = [
            tenant
            for tenant in self.tenants.values()
            if tenant.apartment == apartment_settlement.apartment
        ]

        if not tenants:
            return []

        return [
            TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_settlement.key,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                total_due_pln=(
                    apartment_settlement.total_due_pln / len(tenants)
                ),
            )
            for tenant in tenants
        ]

    def get_debtors(
        self, apartment_key: str, year: int, month: int
    ) -> List[str]:
        """Return tenants with unpaid balances."""
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12")

        settlement = self.get_settlement(apartment_key, year, month)
        if settlement is None:
            return []

        tenant_settlements = self.create_tenants_settlements(settlement)
        if tenant_settlements is None:
            return []

        output = []

        for ts in tenant_settlements:
            transfers = [
                transfer
                for transfer in self.transfers
                if self.tenants[transfer.tenant].name == ts.tenant
                and transfer.settlement_year == year
                and transfer.settlement_month == month
            ]

            total_paid = sum(t.amount_pln for t in transfers)

            if total_paid < ts.total_due_pln:
                output.append(ts.tenant)

        return output

    def calculate_tax(
        self, year: int, month: int, tax_rate: float
    ) -> float:
        """Calculate tax based on income."""
        total_income = sum(
            transfer.amount_pln
            for transfer in self.transfers
            if transfer.settlement_year == year
            and transfer.settlement_month == month
        )
        return round(total_income * tax_rate, 0)

    def check_deposits(self) -> float:
        """Check deposit balance."""
        total_deposits = 0.0
        total_due = 0.0

        for tenant in self.tenants.values():
            total_deposits += sum(
                transfer.amount_pln
                for transfer in self.transfers
                if self.tenants[transfer.tenant].name == tenant.name
                and transfer.type == "deposit"
            )
            total_due += tenant.deposit_pln

        return total_deposits - total_due

    def get_annual_balance(self, year: int) -> float:
        """Calculate annual balance."""
        total_income = sum(
            transfer.amount_pln
            for transfer in self.transfers
            if transfer.settlement_year == year
        )
        total_due = sum(
            bill.amount_pln
            for bill in self.bills
            if bill.settlement_year == year
        )
        return total_income - total_due

    def has_any_bills(
        self, apartment_key: str, year: int, month: int
    ) -> bool:
        """Check if apartment has bills for given period."""
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12")

        if apartment_key not in self.apartments:
            raise ValueError("Apartment key does not exist")

        return any(
            bill.apartment == apartment_key
            and bill.settlement_year == year
            and bill.settlement_month == month
            for bill in self.bills
        )

    def check_transfers_amount_range(self) -> bool:
        """Validate transfer amounts."""
        return all(
            -self.parameters.max_refund_pln
            <= transfer.amount_pln
            <= self.parameters.max_transfer_pln
            for transfer in self.transfers
        )

    def check_tenant_blacklist(self, tenant_name: str) -> bool:
        """Check if tenant is blacklisted."""
        return any(
            entry.tenant == tenant_name
            for entry in self.tenants_blacklist
        )

    def check_transfers_tenant(self) -> bool:
        """Validate transfers against tenant agreements."""
        for transfer in self.transfers:
            if transfer.tenant not in self.tenants:
                return False

            if (
                transfer.settlement_year is not None
                and transfer.settlement_month is not None
            ):
                tenant = self.tenants[transfer.tenant]

                agreement_from = datetime.strptime(
                    tenant.date_agreement_from, "%Y-%m-%d"
                ).date()
                agreement_to = datetime.strptime(
                    tenant.date_agreement_to, "%Y-%m-%d"
                ).date()

                if (
                    transfer.settlement_year < agreement_from.year
                    or transfer.settlement_year > agreement_to.year
                ):
                    return False

        return True