EXPLAIN ANALYZE
SELECT *
FROM Seat
WHERE train_id = 1
    AND status = 'Free'
    AND class = 'AC';
EXPLAIN ANALYZE
SELECT *
FROM Passenger
WHERE name = 'Ali Khan'
    and cnic = "3520112345678";
EXPLAIN ANALYZE
SELECT *
FROM Station
WHERE name = 'Lahore';
EXPLAIN ANALYZE
SELECT *
FROM Staff_Assignment
WHERE staff_id = 1
    AND shift_date = '2025-06-01'
    AND shift_type = 'Morning';
CREATE INDEX idx_seat_train_status_class ON Seat(train_id, status, class);
CREATE INDEX idx_passenger ON Passenger(name, cnic);
CREATE INDEX idx_station_name ON Station(name);
CREATE INDEX idx_staff_shift ON Staff_Assignment(staff_id, shift_date, shift_type);
EXPLAIN ANALYZE
SELECT *
FROM Seat
WHERE train_id = 1
    AND status = 'Free'
    AND class = 'AC';
EXPLAIN ANALYZE
SELECT *
FROM Passenger
WHERE email = 'ali.khan@example.com';
EXPLAIN ANALYZE
SELECT *
FROM Station
WHERE name = 'Lahore';
EXPLAIN ANALYZE
SELECT *
FROM Staff_Assignment
WHERE staff_id = 1
    AND shift_date = '2025-06-01'
    AND shift_type = 'Morning';