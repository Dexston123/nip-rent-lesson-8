import time
import pytest

from src.manager import Manager
from src.models import Apartment, Parameters, Tenant


def _create_n_apartments(n: int) -> dict:
    return {
        f"apart-{i}": Apartment(
            key=f"apart-{i}",
            name=f"Apart {i}",
            area_m2=100.0,
            location=f"{i} Main St",
            rooms={},
        )
        for i in range(n)
    }


def _create_n_tenants(n: int, m: int) -> dict:
    return {
        f"tenant-{i}": Tenant(
            name=f"Tenant {i}",
            apartment=f"apart-{i % m}",
            room="room-example",
            deposit_pln=0.0,
            rent_pln=0.0,
            date_agreement_from="2025-01-01",
            date_agreement_to="2025-12-31",
        )
        for i in range(n)
    }


def test_search_for_apartment_large_dataset():
    allowed_search_time_ms = 1
    n_apartments = 100_000

    manager = Manager(Parameters())
    manager.apartments = _create_n_apartments(n_apartments)

    existing_key = "apart-80901"
    missing_key = "apart-1000000"

    start = time.perf_counter()
    result_ok = manager.get_apartment(existing_key)
    ok_time_ms = (time.perf_counter() - start) * 1e3

    start = time.perf_counter()
    result_fail = manager.get_apartment(missing_key)
    fail_time_ms = (time.perf_counter() - start) * 1e3

    assert isinstance(result_ok, Apartment)
    assert result_fail is None

    assert ok_time_ms < allowed_search_time_ms, (
        f"Existing apartment search took {ok_time_ms:.3f}ms"
    )
    assert fail_time_ms < allowed_search_time_ms, (
        f"Missing apartment search took {fail_time_ms:.3f}ms"
    )


def test_check_tenants_apartment_keys_large_dataset():
    pytest.skip(
        reason=(
            "Performance test skipped by default"
        )
    )

    allowed_create_time_s = 10
    allowed_check_time_ms = 10

    n_apartments = 10_000
    n_tenants = 1_000_000

    manager = Manager(Parameters())

    start = time.perf_counter()
    manager.apartments = _create_n_apartments(n_apartments)
    manager.tenants = _create_n_tenants(n_tenants, n_apartments + 1)
    create_time_s = time.perf_counter() - start

    start = time.perf_counter()
    result = manager.check_tenants_apartment_keys()
    check_time_ms = (time.perf_counter() - start) * 1e3

    assert result is False

    assert check_time_ms < allowed_check_time_ms, (
        f"Tenant validation took {check_time_ms:.3f}ms"
    )
    assert create_time_s < allowed_create_time_s, (
        f"Data creation took {create_time_s:.3f}s"
    )