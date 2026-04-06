# Rail Management System — Phase 3

## 1. Project Overview

The **Rail Management System** is a full-stack web application that digitises train travel operations in Pakistan. It serves three distinct user roles — passengers, staff, and administrators — each with a tailored interface. Passengers can search trains, book seats, and view their ticket history. Staff can view their assigned shift schedules. Administrators manage the entire system: stations, trains, routes, staff accounts, and shift assignments.

**Domain:** Public railway ticketing and workforce management  
**Problem Solved:** Replaces manual/paper-based booking and scheduling with a role-gated digital platform backed by a transactional SQLite database that enforces business rules (no double-booking, 40-hour work-week cap) through triggers.

| Member | Role |
|--------|------|
| *(add team members here)* | |

**Group Number:** *(add group number)*

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Flask Jinja2 Templates + plain HTML/CSS/JS |
| Backend | Python 3, Flask |
| Database | SQLite 3 |
| Authentication | JWT (Bearer tokens) + Flask session cookies |
| Password Hashing | bcrypt |
| API Spec | OpenAPI 3.0 (swagger.yaml) |
| Environment Config | python-dotenv |

---

## 3. System Architecture

```
Browser
  │
  ├─► app.py  (port 5000, session-cookie auth, server-side HTML rendering)
  │         └─► renders templates/ → passenger/staff/admin dashboards
  │
  └─► api.py  (port 5000, /api/v1/*, Bearer token auth, JSON responses)
            └─► SQLite db.db (triggers, views, indexes)
```

`app.py` and `api.py` share the same SQLite database. `app.py` is the browser-facing UI; `api.py` is the machine-readable REST layer documented in `swagger.yaml`. Both enforce the same RBAC rules.

---

## 4. UI Examples

### Passenger Dashboard
After login the passenger sees a minimal, focused dashboard with three actions: **Book Ticket**, **My Tickets**, and **Logout**. The design is intentionally simple — passengers have no administrative controls and cannot navigate to staff or admin pages. Attempting to access those URLs directly redirects back to login. This is the entry point to the booking transaction flow.

### Admin Dashboard — Staff & Trains Tabs
The admin dashboard opens with a live summary row showing counts of Staff, Assignments, Stations, Trains, and Routes pulled from the database in real time. Three tabs give access to separate management panels:

- **Staff tab** — A form collects Full Name, CNIC, Phone, Email, Password, Role (e.g. Conductor), Salary, Shift Start Date, and Shift Type (Morning/Evening). Clicking **Create & Auto-Assign to 8 Stations** fires the atomic staff-creation transaction. A "Station Assignment Load" bar chart on the right shows how many staff members are currently assigned to each station, giving the admin visibility into workload distribution before creating new assignments.
- **Trains tab** — Admin enters a train name and clicks **Create Train + 30 Seats**. The backend automatically creates 10 Economy (PKR 2,000), 10 Business (PKR 3,500), and 10 AC (PKR 5,000) seats atomically. The existing trains table below shows remaining seat counts per class.
- **Routes & Stations tab** — Three cards let the admin create a new Station, create a new Route, and add an existing Station to an existing Route with arrival/departure times. Read-only tables at the bottom list all stations (with assignment counts) and all routes (with station counts).

### Admin — Manually Add a Shift
A dedicated form lets the admin add a single shift to an existing staff member. The admin selects the Staff Member and Station from dropdowns, picks a Shift Date, and chooses a Shift Type (Morning/Evening). The backend enforces the maximum-8-shifts-per-week rule via the `ensure_40_hour_rule` trigger; if the limit is already reached the operation is rejected and the UI displays an error. This form exists so that exceptional or one-off shifts can be scheduled without triggering a full staff re-creation.

---

## 5. Setup & Installation

### Prerequisites
- Python 3.10+
- SQLite 3 (bundled with Python)
- pip

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment
```bash
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=replace_with_a_long_random_string
DB_PATH=db.db
```

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | Signs JWT tokens and Flask sessions | `s3cr3t_r4nd0m_k3y` |
| `DB_PATH` | Path to the SQLite database file | `db.db` |

### Initialise the Database
```bash
sqlite3 db.db < Database/schema.sql
sqlite3 db.db < Database/seed.sql
```

### Set the Admin Password
The hash in `seed.sql` is a placeholder. Generate a real bcrypt hash and apply it:
```python
import bcrypt
print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())
```
```bash
sqlite3 db.db "UPDATE User SET password='<paste_hash_here>' WHERE cnic='1234567890123';"
```

