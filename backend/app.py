from flask import Flask, request, g, render_template, redirect, url_for, flash
import sqlite3
import jwt
import bcrypt
import logging
from datetime import datetime, date, timedelta
from functools import wraps
from collections import defaultdict

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
DB_PATH = "db.db"


# ------------------------------------------------------------------ #
#  Logging — writes ONLY rollback events to rollback.log
#
#  Why not basicConfig:
#  Flask configures the root logger before our code runs, so
#  basicConfig() is a no-op (it only acts if no handlers exist yet).
#  We bypass this by attaching a FileHandler directly to our named
#  logger and setting propagate=False so Flask's root logger is
#  never involved.
# ------------------------------------------------------------------ #
_rollback_logger = logging.getLogger("rollback")
_rollback_logger.setLevel(logging.ERROR)
_rollback_logger.propagate = False  # don't forward to Flask's root logger

_fh = logging.FileHandler("rollback.log")
_fh.setLevel(logging.ERROR)
_fh.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
_rollback_logger.addHandler(_fh)


def log_rollback(route, error, admin_id=None):
    """Log a rollback event. Only writes to rollback.log, nothing else."""
    who = f"admin_id={admin_id}" if admin_id else "unauthenticated"
    _rollback_logger.error(f"[{route}] ROLLBACK by {who} — {error}")


# ------------------------------------------------------------------ #
#  DB helper
# ------------------------------------------------------------------ #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ------------------------------------------------------------------ #
#  Auth helpers
# ------------------------------------------------------------------ #
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return redirect(url_for("login"))
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user = payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def rbac_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if g.user.get("role") not in roles:
                return "Forbidden", 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


# ------------------------------------------------------------------ #
#  ID helper — MAX(id)+1, works for every table with an id column
# ------------------------------------------------------------------ #
def next_id(cursor, table):
    cursor.execute(f"SELECT MAX(id) AS max_id FROM {table}")
    row = cursor.fetchone()
    return 1 if row["max_id"] is None else row["max_id"] + 1


# ------------------------------------------------------------------ #
#  Register
# ------------------------------------------------------------------ #
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name")
    cnic = request.form.get("cnic")
    email = request.form.get("email")
    phone = request.form.get("phone_number")
    password = request.form.get("password")

    if not all([name, cnic, email, phone, password]):
        return "All fields are required", 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM User WHERE cnic = ?", (cnic,))
        if cursor.fetchone():
            return "User with this CNIC already exists", 409

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user_id = next_id(cursor, "User")
        cursor.execute(
            "INSERT INTO User (id, name, cnic, email, password, phone_number, role) VALUES (?,?,?,?,?,?,?)",
            (user_id, name, cnic, email, hashed, phone, "passenger"),
        )
        cursor.execute("INSERT INTO Passenger (id) VALUES (?)", (user_id,))
        db.commit()
        return redirect(url_for("login"))
    except Exception as e:
        db.rollback()
        log_rollback("register", e)
        return f"Registration failed: {e}", 500


