BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS Passenger(
    id INT NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(id) REFERENCES User(id)
);
CREATE TABLE IF NOT EXISTS Payment(
    id INT NOT NULL,
    ticket_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(ticket_id) REFERENCES Ticket(id)
);
CREATE TABLE IF NOT EXISTS Route(
    route_id INT NOT NULL,
    route_name VARCHAR(255) NOT NULL,
    PRIMARY KEY(route_id)
);
CREATE TABLE IF NOT EXISTS Route_Station(
    id INT NOT NULL,
    route_id INT NOT NULL,
    station_id INT NOT NULL,
    arrival_time TIME,
    departure_time TIME,
    UNIQUE(route_id, station_id),
    PRIMARY KEY(id),
    FOREIGN KEY(route_id) REFERENCES Route(route_id),
    FOREIGN KEY(station_id) REFERENCES Station(id)
);
CREATE TABLE IF NOT EXISTS Seat(
    id INT NOT NULL,
    train_id INT NOT NULL,
    class VARCHAR(50) CHECK(class IN ('Economy','Business','AC')),
    status VARCHAR(50) CHECK(status IN ('Free','Occupied')),
    PRIMARY KEY(id),
    FOREIGN KEY(train_id) REFERENCES Train(id)
);
CREATE TABLE IF NOT EXISTS Staff(
    id INT NOT NULL,
    role VARCHAR(50) NOT NULL,
    salary INT CHECK (salary > 0),
    PRIMARY KEY(id),
    FOREIGN KEY(id) REFERENCES User(id)
);
CREATE TABLE IF NOT EXISTS Staff_Assignment(
    staff_id INT NOT NULL,
    station_id INT NOT NULL,
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) CHECK(shift_type IN ('Morning','Evening')) NOT NULL,
    PRIMARY KEY(staff_id, shift_date, shift_type),
    FOREIGN KEY(staff_id) REFERENCES Staff(id),
    FOREIGN KEY(station_id) REFERENCES Station(id)
);
CREATE TABLE IF NOT EXISTS Station(
    id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE IF NOT EXISTS Ticket(
    id INT NOT NULL,
    train_id INT NOT NULL,
    passenger_id INT NOT NULL,
    seat_id INT NOT NULL,
    payment_id INT,
    travel_date DATE NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(train_id) REFERENCES Train(id),
    FOREIGN KEY(passenger_id) REFERENCES Passenger(id),
    FOREIGN KEY(seat_id) REFERENCES Seat(id)
);
CREATE TABLE IF NOT EXISTS Train(
    id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS User(
    id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    cnic CHAR(13) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL,
    phone_number CHAR(11) NOT NULL, role TEXT NOT NULL DEFAULT 'passenger',
    PRIMARY KEY(id)
);
CREATE VIEW passenger_bookings_view AS
SELECT
    Passenger.id AS passenger_id,
    User.name AS passenger_name,
    User.email AS passenger_email,
    Ticket.id AS ticket_id,
    Train.name AS train_name,
    Seat.class AS seat_class,
    Ticket.travel_date AS travel_date,
    Payment.amount AS payment_amount
FROM Passenger
JOIN User ON User.id = Passenger.id
JOIN Ticket ON Ticket.passenger_id = Passenger.id
JOIN Train ON Train.id = Ticket.train_id
JOIN Seat ON Seat.id = Ticket.seat_id
JOIN Payment ON Payment.ticket_id = Ticket.id
ORDER BY Ticket.travel_date;
CREATE VIEW staff_weekly_assignments_view AS
SELECT
    Staff_Assignment.staff_id AS staff_id,
    User.name AS staff_name,
    strftime('%Y-%W', Staff_Assignment.shift_date) AS week_number,
    COUNT(*) AS assignments_per_week
FROM Staff_Assignment
JOIN Staff ON Staff.id = Staff_Assignment.staff_id
JOIN User ON User.id = Staff.id
GROUP BY Staff_Assignment.staff_id, strftime('%Y-%W', Staff_Assignment.shift_date)
ORDER BY Staff_Assignment.staff_id, week_number;
CREATE VIEW train_schedule_view AS
SELECT
    Train.id AS train_id,
    Train.name AS train_name,
    Route.route_name AS route_name,
    Station.id AS station_id,
    Station.name AS station_name,
    Route_Station.arrival_time AS arrival_time,
    Route_Station.departure_time AS departure_time
FROM Train
JOIN Route_Station ON Route_Station.route_id = Train.id
JOIN Station ON Station.id = Route_Station.station_id
JOIN Route ON Route.route_id = Route_Station.route_id
ORDER BY Train.id, Route_Station.departure_time;
CREATE TRIGGER ensure_40_hour_rule
BEFORE INSERT ON Staff_Assignment
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN (
            SELECT COUNT(*)
            FROM Staff_Assignment
            WHERE staff_id = NEW.staff_id
              AND strftime('%Y-%W', shift_date) = strftime('%Y-%W', NEW.shift_date)
        ) >= 8
        THEN RAISE(ABORT, 'Staff cannot have more than 8 assignments per week')
    END;
END;
CREATE TRIGGER ensure_no_double_booking
BEFORE INSERT ON Ticket
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN (
            SELECT COUNT(*)
            FROM Ticket
            WHERE train_id = NEW.train_id
              AND seat_id = NEW.seat_id
              AND travel_date = NEW.travel_date
        ) > 0
        THEN RAISE(ABORT, 'This seat is already booked for the selected train and date')
    END;
END;
COMMIT;
