from agent.dialog_manager import detect_intent

def test_detect_intent_book():
    assert detect_intent("I want to book a table") == "book"
    assert detect_intent("I'd like to book a table for 4 people next Friday at 7pm.") == "book"
    assert detect_intent("Can I check availability?") == "check_availability"
    assert detect_intent("Can you show me availability for this weekened?") == "check_availability"
    assert detect_intent("please cancel my booking") == "cancel_booking"
    assert detect_intent("how do I modify my booking?") == "modify_booking"
    assert detect_intent("What time is my booking ABC1234") == "get_booking"
    assert detect_intent("What time is my reservation on Saturday?") == "get_booking"
    assert detect_intent("Please cancel my reservation for tomorrow.") == "cancel_booking"
    assert detect_intent("soudhf awiuvhipsuv hsvh d ") == "unknown"
