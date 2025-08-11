import os
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BASE = "http://localhost:8547"
RESTAURANT = "TheHungryUnicorn"
TOKEN = os.getenv("BOOKING_API_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "BOOKING_API_TOKEN is not set. Create a .env file in the project root with "
        "BOOKING_API_TOKEN=<your_token> or export the environment variable."
    )

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/x-www-form-urlencoded",
}


# create a session with retries
def _create_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "POST", "PATCH"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session

_session = _create_session()
DEFAULT_TIMEOUT = 10  # seconds


def _post(path, data=None, timeout=DEFAULT_TIMEOUT):
    url = f"{BASE}{path}"
    resp = _session.post(url, data=data or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _get(path, timeout=DEFAULT_TIMEOUT):
    url = f"{BASE}{path}"
    resp = _session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _patch(path, data=None, timeout=DEFAULT_TIMEOUT):
    url = f"{BASE}{path}"
    resp = _session.patch(url, data=data or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

# --------------------------Public helpers--------------------------

def availability_search(visit_date: str, party_size: int, channel_code="ONLINE"):
    path = f"/api/ConsumerApi/v1/Restaurant/{RESTAURANT}/AvailabilitySearch"
    data = {"VisitDate": visit_date, "PartySize": party_size, "ChannelCode": channel_code}
    return _post(path, data=data)


def create_booking(visit_date, visit_time, party_size, customer=None, special_requests=None, channel_code="ONLINE"):
    path = f"/api/ConsumerApi/v1/Restaurant/{RESTAURANT}/BookingWithStripeToken"
    payload = {
        "VisitDate": visit_date,
        "VisitTime": visit_time,
        "PartySize": party_size,
        "ChannelCode": channel_code
    }
    if special_requests:
        payload["SpecialRequests"] = special_requests

    # Flatten customer dict to form-style keys like Customer[FirstName]
    for k, v in customer.items():
        payload[f"Customer[{k}]"] = v

    return _post(path, data=payload)


def get_booking(booking_reference):
    path = f"/api/ConsumerApi/v1/Restaurant/{RESTAURANT}/Booking/{booking_reference}"
    return _get(path)


def update_booking(booking_reference, updates: dict):
    path = f"/api/ConsumerApi/v1/Restaurant/{RESTAURANT}/Booking/{booking_reference}"
    return _patch(path, data=updates)


def cancel_booking(booking_reference, reason_id=1):
    path = f"/api/ConsumerApi/v1/Restaurant/{RESTAURANT}/Booking/{booking_reference}/Cancel"
    data = {"micrositeName": RESTAURANT, "bookingReference": booking_reference, "cancellationReasonId": reason_id}
    return _post(path, data=data)