### Start the Application

**REST API:**
```bash
cd backend
python api.py
```
Base URL: `http://localhost:5000/api/v1`

**Browser UI:**
```bash
cd backend
python app.py
```
Open `http://localhost:5000` in a browser.

---

## 6. User Roles

| Role | Can Do | Cannot Do | Login Credentials (seed.sql) |
|------|--------|-----------|------------------------------|
| **Passenger** | Register, login, search trains, book a seat, view own tickets | Access staff schedules or admin controls | Register a new account |
| **Staff** | Login, view assigned shift schedule | Book tickets, modify data | Created by admin |
| **Admin** | Login, view dashboard, manage stations/trains/routes, create staff (auto 8 shifts), manually add shifts | Book passenger tickets | CNIC: `1234567890123` / PW: `admin123` |

---

## 7. Feature Walkthrough

### Passenger — Book a Ticket
- **Role:** Passenger
- **Page:** `/book`
- **API:** `POST /api/v1/passenger/book`
- The passenger selects a train and seat. The backend wraps Payment insert + Ticket insert + Seat update in a single transaction. If the seat is already taken the `ensure_no_double_booking` trigger aborts the transaction and the UI shows an error.

### Passenger — View My Tickets
- **Role:** Passenger
- **Page:** `/my_tickets`
- **API:** `GET /api/v1/passenger/tickets`
- Lists all bookings for the logged-in passenger with train name, route, seat number, and payment status.

### Staff — View Schedule
- **Role:** Staff
- **Page:** `/staff_dashboard`
- **API:** `GET /api/v1/staff/dashboard`
- Displays the staff member's assigned shifts (day, start time, end time, station).

### Admin — Create Staff (Auto 8 Shifts)
- **Role:** Admin
- **Page:** `/admin_dashboard` → Staff tab
- **API:** `POST /api/v1/admin/staff`
- Admin fills in staff details. The backend opens one transaction: inserts a User row, inserts a Staff row, then inserts 8 Staff_Assignment rows covering a standard working week. If any insert fails (e.g. the `ensure_40_hour_rule` trigger fires) the entire transaction rolls back atomically — no partial data is written.

### Admin — Manually Add a Shift
- **Role:** Admin
- **Page:** `/admin_dashboard` → Add Shift form
- **API:** `POST /api/v1/admin/staff/shift`
- Admin selects an existing staff member, a station, a date, and a shift type. The backend validates against the 40-hour cap trigger before committing.

### Admin — Manage Stations / Trains / Routes
- **Role:** Admin
- **Pages:** Routes & Stations tab and Trains tab within admin dashboard
- **APIs:** `GET/POST /api/v1/admin/stations`, `GET/POST /api/v1/admin/trains`, `GET/POST /api/v1/admin/routes`, `POST /api/v1/admin/routes/station`
- Full CRUD for the core rail network entities.

---

## 8. Transaction Scenarios

### Scenario 1 — Ticket Booking (`POST /api/v1/passenger/book`)

| Step | Operation |
|------|-----------|
| 1 | `BEGIN TRANSACTION` |
| 2 | `INSERT INTO Payment` |
| 3 | `INSERT INTO Ticket` |
| 4 | `UPDATE Seat SET is_available = 0` |
| 5 | `COMMIT` on success |

**Rollback trigger:** `ensure_no_double_booking` — fires on Ticket insert if the seat is already booked for that journey. SQLite raises `ABORT`; Python catches it, executes `ROLLBACK`, and writes an entry to `rollback.log`.

**Code location:** `backend/api.py` → `book_ticket()` function.

### Scenario 2 — Staff Creation (`POST /api/v1/admin/staff`)

| Step | Operation |
|------|-----------|
| 1 | `BEGIN TRANSACTION` |
| 2 | `INSERT INTO User` |
| 3 | `INSERT INTO Staff` |
| 4 | `INSERT INTO Staff_Assignment` × 8 |
| 5 | `COMMIT` on success |

**Rollback trigger:** `ensure_40_hour_rule` — fires on any Staff_Assignment insert if the running weekly total for that staff member would exceed 40 hours. SQLite raises `ABORT`; all 10+ inserts are rolled back atomically.

**Code location:** `backend/api.py` → `create_staff()` function.

---

## 9. ACID Compliance

