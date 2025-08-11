# Overview

This project implements a small, deterministic Python terminal agent that integrates with a restaurant booking API (mock server in `localhost:8547`). The agent supports the common user stories:

- **As a user, I want to check availability** for a given date and party size so I can choose a time.  
- **As a user, I want to book a table** (date, time, party size, name, optional special requests).  
- **As a user, I want to view my booking** using a booking reference.  
- **As a user, I want to modify or cancel my booking.**

The repository contains:
- `agent/dialog_manager.py`: small rule-based conversation manager and intent detector.  
- `client/api_client.py`: thin API client with retries, timeouts and auth.  
- `run_terminal.py`: terminal agent entrypoint (run the conversation loop).  
- `tests/`: unit and integration tests demonstrating expected behaviour.

# Quickstart

1. Ensure prerequisites (see below).  
2. Start the mock server (see *Start mock server*).  
3. Set the booking API token environment variable.  

```bash
# from project root
python -m app   # Start the upstream/mock server (see Start mock server)
python run_terminal.py
```

# Prereqs

- **Python 3.10+**  

```bash
pip install -r requirements.txt
```

# Start mock server: `python -m app` (link to upstream repo)

The mock server expected by the tests and local development runs on `http://localhost:8547`. If you have a specific upstream mock repo, replace the following placeholder with that repository's README or URL:

`<UPSTREAM_MOCK_SERVER_REPO_URL_HERE>`

Start the server from the project root with:

```bash
python -m app
```

and verify it responds on `http://localhost:8547`.

# Set env var: `export BOOKING_API_TOKEN="..."`

The API client expects a bearer token in the environment variable `BOOKING_API_TOKEN`. Example (Linux/macOS):

```bash
export BOOKING_API_TOKEN="your_token_here"
```

If the token is missing the client will fail fast with a clear RuntimeError. Do not commit tokens to source control.

# Run terminal agent: `python run_terminal.py`

This launches the simple REPL-style conversational agent. Example session flow:

- "I want to check availability"  
- Agent asks: "what date would you like (YYYY-MM-DD)?"  
- Provide date and party size and continue with booking flow.

# Design Rationale

## Why Python / custom agent

- **Speed of development:** small codebase and standard Python libs let us iterate quickly.  
- **Clarity:** rule-based intent detection and an explicit `Conversation` state make behaviour predictable and testable.  
- **Testability:** deterministic flows are easy to unit- and integration-test (see `tests/`).

## Scaling path

- Move ephemeral state from memory to **Redis** (concurrency / multi-process safety).  
- Persist bookings and audit logs to **Postgres** for analytics and recovery.  
- Containerize components (Docker) and orchestrate with Kubernetes (or simpler Docker Compose).  
- Add rotating short-lived tokens and an OAuth-based client for stronger auth.  
- Add monitoring/metrics (Prometheus + Grafana), request tracing (OpenTelemetry).

## Trade-offs

- **Chosen:** small, deterministic agent for reliability and simple QA. Minimal external ML/LLM usage to avoid non-deterministic outputs.  
- **Trade-off:** not as flexible as a full LLM-driven assistant, but much easier to reason about and to reproduce in tests.

# Architecture diagram

Small ASCII diagram (replace with PNG in docs if you prefer):

```
+-------------+     HTTP      +---------------+    
|  Terminal / | <---------->  |  Mock Booking | 
|  Web client |               |  Server @8547 | 
+-------------+               +---------------+ 
        ^                             ^                 
        |                             |                 
   agent/dialog_manager.py      client/api_client.py 
        |                             |
        +------ run_terminal.py ------+
```

# Validation & error handling

This project takes an explicit, defensive approach. Please include the following behaviours (these are implemented or should be mirrored in the code):

## Client-side validation (input before API call)
- **Date format:** must match `YYYY-MM-DD` (use `\d{4}-\d{2}-\d{2}`) and ideally validate with `datetime.date.fromisoformat()`.
- **Time format:** must match `HH:MM:SS` (use `\d{2}:\d{2}:\d{2}`) and validate with `datetime.time.fromisoformat()`.
- **Party size:** integer, reasonable range `1–20`. Reject and prompt the user if outside range.
- Reject invalid inputs **before** calling the API and show clear messages to the user.

