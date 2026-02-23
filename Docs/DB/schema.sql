BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS Passenger(
	id int NOT NULL,
	name varchar(255) NOT NULL,
	cnic char(13) NOT NULL UNIQUE,
	email varchar(100) NOT NULL,
	password varchar(100) NOT NULL,
	phone_number char(11) NOT NULL,
	PRIMARY KEY(id)
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
	id int NOT NULL,
	name varchar(255) NOT NULL,
	role varchar(50) NOT NULL,
	phone_number char(11) NOT NULL,
	salary int CHECK (salary > 0),
	PRIMARY KEY(id)
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
	id int NOT NULL,
	name varchar(100) NOT NULL,
	PRIMARY KEY (id)
);
COMMIT;
