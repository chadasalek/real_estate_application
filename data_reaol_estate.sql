DELETE FROM Vacation;
DELETE FROM Residential_Property;
DELETE FROM Commercial;
DELETE FROM Land;
DELETE FROM Manages;
DELETE FROM Booking;
DELETE FROM Credit_Card;
DELETE FROM Agents;
DELETE FROM Prospective_Renters;
DELETE FROM Property;
DELETE FROM Neighborhood;
DELETE FROM Address;
DELETE FROM Users;

ALTER SEQUENCE address_address_id_seq RESTART WITH 1;
ALTER SEQUENCE neighborhood_neighborhood_id_seq RESTART WITH 1;
ALTER SEQUENCE property_property_id_seq RESTART WITH 1;

-- Insert Users
INSERT INTO Users (user_email, first_name, last_name, user_type) VALUES
('agent.smith@realestate.com', 'John', 'Smith', 'Agent'),
('maria.garcia@properties.com', 'Maria', 'Garcia', 'Agent'),
('renter1@email.com', 'Alice', 'Johnson', 'Renter'),
('renter2@mail.com', 'Bob', 'Williams', 'Renter'),
('renter3@example.com', 'Charlie', 'Brown', 'Renter'),
('lucas.martin@agency.com', 'Lucas', 'Martin', 'Agent'),
('emma.wilson@brokers.com', 'Emma', 'Wilson', 'Agent'),
('renter4@mail.com', 'Diana', 'Miller', 'Renter'),
('renter5@example.com', 'Ethan', 'Davis', 'Renter'),
('renter6@domain.com', 'Sophia', 'Wilson', 'Renter');


-- Insert Addresses (for users and properties)
INSERT INTO Address (street, city, state, country, zip_code, address_type) VALUES
('123 Main St', 'New York', 'NY', 'USA', '10001', 'Business'), 
('456 Oak Ave', 'Los Angeles', 'CA', 'USA', '90001', 'Business'),  
('789 Pine Rd', 'Chicago', 'IL', 'USA', '60601', 'Residential'),  
('321 Elm Ln', 'Miami', 'FL', 'USA', '33101', 'Residential'), 
('654 Beach Blvd', 'Miami', 'FL', 'USA', '33109', 'Vacation'), 
('900 Commerce St', 'Houston', 'TX', 'USA', '77002', 'Commercial'), 
('200 Farm Rd', 'Austin', 'TX', 'USA', '78701', 'Land'),
('888 Skyline Blvd', 'Denver', 'CO', 'USA', '80202', 'Business'),
('234 Maple St', 'Seattle', 'WA', 'USA', '98101', 'Residential'),
('505 Desert Rd', 'Phoenix', 'AZ', 'USA', '85001', 'Vacation'),
('789 Tech Park', 'Boston', 'MA', 'USA', '02108', 'Commercial'),
('1500 Ranch Rd', 'Dallas', 'TX', 'USA', '75201', 'Land'),
('600 Loft Ave', 'Brooklyn', 'NY', 'USA', '11201', 'Residential'),
('321 Harbor View', 'San Diego', 'CA', 'USA', '92101', 'Vacation');  

-- Insert Neighborhoods
INSERT INTO Neighborhood (name, crime_rate, nb_nearby_schools, nb_super_markets) VALUES
('Downtown', 15.75, 8, 12),
('Beachfront', 8.20, 3, 5),
('Business District', 22.30, 2, 8),
('Rural Area', 5.50, 1, 2),
('Suburban Hills', 4.80, 7, 6),
('University District', 18.90, 12, 9);

-- Insert Properties
INSERT INTO Property (prop_type, description, price, sq_foot, availability, address_id, neighborhood_id, status) VALUES
('Vacation', 'Luxury beachfront villa', 450000.00, 3000, 'Available', 5, 2, 'Rental'),
('Commercial', 'Downtown retail space', 1200000.00, 5000, 'Contingent', 6, 3, 'Sale'),
('Land', '50-acre cultivable land', 750000.00, 2178000, 'Available', 7, 4, 'Rental'),
('Residential', '3-bedroom family home', 325000.00, 1800, 'Available', 3, 1, 'Sale'),
('Vacation', 'Modern desert retreat', 320000.00, 2500, 'Available', 8, 2, 'Rental'),
('Commercial', 'Tech office space', 950000.00, 4000, 'Available', 9, 3, 'Sale'),
('Land', '30-acre ranch land', 450000.00, 1306800, 'Contingent', 10, 4, 'Sale'),
('Residential', 'Downtown loft', 650000.00, 2200, 'Available', 11, 1, 'Rental'),
('Vacation', 'Coastal luxury condo', 820000.00, 3500, 'Not available', 12, 2, 'Rental'),
('Commercial', 'Medical center', 2300000.00, 8000, 'Available', 9, 3, 'Rental'),
('Land', 'Urban empty lot', 150000.00, 43560, 'Available', 10, 1, 'Rental'),
('Residential', 'Student studio', 180000.00, 800, 'Available', 11, 5, 'Rental');