## API error handling
- Wrap all HTTP requests in `try/except` blocks.  
- On `requests.HTTPError` (4xx/5xx), capture `resp.json().get('detail')` (if available) and return a user-friendly message like: "Booking failed: [detail] — please check your input or try again later."  
- Avoid exposing raw tracebacks to end users; log them server-side instead.

## Retries & timeouts
- Use reasonable timeouts for external calls (default **5–10s**; current implementation uses `DEFAULT_TIMEOUT = 10`).  
- Retry transient network errors (3 attempts) with exponential backoff (the `requests` session in `client/api_client.py` uses `urllib3.Retry` configured to retry on 5xx errors).

## Input sanitation
- Strip whitespace from all string fields before sending.  
- Limit lengths (e.g., `special_requests` <= **500 chars**).  
- Validate and canonicalize names and email if supplied.  

## Auth
- Token is read from `BOOKING_API_TOKEN` environment variable.  
- If missing, the client should `raise RuntimeError` and the app should exit with a clear error: "BOOKING_API_TOKEN is not set. Create a .env or export the variable."  

# API integration notes

Base URL and headers (see `client/api_client.py`):

- `BASE = http://localhost:8547` (override for production).  
- `HEADERS` include `Authorization: Bearer <TOKEN>` and `Content-Type: application/x-www-form-urlencoded`.

Endpoints used:

- `POST /api/ConsumerApi/v1/Restaurant/{RESTAURANT}/AvailabilitySearch`  
  Payload: `VisitDate`, `PartySize`, `ChannelCode`  
  Response: `available_slots` with `time` and `available` flags.

- `POST /api/ConsumerApi/v1/Restaurant/{RESTAURANT}/BookingWithStripeToken`  
  Payload: `VisitDate`, `VisitTime`, `PartySize`, `ChannelCode`, `SpecialRequests`, and `Customer[...]` form fields.  
  Response: includes `booking_reference`, `visit_date`, `visit_time`, `party_size`.

- `GET /api/ConsumerApi/v1/Restaurant/{RESTAURANT}/Booking/{booking_reference}`

- `PATCH /api/ConsumerApi/v1/Restaurant/{RESTAURANT}/Booking/{booking_reference}`

- `POST /api/ConsumerApi/v1/Restaurant/{RESTAURANT}/Booking/{booking_reference}/Cancel`

Implementation notes:
- The client uses a `requests.Session` with `urllib3.Retry` to handle retries and backoff.  
- Form-encoded payloads (`application/x-www-form-urlencoded`) are used for compatibility with the upstream mock.

# How to test (unit + integration)

- Unit tests (fast, isolated) live under `tests/unit/`. They use `monkeypatch` to stub API calls and exercise `dialog_manager` flows.
- Integration tests live under `tests/integration/` and require the mock server running at `localhost:8547` and a valid `BOOKING_API_TOKEN` in environment. Integration test (`test_end_to_end_booking`) runs the full flow: availability -> create -> get -> update -> cancel.

Run all tests:

```bash
# start mock server in another terminal: python -m app
pytest -q
```

CI recommendations:
- Run unit tests on every PR.  
- Run integration tests in a gated job that spins up the mock server (or uses a hosted test environment) and limits secrets exposure.

# Limitations & improvements

Current limitations:
- Rule-based intent detection — limited NLU (simple regexes).  
- In-memory conversation state (not shared across processes or restarts).  
- No rate-limiting or per-user authentication (beyond the single bearer token).  

Planned / suggested improvements:
- Replace rule-based NLU with a small intent classifier or a robust NLU package.  
- Persist conversation state to Redis and bookings to Postgres.  
- Add input forms and client-side validation in the web UI.  
- Harden integration tests to run inside CI with ephemeral mock instances.

# Security considerations

- **Secrets:** never commit `BOOKING_API_TOKEN` to VCS. Use environment variables or a secrets manager.  
- **Transport:** use HTTPS in production. Never send tokens over unencrypted HTTP.  
- **Logging:** avoid logging full request bodies that contain PII or tokens. Sanitize logs.  
- **Input validation/sanitization:** always validate types and length, and escape/normalize user inputs before storing or forwarding.  
- **Rate limiting and abuse:** add throttling for repeated booking attempts.

# License

This project is available under the **MIT License**. See `LICENSE` for full text.

---
