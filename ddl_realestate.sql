DROP TABLE IF EXISTS Vacation;
DROP TABLE IF EXISTS Residential_Property;
DROP TABLE IF EXISTS Commercial;
DROP TABLE IF EXISTS Land;
DROP TABLE IF EXISTS Manages;
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS Credit_Card;
DROP TABLE IF EXISTS Agents;
DROP TABLE IF EXISTS Prospective_Renters;
DROP TABLE IF EXISTS Property;
DROP TABLE IF EXISTS Neighborhood;
DROP TABLE IF EXISTS Address;
DROP TABLE IF EXISTS Users;

-- 1) Utilisateurs (supertype)
CREATE TABLE Users (
    user_email    VARCHAR(255) PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    user_type     VARCHAR(20)  NOT NULL
                   CHECK (user_type IN ('Agent','Renter'))
);

-- 2) Adresses
CREATE TABLE Address (
    address_id   SERIAL PRIMARY KEY,
    street       VARCHAR(100)  NOT NULL,
    city         VARCHAR(50)   NOT NULL,
    state        VARCHAR(50)   NOT NULL,
    country      VARCHAR(50)   NOT NULL,
    zip_code     CHAR(9)       NOT NULL
                   CHECK (char_length(zip_code) BETWEEN 5 AND 9),
    address_type VARCHAR(30)   NOT NULL
);

-- 3) Quartiers
CREATE TABLE Neighborhood (
    neighborhood_id   SERIAL PRIMARY KEY,
    name              VARCHAR(50)  NOT NULL,
    crime_rate        NUMERIC(5,2) CHECK (crime_rate BETWEEN 0 AND 100),
    nb_nearby_schools INTEGER     NOT NULL CHECK (nb_nearby_schools >= 0),
    nb_super_markets  INTEGER     NOT NULL CHECK (nb_super_markets >= 0)
);

-- 4) Propriétés
CREATE TABLE Property (
    property_id     SERIAL PRIMARY KEY,
    prop_type       VARCHAR(30) NOT NULL
                     CHECK (prop_type IN ('Land','Commercial','Residential','Vacation')),
    description     TEXT,
    price           NUMERIC(12,2) NOT NULL CHECK (price >= 0),
    sq_foot         INTEGER       NOT NULL CHECK (sq_foot >= 0),
    availability    VARCHAR(20)   NOT NULL
                     CHECK (availability IN ('Available','Not available','Contingent')),
    address_id      INTEGER,
    neighborhood_id INTEGER,
	status    VARCHAR(20)   NOT NULL
                     CHECK (status IN ('Sale','Rental')),
    FOREIGN KEY (address_id)      REFERENCES Address(address_id)
      ON DELETE SET NULL,
    FOREIGN KEY (neighborhood_id) REFERENCES Neighborhood(neighborhood_id)
      ON DELETE SET NULL

);

-- 5) Sous‐type : locataires potentiels
CREATE TABLE Prospective_Renters (
    user_email         VARCHAR(255) PRIMARY KEY
                         REFERENCES Users(user_email)
                           ON DELETE CASCADE,
    age                INTEGER       CHECK (age >= 18),
    budget             NUMERIC(12,2) CHECK (budget >= 0),
    move_in_date       DATE,
    preferred_location VARCHAR(100),
    preferred_sq_ft    INTEGER       CHECK (preferred_sq_ft >= 0),
    address_id         INTEGER,
    points             INTEGER       NOT NULL DEFAULT 0 CHECK (points >= 0),
    FOREIGN KEY (address_id) REFERENCES Address(address_id)
      ON DELETE SET NULL
);

-- 6) Sous‐type : agents
CREATE TABLE Agents (
    user_email  VARCHAR(255) PRIMARY KEY
                 REFERENCES Users(user_email)
                   ON DELETE CASCADE,
    phone_number CHAR(10)
                 CHECK (phone_number ~ '^[0-9]{10}$'),
    agency       VARCHAR(100) NOT NULL,
    position     VARCHAR(50)  NOT NULL
);

-- 7) Cartes de crédit
CREATE TABLE Credit_Card (
    credit_card_num VARCHAR(16) PRIMARY KEY
                     CHECK (char_length(credit_card_num) BETWEEN 13 AND 16),
    exp_date         DATE        NOT NULL,
    user_email       VARCHAR(255) NOT NULL
                     REFERENCES Prospective_Renters(user_email)
                       ON DELETE CASCADE,
    billing_address_id INTEGER
                     REFERENCES Address(address_id)
                       ON DELETE SET NULL
);

-- 8) Réservations
CREATE TABLE Booking (
    reservation_id    SERIAL PRIMARY KEY,
    credit_card_num   VARCHAR(16)
                       REFERENCES Credit_Card(credit_card_num)
                         ON DELETE SET NULL,
    property_id       INTEGER       NOT NULL
                       REFERENCES Property(property_id)
                         ON DELETE CASCADE,
    user_email        VARCHAR(255)  NOT NULL
                       REFERENCES Prospective_Renters(user_email)
                         ON DELETE CASCADE,
    start_date        DATE          NOT NULL,
    end_date          DATE          NOT NULL,
    price             NUMERIC(12,2) NOT NULL CHECK (price >= 0)
);

-- 9) Gestion (many-to-many)
CREATE TABLE Manages (
    property_id INTEGER       NOT NULL
                 REFERENCES Property(property_id)
                   ON DELETE CASCADE,
    user_email  VARCHAR(255)  NOT NULL
                 REFERENCES Agents(user_email)
                   ON DELETE CASCADE,
    PRIMARY KEY (property_id, user_email)
);

-- 10) Sous‐types de propriété
CREATE TABLE Land (
    property_id  INTEGER PRIMARY KEY
                  REFERENCES Property(property_id)
                    ON DELETE CASCADE,
    cultivable   BOOLEAN     NOT NULL,
    culture_type VARCHAR(100)
);

CREATE TABLE Commercial (
    property_id   INTEGER PRIMARY KEY
                   REFERENCES Property(property_id)
                     ON DELETE CASCADE,
    type_business VARCHAR(100) NOT NULL
);

CREATE TABLE Residential_Property (
    property_id   INTEGER PRIMARY KEY
                   REFERENCES Property(property_id)
                     ON DELETE CASCADE,
    nb_rooms      INTEGER      NOT NULL CHECK (nb_rooms > 0),
    building_type VARCHAR(100) NOT NULL
);

CREATE TABLE Vacation (
    property_id INTEGER PRIMARY KEY
                 REFERENCES Property(property_id)
                   ON DELETE CASCADE,
    nb_rooms    INTEGER     NOT NULL CHECK (nb_rooms >= 0)
);
