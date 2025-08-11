from agent.dialog_manager import Conversation

import re

def extract_slots_from_text(text, conv):
    """
    Extract visit_date, visit_time and party_size from a user text message.
    Prioritise date/time extraction first. Only set party_size if the text
    clearly indicates party size (e.g., 'for 4', 'party of 3' or the text is just '4').
    """
    
    # Detect date
    date_m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if date_m:
        conv.state["slots"]["visit_date"] = date_m.group(1)

    # Detect time
    time_m = re.search(r"\b(\d{2}:\d{2}:\d{2})\b", text)
    if time_m:
        conv.state["slots"]["visit_time"] = time_m.group(1)

    # party size detection - prefer explicit phrases
    party_m = re.search(r'(?:for|party of|party|for a party of|guests|people|persons)\s+(\d{1,2})\b', text, re.I)
    if party_m:
        conv.state["slots"]["party_size"] = party_m.group(1)
        return
    
    # Email detection
    email_m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_m:
        conv.state["slots"]["email"] = email_m.group(0)

    # Mobile no. detection
    if "mobile no:" in text:
        conv.state["slots"]["mobile"] = text.split(":")[1].strip()

    # special requests extraction
    special_m = re.search(r"(special requests?[:\-]?\s*)(.*)", text, re.I)
    if special_m:
        conv.state["slots"]["special_requests"] = text.split(":")[1].strip()

    name_m = re.search(r"\bfull name is\s+([A-Z][a-zA-Z]+)\s+([A-Z][a-zA-Z]+)\b", text, re.I)
    if name_m:
        conv.state["slots"]["first_name"], conv.state["slots"]["surname"] = name_m.group(1), name_m.group(2)


    # if the user response is just a small number (e.g., they replied "2"), accept it
    stripped = text.strip()
    if re.fullmatch(r'\d{1,2}', stripped):
        # treat as party size only if it's not a date/time (already handled above)
        # and within a reasonable range
        num = int(stripped)
        if 1 <= num <= 20:
            conv.state["slots"]["party_size"] = str(num)
        return


def main():
    print("Hello — I'm the HungryUnicorn booking assistant. Type 'help' for options.")
    conv = Conversation()
    while True:
        text = input("> ").strip()
        if text.lower() in ("quit","exit"):
            print("Bye!")
            break
        if conv.state["intent"]:
            extract_slots_from_text(text, conv)
            # also detect names like "my name is John Smith"
            if "name is" in text.lower():
                parts = text.split("is", 1)[1].strip()
                if " " in parts:
                    first, last = parts.split(" ", 1)
                    conv.state["slots"]["first_name"] = first
                    conv.state["slots"]["surname"] = last
            resp = conv.handle(text)
            print(resp)
        else:
            resp = conv.handle(text)
            print(resp)

if __name__ == "__main__":
    main()