# ------------------------------------------------------------------ #
#  Login / Logout / Home
# ------------------------------------------------------------------ #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    cnic = request.form.get("cnic")
    password = request.form.get("password")
    if not all([cnic, password]):
        return "CNIC and password required", 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE cnic = ?", (cnic,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404
    if not bcrypt.checkpw(password.encode(), user["password"]):
        return "Invalid password", 401

    token = jwt.encode(
        {
            "id": user["id"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=2),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    role_map = {
        "passenger": "passenger_dashboard",
        "staff": "staff_dashboard",
        "admin": "admin_dashboard",
    }
    target = role_map.get(user["role"])
    if not target:
        return "Invalid role", 403

    resp = redirect(url_for(target))
    resp.set_cookie("token", token, httponly=True)
    return resp


@app.route("/logout")
def logout():
    resp = redirect(url_for("login"))
    resp.set_cookie("token", "", expires=0)
    return resp


@app.route("/")
def home():
    token = request.cookies.get("token")
    if not token:
        return redirect(url_for("login"))
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        role_map = {
            "passenger": "passenger_dashboard",
            "staff": "staff_dashboard",
            "admin": "admin_dashboard",
        }
        target = role_map.get(payload.get("role"))
        return redirect(url_for(target)) if target else redirect(url_for("login"))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return redirect(url_for("login"))


# ------------------------------------------------------------------ #
#  Passenger routes
# ------------------------------------------------------------------ #
@app.route("/passenger_dashboard")
@token_required
@rbac_required("passenger")
def passenger_dashboard():
    return render_template("passenger_dashboard.html", user_id=g.user["id"])


@app.route("/my_tickets")
@token_required
def my_tickets():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT ticket_id, train_name, seat_class, travel_date, payment_amount
           FROM passenger_bookings_view WHERE passenger_id = ? ORDER BY travel_date""",
        (g.user["id"],),
    )
    return render_template("my_tickets.html", tickets=cursor.fetchall())


@app.route("/book", methods=["GET", "POST"])
@token_required
def book():
    db = get_db()
    cursor = db.cursor()
    if request.method == "GET":
        cursor.execute("SELECT id, name FROM Train")
        return render_template("book.html", trains=cursor.fetchall())

    train_id = request.form.get("train_id")
    seat_class = request.form.get("seat_class")
    travel_date = request.form.get("travel_date")
    if not all([train_id, seat_class, travel_date]):
        return "All fields are required", 400
    try:
        td = datetime.strptime(travel_date, "%Y-%m-%d").date()
        if td < date.today():
            return "Travel date cannot be in the past", 400
    except ValueError:
        return "Invalid date format", 400

    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            "SELECT id FROM Seat WHERE train_id=? AND class=? AND status='Free' LIMIT 1",
            (train_id, seat_class),
        )
        seat = cursor.fetchone()
        if not seat:
            db.rollback()
            return "No seats available", 409

        ticket_id = next_id(cursor, "Ticket")
        payment_id = next_id(cursor, "Payment")
        amount = {"Economy": 2000, "Business": 3500, "AC": 5000}.get(seat_class, 2000)

        cursor.execute(
            "INSERT INTO Payment (id, ticket_id, amount) VALUES (?,?,?)",
            (payment_id, ticket_id, amount),
        )
        cursor.execute(
            "INSERT INTO Ticket (id, train_id, passenger_id, seat_id, payment_id, travel_date) VALUES (?,?,?,?,?,?)",
            (ticket_id, train_id, g.user["id"], seat["id"], payment_id, travel_date),
        )
        cursor.execute("UPDATE Seat SET status='Occupied' WHERE id=?", (seat["id"],))
        db.commit()
        return f"Booked! Ticket #{ticket_id} | PKR {amount}"
    except Exception as e:
        db.rollback()
        log_rollback("book", e)
        return f"Booking failed: {e}", 500


# ================================================================== #
#  ADMIN — dashboard GET
# ================================================================== #
@app.route("/admin_dashboard")
@token_required
@rbac_required("admin")
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()

    # metrics
    cursor.execute("SELECT COUNT(*) AS c FROM Staff")
    total_staff = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) AS c FROM Staff_Assignment")
    total_assignments = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) AS c FROM Station")
    total_stations = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) AS c FROM Train")
    total_trains = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) AS c FROM Route")
    total_routes = cursor.fetchone()["c"]

    metrics = {
        "total_staff": total_staff,
        "total_assignments": total_assignments,
        "total_stations": total_stations,
        "total_trains": total_trains,
        "total_routes": total_routes,
    }

    # station load bars
    cursor.execute(
        """SELECT s.name, COUNT(sa.staff_id) AS cnt
           FROM Station s
           LEFT JOIN Staff_Assignment sa ON sa.station_id = s.id
           GROUP BY s.id ORDER BY cnt DESC"""
    )
    raw = cursor.fetchall()
    max_load = max((r["cnt"] for r in raw), default=1) or 1
    station_loads = [
        {"name": r["name"], "count": r["cnt"], "pct": round(r["cnt"] / max_load * 100)}
        for r in raw
    ]

    # staff list
    cursor.execute(
        """SELECT u.name, u.email, st.role, st.salary,
                  COALESCE(
                    (SELECT sa.shift_type FROM Staff_Assignment sa
                     WHERE sa.staff_id = st.id ORDER BY sa.shift_date DESC LIMIT 1),
                    'N/A'
                  ) AS shift_type,
                  COUNT(sa2.staff_id) AS assignment_count
           FROM Staff st
           JOIN User u ON u.id = st.id
           LEFT JOIN Staff_Assignment sa2 ON sa2.staff_id = st.id
           GROUP BY st.id ORDER BY u.name"""
    )
    staff_list = [dict(r) for r in cursor.fetchall()]

    # trains list — seat counts per class
    cursor.execute(
        """SELECT t.id, t.name,
                  SUM(CASE WHEN s.class='Economy'  THEN 1 ELSE 0 END) AS economy_seats,
                  SUM(CASE WHEN s.class='Business' THEN 1 ELSE 0 END) AS business_seats,
                  SUM(CASE WHEN s.class='AC'       THEN 1 ELSE 0 END) AS ac_seats,
                  COUNT(s.id) AS total_seats
           FROM Train t
           LEFT JOIN Seat s ON s.train_id = t.id
           GROUP BY t.id ORDER BY t.id"""
    )
    trains_list = [dict(r) for r in cursor.fetchall()]

    # stations list with assignment count
    cursor.execute(
        """SELECT s.id, s.name, COUNT(sa.staff_id) AS assignment_count
           FROM Station s
           LEFT JOIN Staff_Assignment sa ON sa.station_id = s.id
           GROUP BY s.id ORDER BY s.name"""
    )
    stations_list = [dict(r) for r in cursor.fetchall()]

    # routes list with station count
    cursor.execute(
        """SELECT r.route_id, r.route_name, COUNT(rs.id) AS station_count
           FROM Route r
           LEFT JOIN Route_Station rs ON rs.route_id = r.route_id
           GROUP BY r.route_id ORDER BY r.route_id"""
    )
    routes_list = [dict(r) for r in cursor.fetchall()]

    # dropdowns for forms
    cursor.execute("SELECT id, name FROM Station ORDER BY name")
    stations_dropdown = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT route_id, route_name FROM Route ORDER BY route_name")
    routes_dropdown = [dict(r) for r in cursor.fetchall()]

    # staff dropdown for manual shift form — id + name
    cursor.execute(
        "SELECT st.id, u.name FROM Staff st JOIN User u ON u.id = st.id ORDER BY u.name"
    )
    staff_dropdown = [dict(r) for r in cursor.fetchall()]

    return render_template(
        "admin_dashboard.html",
        metrics=metrics,
        station_loads=station_loads,
        staff_list=staff_list,
        trains_list=trains_list,
        stations_list=stations_list,
        routes_list=routes_list,
        stations_dropdown=stations_dropdown,
        routes_dropdown=routes_dropdown,
        staff_dropdown=staff_dropdown,
    )


# ================================================================== #
#  ADMIN — create staff
# ================================================================== #
@app.route("/admin/create_staff", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_staff():
    admin_id = g.user.get("id")
    name = request.form.get("name", "").strip()
    cnic = request.form.get("cnic", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone_number", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "").strip()
    salary_raw = request.form.get("salary", "").strip()
    shift_date = request.form.get("shift_date", "").strip()
    shift_type = request.form.get("shift_type", "Morning").strip()

    if not all([name, cnic, email, phone, password, role, salary_raw, shift_date]):
        flash("All fields are required.", "error")
        return redirect(url_for("admin_dashboard"))
    if len(cnic) != 13 or not cnic.isdigit():
        flash("CNIC must be exactly 13 digits.", "error")
        return redirect(url_for("admin_dashboard"))
    if len(phone) != 11 or not phone.isdigit():
        flash("Phone must be exactly 11 digits.", "error")
        return redirect(url_for("admin_dashboard"))
    try:
        salary = int(salary_raw)
        if salary <= 0:
            raise ValueError
    except ValueError:
        flash("Salary must be a positive number.", "error")
        return redirect(url_for("admin_dashboard"))
    try:
        start = datetime.strptime(shift_date, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid shift start date.", "error")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM User WHERE cnic = ?", (cnic,))
        if cursor.fetchone():
            flash("A user with this CNIC already exists.", "error")
            return redirect(url_for("admin_dashboard"))

        cursor.execute("BEGIN TRANSACTION")
        user_id = next_id(cursor, "User")
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        cursor.execute(
            "INSERT INTO User (id, name, cnic, email, password, phone_number, role) VALUES (?,?,?,?,?,?,?)",
            (user_id, name, cnic, email, hashed, phone, "staff"),
        )
        cursor.execute(
            "INSERT INTO Staff (id, role, salary) VALUES (?,?,?)",
            (user_id, role, salary),
        )

        # 8 least-loaded stations — LEFT JOIN so zero-assignment stations rank first
        cursor.execute(
            """SELECT s.id FROM Station s
               LEFT JOIN Staff_Assignment sa ON sa.station_id = s.id
               GROUP BY s.id ORDER BY COUNT(sa.staff_id) ASC LIMIT 8"""
        )
        stations = [r["id"] for r in cursor.fetchall()]
        if not stations:
            db.rollback()
            flash("No stations found. Add stations first.", "error")
            return redirect(url_for("admin_dashboard"))

        for i, sid in enumerate(stations):
            assign_date = (start + timedelta(days=i)).isoformat()
            cursor.execute(
                "INSERT INTO Staff_Assignment (staff_id, station_id, shift_date, shift_type) VALUES (?,?,?,?)",
                (user_id, sid, assign_date, shift_type),
            )

        db.commit()
        flash(
            f"{name} created and auto-assigned to {len(stations)} stations.", "success"
        )
    except Exception as e:
        db.rollback()
        log_rollback("create_staff", e, admin_id)
        flash(f"Failed to create staff: {e}", "error")

    return redirect(url_for("admin_dashboard"))


# ================================================================== #
#  ADMIN — manually add a shift for an existing staff member
# ================================================================== #
@app.route("/admin/add_shift", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_add_shift():
    admin_id = g.user.get("id")
    staff_id = request.form.get("staff_id", "").strip()
    station_id = request.form.get("station_id", "").strip()
    shift_date = request.form.get("shift_date", "").strip()
    shift_type = request.form.get("shift_type", "Morning").strip()

    if not all([staff_id, station_id, shift_date]):
        flash("Staff member, station, and shift date are all required.", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        datetime.strptime(shift_date, "%Y-%m-%d")
    except ValueError:
        flash("Invalid shift date.", "error")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    cursor = db.cursor()
    try:
        # Confirm staff member exists
        cursor.execute("SELECT id FROM Staff WHERE id = ?", (staff_id,))
        if not cursor.fetchone():
            flash("Staff member not found.", "error")
            return redirect(url_for("admin_dashboard"))

        # Confirm station exists
        cursor.execute("SELECT id FROM Station WHERE id = ?", (station_id,))
        if not cursor.fetchone():
            flash("Station not found.", "error")
            return redirect(url_for("admin_dashboard"))

        # PK is (staff_id, shift_date, shift_type) — check for duplicate
        cursor.execute(
            """SELECT 1 FROM Staff_Assignment
               WHERE staff_id=? AND shift_date=? AND shift_type=?""",
            (staff_id, shift_date, shift_type),
        )
        if cursor.fetchone():
            flash(
                "This staff member already has a shift on that date with the same shift type.",
                "error",
            )
            return redirect(url_for("admin_dashboard"))

        cursor.execute(
            "INSERT INTO Staff_Assignment (staff_id, station_id, shift_date, shift_type) VALUES (?,?,?,?)",
            (staff_id, station_id, shift_date, shift_type),
        )
        db.commit()
        flash("Shift added successfully.", "success")
    except Exception as e:
        db.rollback()
        log_rollback("add_shift", e, admin_id)
        flash(f"Failed to add shift: {e}", "error")

    return redirect(url_for("admin_dashboard"))


# ================================================================== #
#  ADMIN — create station
# ================================================================== #
@app.route("/admin/create_station", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_station():
    admin_id = g.user.get("id")
    name = request.form.get("station_name", "").strip()
    if not name:
        flash("Station name is required.", "error")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM Station WHERE name = ?", (name,))
        if cursor.fetchone():
            flash(f"Station '{name}' already exists.", "error")
            return redirect(url_for("admin_dashboard"))

        station_id = next_id(cursor, "Station")
        cursor.execute(
            "INSERT INTO Station (id, name) VALUES (?,?)", (station_id, name)
        )
        db.commit()
        flash(f"Station '{name}' created (ID {station_id}).", "success")
    except Exception as e:
        db.rollback()
        log_rollback("create_station", e, admin_id)
        flash(f"Failed to create station: {e}", "error")

    return redirect(url_for("admin_dashboard"))


# ================================================================== #
#  ADMIN — create train + 30 seats
# ================================================================== #
@app.route("/admin/create_train", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_train():
    admin_id = g.user.get("id")
    name = request.form.get("train_name", "").strip()
    if not name:
        flash("Train name is required.", "error")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM Train WHERE name = ?", (name,))
        if cursor.fetchone():
            flash(f"Train '{name}' already exists.", "error")
            return redirect(url_for("admin_dashboard"))

        cursor.execute("BEGIN TRANSACTION")
        train_id = next_id(cursor, "Train")
        cursor.execute("INSERT INTO Train (id, name) VALUES (?,?)", (train_id, name))

        # 10 seats per class — each seat gets its own globally-unique id
        for cls in ("Economy", "Business", "AC"):
            for _ in range(10):
                seat_id = next_id(cursor, "Seat")
                cursor.execute(
                    "INSERT INTO Seat (id, train_id, class, status) VALUES (?,?,?,?)",
                    (seat_id, train_id, cls, "Free"),
                )

        db.commit()
        flash(
            f"Train '{name}' (ID {train_id}) created with 30 seats "
            f"(10 Economy, 10 Business, 10 AC).",
            "success",
        )
    except Exception as e:
        db.rollback()
        log_rollback("create_train", e, admin_id)
        flash(f"Failed to create train: {e}", "error")

    return redirect(url_for("admin_dashboard"))


# ================================================================== #
#  ADMIN — create route
# ================================================================== #
@app.route("/admin/create_route", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_route():
    admin_id = g.user.get("id")
    route_name = request.form.get("route_name", "").strip()
    if not route_name:
        flash("Route name is required.", "error")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT route_id FROM Route WHERE route_name = ?", (route_name,))
        if cursor.fetchone():
            flash(f"Route '{route_name}' already exists.", "error")
            return redirect(url_for("admin_dashboard"))

        # Route PK is route_id, not id
        cursor.execute("SELECT MAX(route_id) AS max_id FROM Route")
        row = cursor.fetchone()
        route_id = 1 if row["max_id"] is None else row["max_id"] + 1

        cursor.execute(
            "INSERT INTO Route (route_id, route_name) VALUES (?,?)",
            (route_id, route_name),
        )
        db.commit()
        flash(f"Route '{route_name}' created (ID {route_id}).", "success")
    except Exception as e:
        db.rollback()
        log_rollback("create_route", e, admin_id)
        flash(f"Failed to create route: {e}", "error")

    return redirect(url_for("admin_dashboard"))


# ================================================================== #
#  ADMIN — add station to route
# ================================================================== #
@app.route("/admin/add_route_station", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_add_route_station():
    admin_id = g.user.get("id")
    route_id = request.form.get("route_id", "").strip()
    station_id = request.form.get("station_id", "").strip()
    arrival_time = request.form.get("arrival_time", "").strip() or None
    departure_time = request.form.get("departure_time", "").strip() or None

    if not all([route_id, station_id]):
        flash("Route and station are required.", "error")
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT id FROM Route_Station WHERE route_id=? AND station_id=?",
            (route_id, station_id),
        )
        if cursor.fetchone():
            flash("That station is already on this route.", "error")
            return redirect(url_for("admin_dashboard"))

        rs_id = next_id(cursor, "Route_Station")
        cursor.execute(
            "INSERT INTO Route_Station (id, route_id, station_id, arrival_time, departure_time) VALUES (?,?,?,?,?)",
            (rs_id, route_id, station_id, arrival_time, departure_time),
        )
        db.commit()
        flash("Station added to route successfully.", "success")
    except Exception as e:
        db.rollback()
        log_rollback("add_route_station", e, admin_id)
        flash(f"Failed to add station to route: {e}", "error")

    return redirect(url_for("admin_dashboard"))


# ================================================================== #
#  STAFF DASHBOARD
# ================================================================== #
@app.route("/staff_dashboard")
@token_required
@rbac_required("staff")
def staff_dashboard():
    staff_id = g.user["id"]
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """SELECT u.name, u.email, u.cnic, u.phone_number, st.role, st.salary
           FROM Staff st JOIN User u ON u.id = st.id WHERE st.id = ?""",
        (staff_id,),
    )
    row = cursor.fetchone()
    if not row:
        return "Staff record not found", 404
    staff = dict(row)

    cursor.execute(
        """SELECT sa.shift_date, sa.shift_type, s.name AS station_name
           FROM Staff_Assignment sa
           JOIN Station s ON s.id = sa.station_id
           WHERE sa.staff_id = ? ORDER BY sa.shift_date""",
        (staff_id,),
    )
    all_assignments = cursor.fetchall()
    total_assignments = len(all_assignments)

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    this_week_count = sum(
        1
        for a in all_assignments
        if week_start
        <= datetime.strptime(a["shift_date"], "%Y-%m-%d").date()
        <= week_end
    )

    def week_label(date_str):
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        ws = d - timedelta(days=d.weekday())
        we = ws + timedelta(days=6)
        return f"Week of {ws.strftime('%d %b')} – {we.strftime('%d %b')}"

    grouped = defaultdict(list)
    for a in all_assignments:
        grouped[week_label(a["shift_date"])].append(dict(a))

    return render_template(
        "staff_dashboard.html",
        staff=staff,
        grouped_assignments=dict(grouped),
        total_assignments=total_assignments,
        this_week_count=this_week_count,
    )


if __name__ == "__main__":
    app.run(debug=True)
