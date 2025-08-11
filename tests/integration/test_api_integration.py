import uuid
import pytest
from client import api_client

def test_end_to_end_booking():
    """ 
    Requires the mock server running at localhost:8547 and BOOKING_API_TOKEN available
    (api_client loads .env automatically if present).
    Flow: check availability -> create booking -> get booking -> update -> cancel
    """
    visit_date = "2025-08-10"

    # Availability
    availability = api_client.availability_search(visit_date=visit_date, party_size=2)
    slots = availability.get("available_slots", [])
    assert isinstance(slots, list)
    assert len(slots) >= 0

    # Pick an available date
    chosen = None
    for s in slots:
        if s.get("available"):
            chosen = s["time"]
            break

    if not chosen:
        pytest.skip(f"No available slots on {visit_date} for party size 2; can't run integration booking")

    # Create booking
    unique_email = f"test+{uuid.uuid4().hex[:6]}@example.com"
    customer = {"first_name": "Test", "surname": "User", "email":unique_email}
    resp = api_client.create_booking(visit_date=visit_date, visit_time=chosen, party_size=2,
                                     customer=customer, special_requests="special requests")
    assert "booking_reference" in resp
    booking_ref = resp["booking_reference"]

    try:
        # Get booking
        info = api_client.get_booking(booking_reference=booking_ref)
        assert info["booking_reference"] == booking_ref
        assert info["visit_date"] == visit_date

        # Update booking
        updated = api_client.update_booking(booking_reference=booking_ref, updates={"PartySize":3})
        assert updated.get("status") in ("updated", "confirmed")

        # Cancel booking
        cancelled = api_client.cancel_booking(booking_reference=booking_ref, reason_id=1)
        assert cancelled.get("status") == "cancelled"
    finally:
        # Clean up
        try:
            api_client.cancel_booking(booking_reference=booking_ref, reason_id=1)
        except Exception as e:
            print(e)
