DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS Ticket;
DROP TABLE IF EXISTS Seat;
DROP TABLE IF EXISTS Route_Station;
DROP TABLE IF EXISTS Staff_Assignment;
DROP TABLE IF EXISTS Route;
DROP TABLE IF EXISTS Train;
DROP TABLE IF EXISTS Passenger;
DROP TABLE IF EXISTS Staff;
DROP TABLE IF EXISTS Station;
-- Now recreate the tables in the same order as before
CREATE TABLE Station(
    id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE Passenger(
    id int NOT NULL,
    name varchar(255) NOT NULL,
    cnic char(13) NOT NULL UNIQUE,
    email varchar(100) NOT NULL,
    password varchar(100) NOT NULL,
    phone_number char(11) NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE Staff(
    id int NOT NULL,
    name varchar(255) NOT NULL,
    role varchar(50) NOT NULL,
    phone_number char(11) NOT NULL,
    salary int CHECK (salary > 0),
    PRIMARY KEY(id)
);
CREATE TABLE Train(
    id int NOT NULL,
    name varchar(100) NOT NULL,
    PRIMARY KEY (id)
);
CREATE TABLE Route(
    route_id INT NOT NULL,
    route_name VARCHAR(255) NOT NULL,
    PRIMARY KEY(route_id)
);
CREATE TABLE Seat(
    id INT NOT NULL,
    train_id INT NOT NULL,
    class VARCHAR(50) CHECK(class IN ('Economy', 'Business', 'AC')),
    status VARCHAR(50) CHECK(status IN ('Free', 'Occupied')),
    PRIMARY KEY(id),
    FOREIGN KEY(train_id) REFERENCES Train(id)
);
CREATE TABLE Ticket(
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
CREATE TABLE Payment(
    id INT NOT NULL,
    ticket_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(ticket_id) REFERENCES Ticket(id)
);
DROP TABLE IF EXISTS Staff_Assignment;
CREATE TABLE Staff_Assignment(
    staff_id INT NOT NULL,
    station_id INT NOT NULL,
    shift_date DATE NOT NULL,
    shift_type VARCHAR(20) CHECK(shift_type IN ('Morning', 'Evening')) NOT NULL,
    PRIMARY KEY(staff_id, shift_date, shift_type),
    FOREIGN KEY(staff_id) REFERENCES Staff(id),
    FOREIGN KEY(station_id) REFERENCES Station(id)
);
DROP TABLE IF EXISTS Route_Station;
CREATE TABLE Route_Station(
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
INSERT INTO Train (id, name)
VALUES (1, 'Khyber Mail');
INSERT INTO Train (id, name)
VALUES (2, 'Green Line Express');
INSERT INTO Train (id, name)
VALUES (3, 'Tezgam Express');
INSERT INTO Train (id, name)
VALUES (4, 'Karachi Express');
INSERT INTO Train (id, name)
VALUES (5, 'Allama Iqbal Express');
INSERT INTO Train (id, name)
VALUES (6, 'Awam Express');
INSERT INTO Train (id, name)
VALUES (7, 'Pakistan Express');
INSERT INTO Train (id, name)
VALUES (8, 'Millat Express');
INSERT INTO Train (id, name)
VALUES (9, 'Shalimar Express');
INSERT INTO Train (id, name)
VALUES (10, 'Rehman Baba Express');
INSERT INTO Train (id, name)
VALUES (11, 'Subak Raftar Express');
INSERT INTO Train (id, name)
VALUES (12, 'Sir Syed Express');
INSERT INTO Train (id, name)
VALUES (13, 'Mehr Express');
INSERT INTO Train (id, name)
VALUES (14, 'Bolan Mail');
INSERT INTO Train (id, name)
VALUES (15, 'Quetta Express');
INSERT INTO Train (id, name)
VALUES (16, 'Hazara Express');
INSERT INTO Train (id, name)
VALUES (17, 'Jaffar Express');
INSERT INTO Train (id, name)
VALUES (18, 'Rawal Express');
INSERT INTO Train (id, name)
VALUES (19, 'Badar Express');
INSERT INTO Train (id, name)
VALUES (20, 'Ghouri Express');
INSERT INTO Station (id, name)
VALUES (1, 'Karachi Cantt');
INSERT INTO Station (id, name)
VALUES (2, 'Karachi City');
INSERT INTO Station (id, name)
VALUES (3, 'Drigh Road');
INSERT INTO Station (id, name)
VALUES (4, 'Hyderabad Junction');
INSERT INTO Station (id, name)
VALUES (5, 'Nawabshah');
INSERT INTO Station (id, name)
VALUES (6, 'Rohri Junction');
INSERT INTO Station (id, name)
VALUES (7, 'Sukkur');
INSERT INTO Station (id, name)
VALUES (8, 'Rahim Yar Khan');
INSERT INTO Station (id, name)
VALUES (9, 'Khanpur Junction');
INSERT INTO Station (id, name)
VALUES (10, 'Bahawalpur');
INSERT INTO Station (id, name)
VALUES (11, 'Lodhran Junction');
INSERT INTO Station (id, name)
VALUES (12, 'Multan Cantt');
INSERT INTO Station (id, name)
VALUES (13, 'Khanewal Junction');
INSERT INTO Station (id, name)
VALUES (14, 'Mian Channu');
INSERT INTO Station (id, name)
VALUES (15, 'Sahiwal');
INSERT INTO Station (id, name)
VALUES (16, 'Okara');
INSERT INTO Station (id, name)
VALUES (17, 'Pattoki');
INSERT INTO Station (id, name)
VALUES (18, 'Raiwind Junction');
INSERT INTO Station (id, name)
VALUES (19, 'Lahore Junction');
INSERT INTO Station (id, name)
VALUES (20, 'Lahore Cantt');
INSERT INTO Station (id, name)
VALUES (21, 'Sheikhupura');
INSERT INTO Station (id, name)
VALUES (22, 'Faisalabad');
INSERT INTO Station (id, name)
VALUES (23, 'Chiniot');
INSERT INTO Station (id, name)
VALUES (24, 'Sargodha Junction');
INSERT INTO Station (id, name)
VALUES (25, 'Jhelum');
INSERT INTO Station (id, name)
VALUES (26, 'Gujrat');
INSERT INTO Station (id, name)
VALUES (27, 'Gujranwala');
INSERT INTO Station (id, name)
VALUES (28, 'Wazirabad Junction');
INSERT INTO Station (id, name)
VALUES (29, 'Rawalpindi');
INSERT INTO Route (route_id, route_name)
VALUES (1, 'Karachi → Lahore');
INSERT INTO Route (route_id, route_name)
VALUES (2, 'Karachi → Peshawar');
INSERT INTO Route (route_id, route_name)
VALUES (3, 'Lahore → Quetta');
INSERT INTO Route (route_id, route_name)
VALUES (4, 'Rawalpindi → Karachi');
INSERT INTO Route (route_id, route_name)
VALUES (5, 'Multan → Islamabad');
-- Seats for Train 1 (Khyber Mail)
INSERT INTO Seat (id, train_id, class, status)
VALUES (1, 1, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (2, 1, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (3, 1, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (4, 1, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (5, 1, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (6, 1, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (7, 1, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (8, 1, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (9, 1, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (10, 1, 'AC', 'Free');
-- Seats for Train 2 (Green Line Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (11, 2, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (12, 2, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (13, 2, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (14, 2, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (15, 2, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (16, 2, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (17, 2, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (18, 2, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (19, 2, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (20, 2, 'Economy', 'Free');
-- Seats for Train 3 (Tezgam Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (21, 3, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (22, 3, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (23, 3, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (24, 3, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (25, 3, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (26, 3, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (27, 3, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (28, 3, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (29, 3, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (30, 3, 'Economy', 'Free');
-- Seats for Train 4 (Karachi Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (31, 4, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (32, 4, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (33, 4, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (34, 4, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (35, 4, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (36, 4, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (37, 4, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (38, 4, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (39, 4, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (40, 4, 'Economy', 'Free');
-- Seats for Train 5 (Allama Iqbal Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (41, 5, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (42, 5, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (43, 5, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (44, 5, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (45, 5, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (46, 5, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (47, 5, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (48, 5, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (49, 5, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (50, 5, 'Economy', 'Free');
-- Seats for Train 6 (Awam Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (51, 6, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (52, 6, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (53, 6, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (54, 6, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (55, 6, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (56, 6, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (57, 6, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (58, 6, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (59, 6, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (60, 6, 'Economy', 'Free');
-- Seats for Train 7 (Pakistan Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (61, 7, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (62, 7, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (63, 7, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (64, 7, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (65, 7, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (66, 7, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (67, 7, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (68, 7, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (69, 7, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (70, 7, 'Economy', 'Free');
-- Seats for Train 8 (Millat Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (71, 8, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (72, 8, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (73, 8, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (74, 8, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (75, 8, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (76, 8, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (77, 8, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (78, 8, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (79, 8, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (80, 8, 'Economy', 'Free');
-- Seats for Train 9 (Shalimar Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (81, 9, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (82, 9, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (83, 9, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (84, 9, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (85, 9, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (86, 9, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (87, 9, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (88, 9, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (89, 9, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (90, 9, 'Economy', 'Free');
-- Seats for Train 10 (Rehman Baba Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (91, 10, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (92, 10, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (93, 10, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (94, 10, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (95, 10, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (96, 10, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (97, 10, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (98, 10, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (99, 10, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (100, 10, 'Economy', 'Free');
-- Seats for Train 11 (Subak Raftar Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (101, 11, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (102, 11, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (103, 11, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (104, 11, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (105, 11, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (106, 11, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (107, 11, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (108, 11, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (109, 11, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (110, 11, 'Economy', 'Free');
-- Seats for Train 12 (Sir Syed Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (111, 12, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (112, 12, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (113, 12, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (114, 12, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (115, 12, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (116, 12, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (117, 12, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (118, 12, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (119, 12, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (120, 12, 'Economy', 'Free');
-- Seats for Train 13 (Mehr Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (121, 13, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (122, 13, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (123, 13, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (124, 13, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (125, 13, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (126, 13, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (127, 13, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (128, 13, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (129, 13, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (130, 13, 'Economy', 'Free');
-- Seats for Train 14 (Bolan Mail)
INSERT INTO Seat (id, train_id, class, status)
VALUES (131, 14, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (132, 14, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (133, 14, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (134, 14, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (135, 14, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (136, 14, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (137, 14, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (138, 14, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (139, 14, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (140, 14, 'Economy', 'Free');
-- Seats for Train 15 (Quetta Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (141, 15, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (142, 15, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (143, 15, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (144, 15, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (145, 15, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (146, 15, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (147, 15, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (148, 15, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (149, 15, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (150, 15, 'Economy', 'Free');
-- Seats for Train 16 (Hazara Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (151, 16, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (152, 16, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (153, 16, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (154, 16, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (155, 16, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (156, 16, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (157, 16, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (158, 16, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (159, 16, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (160, 16, 'Economy', 'Free');
-- Seats for Train 17 (Jaffar Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (161, 17, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (162, 17, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (163, 17, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (164, 17, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (165, 17, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (166, 17, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (167, 17, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (168, 17, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (169, 17, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (170, 17, 'Economy', 'Free');
-- Seats for Train 18 (Rawal Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (171, 18, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (172, 18, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (173, 18, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (174, 18, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (175, 18, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (176, 18, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (177, 18, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (178, 18, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (179, 18, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (180, 18, 'Economy', 'Free');
-- Seats for Train 19 (Badar Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (181, 19, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (182, 19, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (183, 19, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (184, 19, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (185, 19, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (186, 19, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (187, 19, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (188, 19, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (189, 19, 'AC', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (190, 19, 'Economy', 'Free');
-- Seats for Train 20 (Ghouri Express)
INSERT INTO Seat (id, train_id, class, status)
VALUES (191, 20, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (192, 20, 'Economy', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (193, 20, 'Business', 'Free');
INSERT INTO Seat (id, train_id, class, status)
VALUES (194, 20, 'Business', 'Free');
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        1,
        'Ali Khan',
        '3520112345678',
        'ali.khan@example.com',
        'pass123',
        '03001234567'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        2,
        'Ayesha Iqbal',
        '3520212345678',
        'ayesha.iqbal@example.com',
        'pass123',
        '03007654321'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        3,
        'Bilal Ahmed',
        '3520312345678',
        'bilal.ahmed@example.com',
        'pass123',
        '03009876543'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        4,
        'Fatima Noor',
        '3520412345678',
        'fatima.noor@example.com',
        'pass123',
        '03006543210'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        5,
        'Hassan Raza',
        '3520512345678',
        'hassan.raza@example.com',
        'pass123',
        '03003456789'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        6,
        'Sara Malik',
        '3520612345678',
        'sara.malik@example.com',
        'pass123',
        '03001239876'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        7,
        'Usman Farooq',
        '3520712345678',
        'usman.farooq@example.com',
        'pass123',
        '03009871234'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        8,
        'Zainab Ali',
        '3520812345678',
        'zainab.ali@example.com',
        'pass123',
        '03006547812'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        9,
        'Omar Shah',
        '3520912345678',
        'omar.shah@example.com',
        'pass123',
        '03003451234'
    );
INSERT INTO Passenger (id, name, cnic, email, password, phone_number)
VALUES (
        10,
        'Mariam Khan',
        '3521012345678',
        'mariam.khan@example.com',
        'pass123',
        '03001237654'
    );
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (1, 1, 1, 1, 1, '2026-03-01');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (2, 2, 2, 11, 2, '2026-03-02');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (3, 3, 3, 21, 3, '2026-03-03');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (4, 4, 4, 31, 4, '2026-03-04');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (5, 5, 5, 41, 5, '2026-03-05');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (6, 6, 6, 51, 6, '2026-03-06');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (7, 7, 7, 61, 7, '2026-03-07');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (8, 8, 8, 71, 8, '2026-03-08');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (9, 9, 9, 81, 9, '2026-03-09');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (10, 10, 10, 91, 10, '2026-03-10');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (11, 11, 1, 101, 11, '2026-03-11');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (12, 12, 2, 111, 12, '2026-03-12');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (13, 13, 3, 121, 13, '2026-03-13');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (14, 14, 4, 131, 14, '2026-03-14');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (15, 15, 5, 141, 15, '2026-03-15');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (16, 16, 6, 151, 16, '2026-03-16');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (17, 17, 7, 161, 17, '2026-03-17');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (18, 18, 8, 171, 18, '2026-03-18');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (19, 19, 9, 181, 19, '2026-03-19');
INSERT INTO Ticket (
        id,
        train_id,
        passenger_id,
        seat_id,
        payment_id,
        travel_date
    )
VALUES (20, 20, 10, 191, 20, '2026-03-20');
INSERT INTO Payment (id, ticket_id, amount)
VALUES (1, 1, 1200.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (2, 2, 2000.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (3, 3, 1500.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (4, 4, 1300.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (5, 5, 1400.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (6, 6, 1250.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (7, 7, 1800.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (8, 8, 1600.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (9, 9, 1350.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (10, 10, 1550.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (11, 11, 1200.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (12, 12, 2000.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (13, 13, 1500.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (14, 14, 1300.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (15, 15, 1400.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (16, 16, 1250.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (17, 17, 1800.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (18, 18, 1600.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (19, 19, 1350.00);
INSERT INTO Payment (id, ticket_id, amount)
VALUES (20, 20, 1550.00);
INSERT INTO Staff
VALUES (1, 'Muhammad Imran', 'Driver', '03011234567', 80000);
INSERT INTO Staff
VALUES (
        2,
        'Ali Raza',
        'Assistant Driver',
        '03022345678',
        55000
    );
INSERT INTO Staff
VALUES (3, 'Kashif Mehmood', 'Guard', '03033456789', 60000);
INSERT INTO Staff
VALUES (
        4,
        'Usman Tariq',
        'Ticket Examiner',
        '03044567890',
        50000
    );
INSERT INTO Staff
VALUES (5, 'Hassan Javed', 'Attendant', '03055678901', 40000);
INSERT INTO Staff
VALUES (6, 'Bilal Ahmed', 'Driver', '03066789012', 82000);
INSERT INTO Staff
VALUES (
        7,
        'Sajid Iqbal',
        'Assistant Driver',
        '03077890123',
        56000
    );
INSERT INTO Staff
VALUES (8, 'Zeeshan Malik', 'Guard', '03088901234', 61000);
INSERT INTO Staff
VALUES (
        9,
        'Fahad Khan',
        'Ticket Examiner',
        '03099012345',
        52000
    );
INSERT INTO Staff
VALUES (
        10,
        'Hamza Shahid',
        'Attendant',
        '03110123456',
        39000
    );
INSERT INTO Staff
VALUES (11, 'Rizwan Haider', 'Driver', '03121234567', 83000);
INSERT INTO Staff
VALUES (
        12,
        'Noman Akhtar',
        'Assistant Driver',
        '03132345678',
        57000
    );
INSERT INTO Staff
VALUES (13, 'Adeel Hussain', 'Guard', '03143456789', 62000);
INSERT INTO Staff
VALUES (
        14,
        'Imtiaz Ali',
        'Ticket Examiner',
        '03154567890',
        51000
    );
INSERT INTO Staff
VALUES (
        15,
        'Farhan Saeed',
        'Attendant',
        '03165678901',
        39500
    );
INSERT INTO Staff
VALUES (
        16,
        'Saeed Akhtar',
        'Station Manager',
        '03176789012',
        95000
    );
INSERT INTO Staff
VALUES (
        17,
        'Naveed Iqbal',
        'Station Manager',
        '03187890123',
        92000
    );
INSERT INTO Staff
VALUES (
        18,
        'Tariq Bashir',
        'Station Manager',
        '03198901234',
        94000
    );
INSERT INTO Staff
VALUES (
        19,
        'Junaid Farooq',
        'Station Manager',
        '03209012345',
        91000
    );
INSERT INTO Staff
VALUES (
        20,
        'Kamran Ashraf',
        'Station Manager',
        '03210123456',
        93000
    );
INSERT INTO Route_Station
VALUES (1, 1, 1, NULL, '08:00');
INSERT INTO Route_Station
VALUES (2, 1, 5, '11:30', '11:40');
INSERT INTO Route_Station
VALUES (3, 1, 8, '14:30', '14:40');
INSERT INTO Route_Station
VALUES (4, 1, 12, '18:30', '18:45');
INSERT INTO Route_Station
VALUES (5, 1, 15, '21:30', NULL);
INSERT INTO Route_Station
VALUES (6, 2, 15, NULL, '07:30');
INSERT INTO Route_Station
VALUES (7, 2, 18, '09:00', '09:05');
INSERT INTO Route_Station
VALUES (8, 2, 20, '11:15', '11:20');
INSERT INTO Route_Station
VALUES (9, 2, 22, '13:00', NULL);
INSERT INTO Route_Station
VALUES (10, 3, 1, NULL, '09:00');
INSERT INTO Route_Station
VALUES (11, 3, 6, '13:30', '13:45');
INSERT INTO Route_Station
VALUES (12, 3, 9, '18:10', '18:25');
INSERT INTO Route_Station
VALUES (13, 3, 14, '23:40', NULL);
INSERT INTO Route_Station
VALUES (14, 4, 25, NULL, '06:30');
INSERT INTO Route_Station
VALUES (15, 4, 22, '08:30', '08:35');
INSERT INTO Route_Station
VALUES (16, 4, 20, '10:10', '10:15');
INSERT INTO Route_Station
VALUES (17, 4, 15, '13:00', NULL);
INSERT INTO Route_Station
VALUES (18, 5, 12, NULL, '10:00');
INSERT INTO Route_Station
VALUES (19, 5, 13, '11:20', '11:25');
INSERT INTO Route_Station
VALUES (20, 5, 16, '13:40', '13:45');
INSERT INTO Route_Station
VALUES (21, 5, 18, '16:10', NULL);
INSERT INTO Staff_Assignment
VALUES (1, 1, '2025-06-01', 'Morning');
INSERT INTO Staff_Assignment
VALUES (2, 1, '2025-06-01', 'Evening');
INSERT INTO Staff_Assignment
VALUES (3, 2, '2025-06-01', 'Morning');
INSERT INTO Staff_Assignment
VALUES (4, 2, '2025-06-01', 'Evening');
INSERT INTO Staff_Assignment
VALUES (5, 3, '2025-06-01', 'Morning');
INSERT INTO Staff_Assignment
VALUES (6, 3, '2025-06-01', 'Evening');
INSERT INTO Staff_Assignment
VALUES (7, 4, '2025-06-01', 'Morning');
INSERT INTO Staff_Assignment
VALUES (8, 4, '2025-06-01', 'Evening');
INSERT INTO Staff_Assignment
VALUES (9, 5, '2025-06-01', 'Morning');
INSERT INTO Staff_Assignment
VALUES (10, 5, '2025-06-01', 'Evening');
INSERT INTO Staff_Assignment
VALUES (11, 6, '2025-06-02', 'Morning');
INSERT INTO Staff_Assignment
VALUES (12, 6, '2025-06-02', 'Evening');
INSERT INTO Staff_Assignment
VALUES (13, 7, '2025-06-02', 'Morning');
INSERT INTO Staff_Assignment
VALUES (14, 7, '2025-06-02', 'Evening');
INSERT INTO Staff_Assignment
VALUES (15, 8, '2025-06-02', 'Morning');
INSERT INTO Staff_Assignment
VALUES (16, 8, '2025-06-02', 'Evening');
INSERT INTO Staff_Assignment
VALUES (17, 9, '2025-06-02', 'Morning');
INSERT INTO Staff_Assignment
VALUES (18, 9, '2025-06-02', 'Evening');
INSERT INTO Staff_Assignment
VALUES (19, 10, '2025-06-02', 'Morning');
INSERT INTO Staff_Assignment
VALUES (20, 10, '2025-06-02', 'Evening');
CREATE TRIGGER trg_staff_weekly_limit BEFORE
INSERT ON Staff_Assignment FOR EACH ROW BEGIN -- Count assignments for the same staff in the same week
SELECT CASE
        WHEN (
            SELECT COUNT(*)
            FROM Staff_Assignment
            WHERE staff_id = NEW.staff_id
                AND strftime('%Y-%W', shift_date) = strftime('%Y-%W', NEW.shift_date)
        ) >= 8 THEN RAISE(
            ABORT,
            'Staff cannot have more than 8 assignments per week'
        )
    END;
END;
-- 2️⃣ Trigger: Prevent double booking of seats on the same train & date
CREATE TRIGGER trg_ticket_no_double_booking BEFORE
INSERT ON Ticket FOR EACH ROW BEGIN
SELECT CASE
        WHEN (
            SELECT COUNT(*)
            FROM Ticket
            WHERE train_id = NEW.train_id
                AND seat_id = NEW.seat_id
                AND travel_date = NEW.travel_date
        ) > 0 THEN RAISE(
            ABORT,
            'This seat is already booked for the selected train and date'
        )
    END;
END;