| Property | Implementation |
|----------|---------------|
| **Atomicity** | Explicit `BEGIN … COMMIT / ROLLBACK` blocks in `api.py` for booking and staff creation. A trigger-raised `ABORT` causes Python to issue `ROLLBACK`, leaving no partial rows. |
| **Consistency** | `FOREIGN KEY` constraints on all relational tables; `UNIQUE` constraints on CNIC and seat-journey pairs; `NOT NULL` on critical columns; triggers enforce business rules (no double-booking, 40-hour cap). |
| **Isolation** | SQLite's default serialised write locking ensures that concurrent booking attempts cannot both pass the double-booking check simultaneously. |
| **Durability** | SQLite writes to `db.db` with WAL mode; once `COMMIT` returns, data survives process restart. |

---

## 10. Indexing & Performance

Indexes are defined in `Database/performance.sql`. Rationale:

| Index | Table | Column(s) | Why |
|-------|-------|-----------|-----|
| `idx_ticket_journey` | Ticket | `journey_id` | Speeds up double-booking trigger look-up on every booking |
| `idx_ticket_passenger` | Ticket | `passenger_id` | Speeds up "My Tickets" query (passenger filters by own ID) |
| `idx_staff_assignment_staff` | Staff_Assignment | `staff_id` | Speeds up staff schedule retrieval |
| `idx_seat_train` | Seat | `train_id, is_available` | Speeds up available-seat listing per train |

Query plans and before/after timing measurements are recorded in `Database/performance.sql` using `EXPLAIN QUERY PLAN`.

---

## 11. API Reference

Full detail is in `Docs/swagger.yaml`. Open it at [https://editor.swagger.io](https://editor.swagger.io).

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| POST | `/api/v1/register` | None | Register a new passenger |
| POST | `/api/v1/login` | None | Obtain Bearer token |
| GET | `/api/v1/trains` | Any | List all trains |
| GET | `/api/v1/passenger/tickets` | Passenger | List own tickets |
| POST | `/api/v1/passenger/book` | Passenger | Book a seat (atomic) |
| GET | `/api/v1/admin/dashboard` | Admin | Dashboard summary |
| POST | `/api/v1/admin/staff` | Admin | Create staff + 8 shifts (atomic) |
| POST | `/api/v1/admin/staff/shift` | Admin | Add a single shift manually |
| GET | `/api/v1/admin/stations` | Admin | List stations |
| POST | `/api/v1/admin/stations` | Admin | Add a station |
| GET | `/api/v1/admin/trains` | Admin | List trains |
| POST | `/api/v1/admin/trains` | Admin | Add a train |
| GET | `/api/v1/admin/routes` | Admin | List routes |
| POST | `/api/v1/admin/routes` | Admin | Add a route |
| POST | `/api/v1/admin/routes/station` | Admin | Add station to a route |
| GET | `/api/v1/staff/dashboard` | Staff | View own shift schedule |

---

## 12. Known Issues & Limitations

- **Staff cannot book tickets:** The current database schema ties ticket ownership to a Passenger record. A staff member's User row has no linked Passenger row, so the booking flow rejects them. A proper fix requires a schema change — for example, allowing a User to simultaneously hold a Staff and a Passenger profile. No workaround is currently implemented; this is a known gap that would need database-level changes to resolve.

- **Roles are enforced at the application level, not the database level:** Role-based access control (passenger, staff, admin) is implemented entirely inside Flask route handlers and middleware in `api.py` and `app.py`. The database itself has no row-level security, restricted views, or separate database users per role. This means a direct SQL query against `db.db` bypasses all role checks. A more robust implementation would push access control down to the database layer.

- **No frontend framework:** The UI is rendered via Flask Jinja2 templates. There is no separate `frontend/` directory with a build step; all HTML lives in `backend/templates/`.

- **Single-file servers:** `api.py` and `app.py` are not split into `routes/`, `controllers/`, and `models/` sub-folders as suggested by the Phase 3 directory template. This deviation is intentional to keep the codebase simple for a two-file Flask setup.

- **No real-time updates:** The staff schedule and passenger ticket list require a manual page refresh; WebSocket/polling is not implemented.

- **SQLite concurrency:** Under heavy simultaneous booking load SQLite's write lock may cause brief contention. A production deployment would migrate to PostgreSQL.

- **Admin password setup:** The seed hash is a placeholder and must be replaced manually after seeding (see Setup section). Automating this is left as a future improvement.