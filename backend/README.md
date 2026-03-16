# Rail Management System — Phase 2

## Project Structure

```
submission/
│
├── backend/
│   ├── api.py                    # REST API (JSON, Bearer token, /api/v1/...)
│   ├── app.py                    # Template-based Flask app (browser UI)
│   └── templates/
│       ├── login.html
│       ├── register.html
│       ├── passenger_dashboard.html
│       ├── book.html
│       ├── my_tickets.html
│       ├── admin_dashboard.html
│       └── staff_dashboard.html
│
├── swagger.yaml                  # OpenAPI 3.0 spec for all API endpoints
├── schema.sql                    # Full database schema with triggers and views
├── seed.sql                      # Admin user + sample stations and routes
├── test_double_booking.py        # Script demonstrating rollback via trigger
├── requirements.txt
├── .env.example                  # Environment variable template
├── README.md
├── Backend_Explanation.pdf       # Student-written explanation document
└── media/
    └── rollback.log              # Sample rollback log showing trigger behavior
```

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Create your .env file**
```bash
cp .env.example .env
```
Edit `.env` and set a real `SECRET_KEY`:
```
SECRET_KEY=some_long_random_string_change_this
DB_PATH=db.db
```

**3. Initialise the database**
```bash
sqlite3 db.db < schema.sql
```

**4. Seed initial data (stations, sample route, admin user)**
```bash
sqlite3 db.db < seed.sql
```

**5. Generate a real bcrypt hash for the admin password**

The hash in `seed.sql` is a placeholder. Run:
```python
import bcrypt
print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())
```
Then update the admin row directly:
```bash
sqlite3 db.db "UPDATE User SET password='<hash>' WHERE cnic='1234567890123';"
```

---

## Running the REST API

```bash
cd backend
python api.py
```

Base URL: `http://localhost:5000/api/v1`

All protected endpoints require:
```
Authorization: Bearer <token>
```

Get a token from `POST /api/v1/login`.

---

## Running the Browser UI

```bash
cd backend
python app.py
```

Open `http://localhost:5000` in a browser.

---

## API Endpoint Summary

| Method | Endpoint                      | Role      |
|--------|-------------------------------|-----------|
| POST   | /api/v1/register              | —         |
| POST   | /api/v1/login                 | —         |
| GET    | /api/v1/trains                | any       |
| GET    | /api/v1/passenger/tickets     | passenger |
| POST   | /api/v1/passenger/book        | passenger |
| GET    | /api/v1/admin/dashboard       | admin     |
| POST   | /api/v1/admin/staff           | admin     |
| POST   | /api/v1/admin/staff/shift     | admin     |
| GET    | /api/v1/admin/stations        | admin     |
| POST   | /api/v1/admin/stations        | admin     |
| GET    | /api/v1/admin/trains          | admin     |
| POST   | /api/v1/admin/trains          | admin     |
| GET    | /api/v1/admin/routes          | admin     |
| POST   | /api/v1/admin/routes          | admin     |
| POST   | /api/v1/admin/routes/station  | admin     |
| GET    | /api/v1/staff/dashboard       | staff     |

---

## Transaction Scenarios

**Scenario 1 — Ticket Booking** (`POST /api/v1/passenger/book`)
- `BEGIN TRANSACTION` → INSERT Payment → INSERT Ticket → UPDATE Seat
- If the `ensure_no_double_booking` trigger fires, SQLite raises ABORT, Python catches it, `ROLLBACK` executes, and the event is written to `rollback.log`

**Scenario 2 — Staff Creation** (`POST /api/v1/admin/staff`)
- `BEGIN TRANSACTION` → INSERT User → INSERT Staff → INSERT Staff_Assignment × 8
- If the `ensure_40_hour_rule` trigger fires on any assignment, SQLite raises ABORT, all inserts are rolled back atomically, and the event is logged

---

## Testing Rollback Behavior

```bash
python test_double_booking.py
```

Attempt 1 succeeds. Attempt 2 is blocked by the `ensure_no_double_booking` trigger.
Check `rollback.log` for the logged entry.

---

## Viewing the Swagger Spec

Open `swagger.yaml` in [https://editor.swagger.io](https://editor.swagger.io) to render the full interactive API documentation.
