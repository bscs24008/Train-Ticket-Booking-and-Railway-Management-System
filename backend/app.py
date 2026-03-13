from flask import Flask, request, jsonify, g, render_template, redirect, url_for
import sqlite3
import jwt
import datetime
from functools import wraps
import bcrypt

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
DB_PATH = "db.db"


# ---------- Database helper ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # dict-like access
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------- JWT & RBAC helpers ----------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")  # store token in cookie
        if not token:
            return redirect(url_for("login"))
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user = payload
        except jwt.ExpiredSignatureError:
            return redirect(url_for("login"))
        except jwt.InvalidTokenError:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def rbac_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "role" in g.user and g.user["role"] not in roles:
                return "Forbidden", 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


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
        cursor.execute("BEGIN TRANSACTION;")
        # Check if CNIC exists
        cursor.execute("SELECT * FROM User WHERE cnic = ?", (cnic,))
        if cursor.fetchone():
            return "User with this CNIC already exists", 409

        # Hash password
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # --- Correct manual ID generation ---
        cursor.execute("SELECT MAX(id) as max_id FROM User")
        row = cursor.fetchone()
        max_id = row["max_id"] if row["max_id"] is not None else 0
        user_id = max_id + 1

        # Insert into User
        cursor.execute(
            "INSERT INTO User (id, name, cnic, email, password, phone_number, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, cnic, email, hashed, phone, "passenger"),
        )

        # Insert into Passenger
        cursor.execute("INSERT INTO Passenger (id) VALUES (?)", (user_id,))

        db.commit()
        return redirect(url_for("login"))

    except Exception as e:
        db.rollback()
        return f"Registration failed: {str(e)}", 500


# ---------- Login Page ----------
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

    stored_hash = user["password"].encode("utf-8")

    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return "Invalid password", 401

    # Create JWT
    token = jwt.encode(
        {
            "id": user["id"],
            "role": user["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    response = None

    # Redirect depending on role
    if user["role"] == "passenger":
        response = redirect(url_for("passenger_dashboard"))

    elif user["role"] == "staff":
        response = redirect(url_for("staff_dashboard"))

    else:
        return "Invalid role", 403

    response.set_cookie("token", token, httponly=True)

    return response


@app.route("/passenger_dashboard")
@token_required
@rbac_required("passenger")
def passenger_dashboard():
    return render_template("passenger_dashboard.html", user_id=g.user["id"])


@app.route("/logout")
def logout():
    response = redirect(url_for("login"))
    response.set_cookie("token", "", expires=0)
    return response


@app.route("/my_tickets")
@token_required
def my_tickets():
    passenger_id = g.user["id"]
    db = get_db()
    cursor = db.cursor()

    # Fetch tickets for this passenger using your view
    cursor.execute(
        """
        SELECT ticket_id, train_name, seat_class, travel_date, payment_amount
        FROM passenger_bookings_view
        WHERE passenger_id = ?
        ORDER BY travel_date
        """,
        (passenger_id,),
    )
    tickets = cursor.fetchall()

    return render_template("my_tickets.html", tickets=tickets)


@app.route("/book", methods=["GET", "POST"])
@token_required
def book():
    db = get_db()
    cursor = db.cursor()

    if request.method == "GET":
        # For now, we can fetch list of trains, routes, etc.
        cursor.execute("SELECT id, name FROM Train")
        trains = cursor.fetchall()
        return render_template("book.html", trains=trains)

    # POST method — user submits booking
    train_id = request.form.get("train_id")
    seat_class = request.form.get("seat_class")
    travel_date = request.form.get("travel_date")

    if not all([train_id, seat_class, travel_date]):
        return "All fields are required", 400

    try:
        cursor.execute("BEGIN TRANSACTION;")

        # Find a free seat of requested class
        cursor.execute(
            "SELECT id FROM Seat WHERE train_id=? AND class=? AND status='Free' LIMIT 1",
            (train_id, seat_class),
        )
        seat = cursor.fetchone()
        if not seat:
            db.rollback()
            return "No available seats in this class for selected train", 409

        seat_id = seat["id"]

        # Insert ticket
        cursor.execute(
            "INSERT INTO Ticket (train_id, passenger_id, seat_id, travel_date) VALUES (?, ?, ?, ?)",
            (train_id, g.user["id"], seat_id, travel_date),
        )

        # Mark seat as occupied
        cursor.execute("UPDATE Seat SET status='Occupied' WHERE id=?", (seat_id,))

        db.commit()
        return "Ticket booked successfully!"
    except Exception as e:
        db.rollback()
        return f"Booking failed: {str(e)}", 500


@app.route("/")
def home():
    token = request.cookies.get("token")  # JWT stored in cookie
    if token:
        try:
            payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user = payload  # store user info in g

            # Redirect based on role
            if g.user.get("role") == "passenger":
                return redirect(url_for("passenger_dashboard"))
            elif g.user.get("role") == "staff":
                return redirect(url_for("staff_dashboard"))
            else:
                # Unknown role or misconfigured
                return redirect(url_for("login"))
        except jwt.ExpiredSignatureError:
            # Token expired
            return redirect(url_for("login"))
        except jwt.InvalidTokenError:
            # Invalid token
            return redirect(url_for("login"))
    else:
        # No token → not logged in
        return redirect(url_for("login"))
