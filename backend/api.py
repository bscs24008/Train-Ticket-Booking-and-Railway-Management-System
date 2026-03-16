from flask import Flask, request, g, jsonify
import sqlite3
import jwt
import bcrypt
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from functools import wraps
from collections import defaultdict

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
DB_PATH = os.getenv("DB_PATH", "db.db")


# ------------------------------------------------------------------ #
#  Logging — rollbacks only
# ------------------------------------------------------------------ #
_rollback_logger = logging.getLogger("rollback")
_rollback_logger.setLevel(logging.ERROR)
_rollback_logger.propagate = False

_fh = logging.FileHandler("rollback.log")
_fh.setLevel(logging.ERROR)
_fh.setFormatter(
    logging.Formatter(
        fmt="%(asctime)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
_rollback_logger.addHandler(_fh)


def log_rollback(route, error, user_id=None):
    who = f"user_id={user_id}" if user_id else "unauthenticated"
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
#  ID helper
# ------------------------------------------------------------------ #
def next_id(cursor, table):
    cursor.execute(f"SELECT MAX(id) AS max_id FROM {table}")
    row = cursor.fetchone()
    return 1 if row["max_id"] is None else row["max_id"] + 1


# ------------------------------------------------------------------ #
#  Auth helpers
# ------------------------------------------------------------------ #
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)

    return decorated


def rbac_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if g.user.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


# ================================================================== #
#  AUTH
# ================================================================== #


# POST /api/v1/register
@app.route("/api/v1/register", methods=["POST"])
def register():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    cnic = (data.get("cnic") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone_number") or "").strip()
    password = (data.get("password") or "").strip()

    if not all([name, cnic, email, phone, password]):
        return jsonify({"error": "All fields are required"}), 400
    if len(cnic) != 13 or not cnic.isdigit():
        return jsonify({"error": "CNIC must be exactly 13 digits"}), 400
    if len(phone) != 11 or not phone.isdigit():
        return jsonify({"error": "Phone must be exactly 11 digits"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM User WHERE cnic = ?", (cnic,))
        if cursor.fetchone():
            return jsonify({"error": "User with this CNIC already exists"}), 409

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user_id = next_id(cursor, "User")
        cursor.execute(
            "INSERT INTO User (id, name, cnic, email, password, phone_number, role) VALUES (?,?,?,?,?,?,?)",
            (user_id, name, cnic, email, hashed, phone, "passenger"),
        )
        cursor.execute("INSERT INTO Passenger (id) VALUES (?)", (user_id,))
        db.commit()
        return jsonify({"message": "Registered successfully", "user_id": user_id}), 201
    except Exception as e:
        db.rollback()
        log_rollback("register", e)
        return jsonify({"error": f"Registration failed: {e}"}), 500


# POST /api/v1/login
@app.route("/api/v1/login", methods=["POST"])
def login():
    data = request.get_json()
    cnic = (data.get("cnic") or "").strip()
    password = (data.get("password") or "").strip()

    if not all([cnic, password]):
        return jsonify({"error": "CNIC and password are required"}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE cnic = ?", (cnic,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not bcrypt.checkpw(password.encode(), user["password"]):
        return jsonify({"error": "Invalid password"}), 401

    token = jwt.encode(
        {
            "id": user["id"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=2),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify({"token": token, "role": user["role"], "user_id": user["id"]}), 200


# ================================================================== #
#  PASSENGER
# ================================================================== #


# GET /api/v1/trains
@app.route("/api/v1/trains", methods=["GET"])
@token_required
def get_trains():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM Train")
    return jsonify({"trains": [dict(r) for r in cursor.fetchall()]}), 200


# GET /api/v1/passenger/tickets
@app.route("/api/v1/passenger/tickets", methods=["GET"])
@token_required
@rbac_required("passenger")
def get_my_tickets():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT ticket_id, train_name, seat_class, travel_date, payment_amount
           FROM passenger_bookings_view
           WHERE passenger_id = ?
           ORDER BY travel_date""",
        (g.user["id"],),
    )
    return jsonify({"tickets": [dict(r) for r in cursor.fetchall()]}), 200


# POST /api/v1/passenger/book
@app.route("/api/v1/passenger/book", methods=["POST"])
@token_required
@rbac_required("passenger")
def book():
    data = request.get_json()
    train_id = data.get("train_id")
    seat_class = data.get("seat_class")
    travel_date = (data.get("travel_date") or "").strip()

    if not all([train_id, seat_class, travel_date]):
        return jsonify(
            {"error": "train_id, seat_class, and travel_date are required"}
        ), 400
    if seat_class not in ("Economy", "Business", "AC"):
        return jsonify({"error": "seat_class must be Economy, Business, or AC"}), 400
    try:
        td = datetime.strptime(travel_date, "%Y-%m-%d").date()
        if td < date.today():
            return jsonify({"error": "Travel date cannot be in the past"}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute(
            "SELECT id FROM Seat WHERE train_id=? AND class=? AND status='Free' LIMIT 1",
            (train_id, seat_class),
        )
        seat = cursor.fetchone()
        if not seat:
            db.rollback()
            return jsonify({"error": "No seats available in this class"}), 409

        ticket_id = next_id(cursor, "Ticket")
        payment_id = next_id(cursor, "Payment")
        amount = {"Economy": 2000, "Business": 3500, "AC": 5000}[seat_class]

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
        return jsonify(
            {
                "message": "Ticket booked successfully",
                "ticket_id": ticket_id,
                "payment_id": payment_id,
                "amount": amount,
                "seat_class": seat_class,
                "travel_date": travel_date,
            }
        ), 201
    except Exception as e:
        db.rollback()
        log_rollback("book", e, g.user["id"])
        return jsonify({"error": f"Booking failed: {e}"}), 500


# ================================================================== #
#  ADMIN — dashboard
# ================================================================== #


# GET /api/v1/admin/dashboard
@app.route("/api/v1/admin/dashboard", methods=["GET"])
@token_required
@rbac_required("admin")
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()

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

    cursor.execute(
        """SELECT s.id, s.name, COUNT(sa.staff_id) AS assignment_count
           FROM Station s
           LEFT JOIN Staff_Assignment sa ON sa.station_id = s.id
           GROUP BY s.id ORDER BY assignment_count DESC"""
    )
    station_loads = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        """SELECT u.name, u.email, st.role, st.salary,
                  COALESCE(
                    (SELECT sa.shift_type FROM Staff_Assignment sa
                     WHERE sa.staff_id = st.id ORDER BY sa.shift_date DESC LIMIT 1),
                    'N/A'
                  ) AS last_shift_type,
                  COUNT(sa2.staff_id) AS assignment_count
           FROM Staff st
           JOIN User u ON u.id = st.id
           LEFT JOIN Staff_Assignment sa2 ON sa2.staff_id = st.id
           GROUP BY st.id ORDER BY u.name"""
    )
    staff_list = [dict(r) for r in cursor.fetchall()]

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

    cursor.execute(
        """SELECT r.route_id, r.route_name, COUNT(rs.id) AS station_count
           FROM Route r
           LEFT JOIN Route_Station rs ON rs.route_id = r.route_id
           GROUP BY r.route_id ORDER BY r.route_id"""
    )
    routes_list = [dict(r) for r in cursor.fetchall()]

    return jsonify(
        {
            "metrics": {
                "total_staff": total_staff,
                "total_assignments": total_assignments,
                "total_stations": total_stations,
                "total_trains": total_trains,
                "total_routes": total_routes,
            },
            "station_loads": station_loads,
            "staff": staff_list,
            "trains": trains_list,
            "routes": routes_list,
        }
    ), 200


# ================================================================== #
#  ADMIN — staff
# ================================================================== #


# POST /api/v1/admin/staff
@app.route("/api/v1/admin/staff", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_staff():
    admin_id = g.user.get("id")
    data = request.get_json()
    name = (data.get("name") or "").strip()
    cnic = (data.get("cnic") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone_number") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "").strip()
    salary_raw = data.get("salary")
    shift_date = (data.get("shift_date") or "").strip()
    shift_type = (data.get("shift_type") or "Morning").strip()

    if not all([name, cnic, email, phone, password, role, salary_raw, shift_date]):
        return jsonify({"error": "All fields are required"}), 400
    if len(cnic) != 13 or not cnic.isdigit():
        return jsonify({"error": "CNIC must be exactly 13 digits"}), 400
    if len(phone) != 11 or not phone.isdigit():
        return jsonify({"error": "Phone must be exactly 11 digits"}), 400
    if shift_type not in ("Morning", "Evening"):
        return jsonify({"error": "shift_type must be Morning or Evening"}), 400
    try:
        salary = int(salary_raw)
        if salary <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Salary must be a positive integer"}), 400
    try:
        start = datetime.strptime(shift_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid shift_date, use YYYY-MM-DD"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM User WHERE cnic = ?", (cnic,))
        if cursor.fetchone():
            return jsonify({"error": "A user with this CNIC already exists"}), 409

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

        cursor.execute(
            """SELECT s.id FROM Station s
               LEFT JOIN Staff_Assignment sa ON sa.station_id = s.id
               GROUP BY s.id ORDER BY COUNT(sa.staff_id) ASC LIMIT 8"""
        )
        stations = [r["id"] for r in cursor.fetchall()]
        if not stations:
            db.rollback()
            return jsonify({"error": "No stations found. Add stations first."}), 400

        for i, sid in enumerate(stations):
            assign_date = (start + timedelta(days=i)).isoformat()
            cursor.execute(
                "INSERT INTO Staff_Assignment (staff_id, station_id, shift_date, shift_type) VALUES (?,?,?,?)",
                (user_id, sid, assign_date, shift_type),
            )

        db.commit()
        return jsonify(
            {
                "message": f"{name} created and auto-assigned to {len(stations)} stations",
                "user_id": user_id,
                "assigned_stations": stations,
            }
        ), 201
    except Exception as e:
        db.rollback()
        log_rollback("admin_create_staff", e, admin_id)
        return jsonify({"error": f"Failed to create staff: {e}"}), 500


# POST /api/v1/admin/staff/shift
@app.route("/api/v1/admin/staff/shift", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_add_shift():
    admin_id = g.user.get("id")
    data = request.get_json()
    staff_id = data.get("staff_id")
    station_id = data.get("station_id")
    shift_date = (data.get("shift_date") or "").strip()
    shift_type = (data.get("shift_type") or "Morning").strip()

    if not all([staff_id, station_id, shift_date]):
        return jsonify(
            {"error": "staff_id, station_id, and shift_date are required"}
        ), 400
    if shift_type not in ("Morning", "Evening"):
        return jsonify({"error": "shift_type must be Morning or Evening"}), 400
    try:
        datetime.strptime(shift_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid shift_date, use YYYY-MM-DD"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM Staff WHERE id = ?", (staff_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Staff member not found"}), 404

        cursor.execute("SELECT id FROM Station WHERE id = ?", (station_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Station not found"}), 404

        # No manual duplicate or 40-hour check here.
        # The DB handles both:
        #   - PK (staff_id, shift_date, shift_type) rejects duplicates
        #   - ensure_40_hour_rule trigger rejects > 8 shifts per week
        # If either fires, SQLite raises ABORT, we rollback and log it.
        cursor.execute(
            "INSERT INTO Staff_Assignment (staff_id, station_id, shift_date, shift_type) VALUES (?,?,?,?)",
            (staff_id, station_id, shift_date, shift_type),
        )
        db.commit()
        return jsonify({"message": "Shift added successfully"}), 201
    except Exception as e:
        db.rollback()
        log_rollback("admin_add_shift", e, admin_id)
        return jsonify({"error": f"Failed to add shift: {e}"}), 500


# ================================================================== #
#  ADMIN — stations
# ================================================================== #


# GET /api/v1/admin/stations
@app.route("/api/v1/admin/stations", methods=["GET"])
@token_required
@rbac_required("admin")
def admin_get_stations():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT s.id, s.name, COUNT(sa.staff_id) AS assignment_count
           FROM Station s
           LEFT JOIN Staff_Assignment sa ON sa.station_id = s.id
           GROUP BY s.id ORDER BY s.name"""
    )
    return jsonify({"stations": [dict(r) for r in cursor.fetchall()]}), 200


# POST /api/v1/admin/stations
@app.route("/api/v1/admin/stations", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_station():
    admin_id = g.user.get("id")
    data = request.get_json()
    name = (data.get("station_name") or "").strip()

    if not name:
        return jsonify({"error": "station_name is required"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM Station WHERE name = ?", (name,))
        if cursor.fetchone():
            return jsonify({"error": f"Station '{name}' already exists"}), 409

        station_id = next_id(cursor, "Station")
        cursor.execute(
            "INSERT INTO Station (id, name) VALUES (?,?)", (station_id, name)
        )
        db.commit()
        return jsonify(
            {"message": f"Station '{name}' created", "station_id": station_id}
        ), 201
    except Exception as e:
        db.rollback()
        log_rollback("admin_create_station", e, admin_id)
        return jsonify({"error": f"Failed to create station: {e}"}), 500


# ================================================================== #
#  ADMIN — trains
# ================================================================== #


# GET /api/v1/admin/trains
@app.route("/api/v1/admin/trains", methods=["GET"])
@token_required
@rbac_required("admin")
def admin_get_trains():
    db = get_db()
    cursor = db.cursor()
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
    return jsonify({"trains": [dict(r) for r in cursor.fetchall()]}), 200


# POST /api/v1/admin/trains
@app.route("/api/v1/admin/trains", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_train():
    admin_id = g.user.get("id")
    data = request.get_json()
    name = (data.get("train_name") or "").strip()

    if not name:
        return jsonify({"error": "train_name is required"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM Train WHERE name = ?", (name,))
        if cursor.fetchone():
            return jsonify({"error": f"Train '{name}' already exists"}), 409

        cursor.execute("BEGIN TRANSACTION")
        train_id = next_id(cursor, "Train")
        cursor.execute("INSERT INTO Train (id, name) VALUES (?,?)", (train_id, name))

        for cls in ("Economy", "Business", "AC"):
            for _ in range(10):
                seat_id = next_id(cursor, "Seat")
                cursor.execute(
                    "INSERT INTO Seat (id, train_id, class, status) VALUES (?,?,?,?)",
                    (seat_id, train_id, cls, "Free"),
                )

        db.commit()
        return jsonify(
            {
                "message": f"Train '{name}' created with 30 seats (10 Economy, 10 Business, 10 AC)",
                "train_id": train_id,
            }
        ), 201
    except Exception as e:
        db.rollback()
        log_rollback("admin_create_train", e, admin_id)
        return jsonify({"error": f"Failed to create train: {e}"}), 500


# ================================================================== #
#  ADMIN — routes
# ================================================================== #


# GET /api/v1/admin/routes
@app.route("/api/v1/admin/routes", methods=["GET"])
@token_required
@rbac_required("admin")
def admin_get_routes():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT r.route_id, r.route_name, COUNT(rs.id) AS station_count
           FROM Route r
           LEFT JOIN Route_Station rs ON rs.route_id = r.route_id
           GROUP BY r.route_id ORDER BY r.route_id"""
    )
    return jsonify({"routes": [dict(r) for r in cursor.fetchall()]}), 200


# POST /api/v1/admin/routes
@app.route("/api/v1/admin/routes", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_create_route():
    admin_id = g.user.get("id")
    data = request.get_json()
    route_name = (data.get("route_name") or "").strip()

    if not route_name:
        return jsonify({"error": "route_name is required"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT route_id FROM Route WHERE route_name = ?", (route_name,))
        if cursor.fetchone():
            return jsonify({"error": f"Route '{route_name}' already exists"}), 409

        cursor.execute("SELECT MAX(route_id) AS max_id FROM Route")
        row = cursor.fetchone()
        route_id = 1 if row["max_id"] is None else row["max_id"] + 1

        cursor.execute(
            "INSERT INTO Route (route_id, route_name) VALUES (?,?)",
            (route_id, route_name),
        )
        db.commit()
        return jsonify(
            {"message": f"Route '{route_name}' created", "route_id": route_id}
        ), 201
    except Exception as e:
        db.rollback()
        log_rollback("admin_create_route", e, admin_id)
        return jsonify({"error": f"Failed to create route: {e}"}), 500


# POST /api/v1/admin/routes/station
@app.route("/api/v1/admin/routes/station", methods=["POST"])
@token_required
@rbac_required("admin")
def admin_add_route_station():
    admin_id = g.user.get("id")
    data = request.get_json()
    route_id = data.get("route_id")
    station_id = data.get("station_id")
    arrival_time = (data.get("arrival_time") or "").strip() or None
    departure_time = (data.get("departure_time") or "").strip() or None

    if not all([route_id, station_id]):
        return jsonify({"error": "route_id and station_id are required"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT id FROM Route_Station WHERE route_id=? AND station_id=?",
            (route_id, station_id),
        )
        if cursor.fetchone():
            return jsonify({"error": "That station is already on this route"}), 409

        rs_id = next_id(cursor, "Route_Station")
        cursor.execute(
            "INSERT INTO Route_Station (id, route_id, station_id, arrival_time, departure_time) VALUES (?,?,?,?,?)",
            (rs_id, route_id, station_id, arrival_time, departure_time),
        )
        db.commit()
        return jsonify(
            {
                "message": "Station added to route successfully",
                "route_station_id": rs_id,
            }
        ), 201
    except Exception as e:
        db.rollback()
        log_rollback("admin_add_route_station", e, admin_id)
        return jsonify({"error": f"Failed to add station to route: {e}"}), 500


# ================================================================== #
#  STAFF
# ================================================================== #


# GET /api/v1/staff/dashboard
@app.route("/api/v1/staff/dashboard", methods=["GET"])
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
        return jsonify({"error": "Staff record not found"}), 404
    staff = dict(row)

    cursor.execute(
        """SELECT sa.shift_date, sa.shift_type, s.name AS station_name
           FROM Staff_Assignment sa
           JOIN Station s ON s.id = sa.station_id
           WHERE sa.staff_id = ? ORDER BY sa.shift_date""",
        (staff_id,),
    )
    all_assignments = [dict(r) for r in cursor.fetchall()]
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
        return f"Week of {ws.strftime('%d %b')} - {we.strftime('%d %b')}"

    grouped = defaultdict(list)
    for a in all_assignments:
        grouped[week_label(a["shift_date"])].append(a)

    return jsonify(
        {
            "staff": staff,
            "this_week_count": this_week_count,
            "total_assignments": total_assignments,
            "schedule": dict(grouped),
        }
    ), 200


if __name__ == "__main__":
    app.run(debug=True)
