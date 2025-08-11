from client.api_client import availability_search, create_booking, get_booking, update_booking, cancel_booking

import re

def detect_intent(text: str):
    """ 
    Function to detect intent 
    """
    t = text.lower()
    if "availability" in t or "available" in t:
        return "check_availability"
    if re.search(r"\b(book|reserve|i'd like to book|i want to book)\b", t):
        return "book"
    if re.search(r"\b(what time is my)\b", t):
        return "get_booking"
    if re.search(r"\b(change|modify|move)\b", t):
        return "modify_booking"
    if re.search(r"\b(cancel|cancel my)\b", t):
        return "cancel_booking"
    if re.search(r"\b(help|what can you do)\b", t):
        return "help"
    return "unknown"


class Conversation:
    def __init__(self):
        self.state = {"intent": None, "slots": {}, "last_booking_ref": None}

    def handle(self, text):
        intent = detect_intent(text)
        if intent == "unknown" and not self.state["intent"]:
            return "Sorry, I didn't understand. You can ask to check availability, book, view, modify or cancel a booking."

        # 1. Availability Search
        if intent == "check_availability" or self.state["intent"] == "check_availability":
            self.state["intent"] = "check_availability"
            # ask for date/party if missing
            slots = self.state["slots"]
            if "visit_date" not in slots:
                return "Sure — what date would you like (YYYY-MM-DD)?"
            if "party_size" not in slots:
                return "How many people is the booking for?"
            # call API
            try:
                resp = availability_search(slots["visit_date"], int(slots["party_size"]))
                # format available slots summary
                slots_list = resp.get("available_slots", [])
                if not slots_list:
                    return f"No slots available on {slots['visit_date']} for {slots['party_size']} people."
                times = [s["time"] for s in slots_list if s["available"]]
                return f"Available times on {slots['visit_date']}: {', '.join(times)}"
            except Exception as e:
                return f"API error: {e}"

        # 2. Create new booking
        if intent == "book" or self.state["intent"] == "book":
            self.state["intent"] = "book"
            slots = self.state["slots"]

            for slot in ("visit_date", "visit_time", "party_size"):
                if slot not in slots:
                    pretty = {"visit_date":"date (YYYY-MM-DD)","visit_time":"time (HH:MM:SS)","party_size":"party size (number)"}
                    return f"Please provide {pretty[slot]}."
            # make booking
            try:
                customer = {}
                if "first_name" in slots:
                    customer["FirstName"] = slots["first_name"]
                if "surname" in slots:
                    customer["Surname"] = slots["surname"]
                resp = create_booking(slots["visit_date"], slots["visit_time"], int(slots["party_size"]), customer=customer, 
                                      special_requests=slots.get("special_requests"))
                self.state["last_booking_ref"] = resp.get("booking_reference")
                self.state["slots"].clear()
                self.state["intent"] = None
                return f"Booking confirmed: {resp.get('booking_reference')} on {resp.get('visit_date')} at {resp.get('visit_time')}"
            except Exception as e:
                return f"Booking error: {e}"

        # 3. Get booking details
        if intent == "get_booking":
            # ask for booking reference if not present
            ref = re.search(r"\b([A-Z0-9]{6,8})\b", text)
            if ref:
                booking_ref = ref.group(1)
            else:
                booking_ref = self.state.get("last_booking_ref")
            if not booking_ref:
                return "Please provide your booking reference (e.g. ABC1234)."
            try:
                resp = get_booking(booking_ref)
                return f"Booking {resp['booking_reference']}: {resp['visit_date']} at {resp['visit_time']} for {resp['party_size']} people. Status: {resp['status']}"
            except Exception as e:
                return f"Error fetching booking: {e}"

        # 4. Modify/Update booking
        if intent == "modify_booking":
            ref = re.search(r"\b([A-Z0-9]{6,8})\b", text)
            if not ref and not self.state.get("last_booking_ref"):
                return "Please provide your booking reference to modify the booking."
            booking_ref = ref.group(1) if ref else self.state.get("last_booking_ref")
            updates = {}
            m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            if m:
                updates["VisitDate"] = m.group(1)
            m2 = re.search(r"(\d{2}:\d{2}:\d{2})", text)
            if m2:
                updates["VisitTime"] = m2.group(1)
            m3 = re.search(r"(\b\d+\b)\s*(people|person|guests)?", text)
            if m3:
                updates["PartySize"] = m3.group(1)
            if not updates:
                return "What would you like to change? (date YYYY-MM-DD, time HH:MM:SS or party size)"
            try:
                resp = update_booking(booking_ref, updates)
                return f"Update success: {resp.get('message','updated')}"
            except Exception as e:
                return f"Update error: {e}"

        # 5. Cancel booking
        if intent == "cancel_booking":
            ref = re.search(r"\b([A-Z0-9]{6,8})\b", text)
            if not ref and not self.state.get("last_booking_ref"):
                return "Please provide your booking reference to cancel."
            booking_ref = ref.group(1) if ref else self.state.get("last_booking_ref")
            # default reason 1
            try:
                resp = cancel_booking(booking_ref, reason_id=1)
                return f"Cancelled booking {resp.get('booking_reference')}. Reason: {resp.get('cancellation_reason')}"
            except Exception as e:
                return f"Cancel error: {e}"

        return "Sorry, I couldn't handle that request."
