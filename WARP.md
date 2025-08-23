# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Repository overview
- Stack: Python + Flask web app with sqla-wrapper (SQLAlchemy wrapper) for persistence. Tests use pytest. Default DB is SQLite; psycopg2 is included for Postgres compatibility.
- Entry points: main.py (defines Flask app and routes). Data model in models.py.
- Tests: tests/test_main.py uses an in-memory SQLite database.

Common commands
Setup
- Create a virtualenv and install dependencies
```bash path=null start=null
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# for running tests
pip install -U pytest
```

Run the app (development)
- Using Python’s built-in server
```bash path=null start=null
# Optional: point to a specific DB; defaults to sqlite:///localhost.sqlite
export DATABASE_URL="sqlite:///localhost.sqlite"
python main.py
```
- Using gunicorn
```bash path=null start=null
# DATABASE_URL can be set to Postgres as well, e.g., {{POSTGRES_URL}}
# Example placeholder (replace with your DSN): export DATABASE_URL="{{POSTGRES_URL}}"
gunicorn -b 0.0.0.0:8000 main:app
```

Run tests
```bash path=null start=null
# run entire suite
pytest -q

# run a single test function
pytest -q tests/test_main.py::test_index_not_logged_in

# filter by keyword
pytest -q -k "profile and password"
```

Quick DB reset (SQLite default)
```bash path=null start=null
# remove local SQLite file used by default configuration
rm -f localhost.sqlite
```

High-level architecture and flow
- Persistence (models.py)
  - db is an sqla_wrapper.SQLAlchemy bound to DATABASE_URL (defaults to sqlite:///localhost.sqlite).
  - User model fields: id (PK), name, email, secret_number (stored as string), password (SHA-256 hash), session_token, inactive (boolean).
- Web app (main.py)
  - App initialization calls db.create_all() at import time to ensure tables exist for the configured DB.
  - Authentication/session: not using Flask’s session; instead, a UUID session_token is written to the User row and set as an HTTP-only cookie. Routes retrieve the current user by querying on session_token.
  - Game flow:
    - POST /login: hashes provided password (SHA-256), creates user if new, sets session_token cookie, and generates a per-user secret_number in [1,30].
    - GET/POST /: index page. GET renders template with optional message. POST validates a numeric guess ∈ [1,30]; compares to user.secret_number. On success, it regenerates secret_number and returns recent wrong guesses. A module-level list wrong_guess records recent guesses.
  - Profile management:
    - GET /profile: requires session; otherwise redirects to index with a message.
    - GET/POST /edit_profile: allows updating name, email, and password (min length 6; SHA-256 hashed). Messages returned via templates.
    - GET/POST /delete: soft-deletes by setting inactive=True and clears the session cookie.
  - User directory:
    - GET /users_list: lists all users where inactive=False.
    - GET /user/<user_id>: shows details for a specific user.

Notable quirks and gotchas
- Route name mismatch with tests: tests/test_main.py issues GET to "/user_list" but the app exposes "/users_list" (plural). Be aware when running/fixing tests.
- Global state: wrong_guess is a module-level list. Under multi-worker servers (e.g., gunicorn with >1 worker) it’s per-process and shared across users within a worker. It’s not persisted in the DB.
- Schema types: secret_number is stored as a string though compared numerically in handlers. Conversions are performed at usage sites.
- App initialization side effects: db.create_all() runs at import time in main.py. This can affect test startup and production boot behavior depending on DATABASE_URL.
- README.md contains unresolved merge conflict markers. Review before relying on it for guidance.

Environment configuration
- DATABASE_URL controls the backing database.
  - SQLite examples:
    - File: sqlite:///localhost.sqlite
    - In-memory (tests use this via fixture): sqlite:///:memory:
  - Postgres example (placeholder): postgresql+psycopg2://{{DB_USER}}:{{DB_PASSWORD}}@{{DB_HOST}}:{{DB_PORT}}/{{DB_NAME}}

Existing docs and rules
- README.md: brief description of automated testing practice and a guessing-game/password-hashing exercise, but currently has conflict markers.
- No CLAUDE.md, Cursor rules, or Copilot instructions found in this repository.