-- Insert Property Subtypes
INSERT INTO Vacation (property_id, nb_rooms) VALUES (1, 5), (5, 4), (8, 6);
INSERT INTO Commercial (property_id, type_business) VALUES (2, 'Retail'), (6, 'Tech Startup'), (9, 'Healthcare');
INSERT INTO Land (property_id, cultivable, culture_type) VALUES (3, true, 'Corn'), (7, false, NULL), (10, true, 'Mixed use');
INSERT INTO Residential_Property (property_id, nb_rooms, building_type) VALUES (4, 3, 'Single-family home'), (11, 2, 'Loft'), (12, 1, 'Studio');

-- Insert Prospective Renters
INSERT INTO Prospective_Renters (user_email, age, budget, move_in_date, preferred_location, preferred_sq_ft, address_id) VALUES
('renter1@email.com', 28, 2000.00, '2023-12-01', 'Miami, FL', 1500, 3),
('renter2@mail.com', 35, 3500.00, '2024-01-15', 'New York, NY', 2000, 4),
('renter3@example.com', 42, 5000.00, '2023-11-01', 'Los Angeles, CA', 2500, NULL),
('renter4@mail.com', 31, 2800.00, '2024-03-01', 'Denver, CO', 1800, 12),
('renter5@example.com', 26, 1500.00, '2023-12-15', 'Boston, MA', 800, NULL),
('renter6@domain.com', 45, 4200.00, '2024-06-01', 'San Diego, CA', 3000, 12);

-- Insert Agents
INSERT INTO Agents (user_email, phone_number, agency, position) VALUES
('agent.smith@realestate.com', '2125550101', 'City Real Estate', 'Senior Agent'),
('maria.garcia@properties.com', '3105550202', 'Sunset Properties', 'Managing Broker'),
('lucas.martin@agency.com', '3035550303', 'Mountain Realty', 'Commercial Specialist'),
('emma.wilson@brokers.com', '6175550404', 'Boston Propertiers', 'Leasing Manager');

-- Insert Credit Cards
INSERT INTO Credit_Card (credit_card_num, exp_date, user_email, billing_address_id) VALUES
('4111111111111111', '2025-12-01', 'renter1@email.com', 3),
('5555555555554444', '2026-03-01', 'renter2@mail.com', 4),
('378282246310005', '2027-05-01', 'renter4@mail.com', 12),
('6011111111111117', '2026-11-01', 'renter5@example.com', NULL),
('3530111333300000', '2028-02-01', 'renter6@domain.com', 12);

-- Insert Bookings
INSERT INTO Booking (credit_card_num, property_id, user_email, start_date, end_date, price) VALUES
('4111111111111111', 1, 'renter1@email.com', '2023-12-15', '2024-01-05', 13500.00),
('5555555555554444', 4, 'renter2@mail.com', '2024-02-01', '2024-02-28', 9750.00),
('378282246310005', 5, 'renter4@mail.com', '2024-04-01', '2024-04-15', 9600.00),
('6011111111111117', 12, 'renter5@example.com', '2024-01-10', '2024-01-20', 1350.00),
('3530111333300000', 8, 'renter6@domain.com', '2024-07-01', '2024-07-30', 24600.00);

-- Insert Management Relationships
INSERT INTO Manages (property_id, user_email) VALUES
(1, 'agent.smith@realestate.com'),
(2, 'maria.garcia@properties.com'),
(3, 'maria.garcia@properties.com'),
(4, 'agent.smith@realestate.com'),
(5, 'lucas.martin@agency.com'),
(6, 'emma.wilson@brokers.com'),
(7, 'lucas.martin@agency.com'),
(8, 'maria.garcia@properties.com'),
(9, 'emma.wilson@brokers.com');


