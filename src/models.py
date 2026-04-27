"""Data models for apartment rental system."""

import json
from typing import Dict, List

from pydantic import BaseModel


class Parameters(BaseModel):
    """Configuration parameters for file paths and limits."""

    apartments_json_path: str = "data/apartments.json"
    tenants_json_path: str = "data/tenants.json"
    transfers_json_path: str = "data/transfers.json"
    bills_json_path: str = "data/bills.json"
    tenants_blacklist_json_path: str = "data/tenants_blacklist.json"
    apartment_events_json_path: str = "data/apartment_events.json"

    max_transfer_pln: float = 4500.0
    max_refund_pln: float = 2500.0


class Room(BaseModel):
    """Room within an apartment."""

    name: str
    area_m2: float


class Apartment(BaseModel):
    """Apartment model."""

    key: str
    name: str
    location: str
    area_m2: float
    rooms: Dict[str, Room]

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str, "Apartment"]:
        """Load apartments from JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        assert isinstance(data, dict), "Expected a dictionary of apartments"

        return {
            key: Apartment(**apartment)
            for key, apartment in data.items()
        }


class Tenant(BaseModel):
    """Tenant model."""

    name: str
    apartment: str
    room: str
    rent_pln: float
    deposit_pln: float
    date_agreement_from: str
    date_agreement_to: str

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str, "Tenant"]:
        """Load tenants from JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        assert isinstance(data, dict), "Expected a dictionary of tenants"

        return {
            key: Tenant(**tenant)
            for key, tenant in data.items()
        }


class TenantBlacklistEntry(BaseModel):
    """Blacklist entry for a tenant."""

    tenant: str
    reason: str

    @staticmethod
    def from_json_file(file_path: str) -> List["TenantBlacklistEntry"]:
        """Load blacklist entries from JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        assert isinstance(data, list), "Expected a list of blacklist entries"

        return [
            TenantBlacklistEntry(**entry)
            for entry in data
        ]


class Transfer(BaseModel):
    """Money transfer made by a tenant."""

    amount_pln: float
    date: str
    settlement_year: int | None
    settlement_month: int | None
    tenant: str
    type: str | None = None

    @staticmethod
    def from_json_file(file_path: str) -> List["Transfer"]:
        """Load transfers from JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        assert isinstance(data, list), "Expected a list of transfers"

        return [
            Transfer(**transfer)
            for transfer in data
        ]


class Bill(BaseModel):
    """Bill associated with an apartment."""

    amount_pln: float
    date_due: str
    apartment: str
    settlement_year: int
    settlement_month: int
    type: str

    @staticmethod
    def from_json_file(file_path: str) -> List["Bill"]:
        """Load bills from JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        assert isinstance(data, list), "Expected a list of bills"

        return [
            Bill(**bill)
            for bill in data
        ]


class ApartmentSettlement(BaseModel):
    """Settlement summary for an apartment."""

    key: str
    apartment: str
    month: int
    year: int
    total_due_pln: float
    total_transfers_pln: float = 0.0
    balance_pln: float = 0.0


class TenantSettlement(BaseModel):
    """Settlement summary for a tenant."""

    tenant: str
    apartment_settlement: str
    month: int
    year: int
    total_due_pln: float
    total_transfers_pln: float = 0.0
    balance_pln: float = 0.0


class ApartmentEvent(BaseModel):
    """Event related to an apartment."""

    date: str
    apartment: str
    amount_pln: float | None = None
    tenant: str | None = None
    description: str
    solved: bool = False

    @staticmethod
    def from_json_file(file_path: str) -> List["ApartmentEvent"]:
        """Load apartment events from JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        assert isinstance(data, list), "Expected a list of apartment events"

        return [
            ApartmentEvent(**event)
            for event in data
        ]