-- Transactions

START TRANSACTION;

SELECT *
FROM Staff_Assignment
WHERE staff_id = 1
AND YEARWEEK(shift_date, 1) = YEARWEEK(CURDATE(), 1)
FOR UPDATE;

INSERT INTO Staff_Assignment
(staff_id, station_id, shift_date, shift_type)
VALUES
(1, 3, CURDATE(), 'Morning');

COMMIT;

START TRANSACTION;

SELECT *
FROM Ticket
WHERE train_id = 2
AND seat_id = 14
AND travel_date = CURDATE()
FOR UPDATE;

INSERT INTO Ticket
(id, train_id, passenger_id, seat_id, payment_id, travel_date)
VALUES
(101, 2, 5, 14, NULL, CURDATE());

COMMIT;