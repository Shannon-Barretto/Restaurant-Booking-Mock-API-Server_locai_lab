from agent.dialog_manager import Conversation

# Test: check availability
def test_check_availability(monkeypatch):
    # mock availability_search to simulate API response
    def mock_availability(date, party_size):
        return {
            "restaurant": "TheHungryUnicorn",
            "visit_date": date,
            "party_size": party_size,
            "available_slots": [
                {"time": "19:00:00", "available": True, "max_party_size": 8, "current_bookings": 0}
            ],
            "total_slots":1
        }
    monkeypatch.setattr("agent.dialog_manager.availability_search", mock_availability)

    conv = Conversation()

    r = conv.handle("I want to check availability")
    assert "what date" in r.lower()

    conv.state["slots"]["visit_date"] = "2025-08-10"
    r = conv.handle("2025-08-10")
    assert "how many people" in r.lower()

    conv.state["slots"]["party_size"] = "2"
    r = conv.handle("2")
    assert "available times" in r.lower()
    assert "19:00:00" in r


# Test: create booking
def test_create_booking(monkeypatch):
    # Moch create_booking returns a typical success payload
    def mock_create(visit_date, visit_time, party_size, customer=None, special_requests=None, channel_code="ONLINE"):
        return {
            "booking_reference": "ABC1234",
            "booking_id": 1,
            "restaurant": "TheHungryUnicorn",
            "visit_date": visit_date,
            "visit_time": visit_time,
            "party_size": party_size,
            "status": "confirmed",
        }

    monkeypatch.setattr("agent.dialog_manager.create_booking", mock_create)

    conv = Conversation()
    conv.state["intent"] = "book"
    conv.state["slots"] = {
        "visit_date": "2025-08-10",
        "visit_time": "19:00:00",
        "party_size": "2",
        "first_name": "Alice",
        "surname": "Doe"
    }

    resp = conv.handle("book")  
    assert "Booking confirmed" in resp
    assert conv.state["last_booking_ref"] == "ABC1234"
    # slots should be cleared after booking
    assert conv.state["slots"] == {}


# Test: get booking
def test_get_booking(monkeypatch):
    def mock_get(ref):
        return {
            "booking_reference": ref,
            "booking_id": 1,
            "restaurant": "TheHungryUnicorn",
            "visit_date": "2025-08-10",
            "visit_time": "19:00:00",
            "party_size": 2,
            "status": "confirmed",
        }
    monkeypatch.setattr("agent.dialog_manager.get_booking", mock_get)

    conv = Conversation()
    # pass an utterance that contains a booking ref -> detect_intent should return get_booking
    resp = conv.handle("What time is my booking ABC1234?")
    assert "Booking ABC1234" in resp
    assert "19:00:00" in resp


# Test: update booking
def test_update_booking(monkeypatch):
    def mock_update(ref, updates):
        return {
            "booking_reference": ref,
            "booking_id": 1,
            "restaurant": "TheHungryUnicorn",
            "updates": updates,
            "status": "updated",
            "message": f"Booking {ref} has been successfully updated"
        }
    monkeypatch.setattr("agent.dialog_manager.update_booking", mock_update)

    conv = Conversation()
    resp = conv.handle("Please change booking ABC1234 to 20:00:00")
    assert "success" in resp.lower() or "updated" in resp.lower()


# Test: cancel booking
def test_cancel_booking(monkeypatch):
    def mock_cancel(ref, reason_id=1):
        return {
            "booking_reference": ref,
            "booking_id": 1,
            "restaurant": "TheHungryUnicorn",
            "cancellation_reason_id": reason_id,
            "cancellation_reason": "Customer Request",
            "status": "cancelled",
            "message": f"Booking {ref} has been successfully cancelled"
        }
    monkeypatch.setattr("agent.dialog_manager.cancel_booking", mock_cancel)

    conv = Conversation()
    resp = conv.handle("Please cancel my booking ABC1234")
    assert "cancelled" in resp.lower() or "successfully cancelled" in resp.lower()


# Test: Error handling
def test_create_booking_error_handling(monkeypatch):
    # simulate create_booking raising an HTTP error (or any exception)
    def mock_create_raise():
        raise Exception("422 Unprocessable Entity")
    monkeypatch.setattr("agent.dialog_manager.create_booking", mock_create_raise)

    conv = Conversation()
    conv.state["intent"] = "book"
    conv.state["slots"] = {
        "visit_date": "2025-08-10",
        "visit_time": "19:00:00",
        "party_size": "10",
    }

    resp = conv.handle("confirm")
    assert "Booking error" in resp or "error" in resp.lower()
