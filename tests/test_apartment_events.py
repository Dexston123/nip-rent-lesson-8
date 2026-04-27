"""Tests for apartment events reporting."""

import pytest

from src.manager import Manager
from src.models import ApartmentEvent, Parameters


def test_apartment_events_report():
    """Test filtering and validation of apartment events."""
    manager = Manager(Parameters())
    manager.load_additional_data()

    manager.apartment_events = [
        ApartmentEvent(
            date="2025-01-01",
            apartment="apart-polanka",
            description="Broken window",
            solved=False,
        ),
        ApartmentEvent(
            date="2025-01-02",
            apartment="apart-polanka",
            description="Leak fixed",
            solved=True,
        ),
        ApartmentEvent(
            date="2025-01-03",
            apartment="other-apartment",
            description="Other issue",
            solved=False,
        ),
    ]

    events = manager.generate_apartment_events_report("apart-polanka")
    assert len(events) == 1
    assert events[0].description == "Broken window"

    events = manager.generate_apartment_events_report(
        "apart-polanka", only_unsolved=False
    )
    assert len(events) == 2

    with pytest.raises(ValueError):
        manager.generate_apartment_events_report("invalid-key")