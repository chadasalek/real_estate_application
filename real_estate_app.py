# cli.py
import os
from idlelib.colorizer import prog_group_name_to_tag
from sys import excepthook

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from datetime import datetime

load_dotenv()  # lit le .env existant

# CONNECTION & MENU
def get_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD")
    )
            
def renter_menu(user_email):
    while True:
        print("\n--- Renter Menu ---")
        print("1) Add address")
        print("2) Add payment method")
        print("3) Search property")
        print("4) Book")
        print("5) Update Information")
        print("6) Logout")
        c = input("Choice: ").strip()
        if c == '1': add_address(user_email)
        elif c == '2': add_credit_card(user_email)
        elif c == '3': search_properties()
        elif c == '4': book_property(user_email)
        elif c == '5': update_renter_info(user_email)
        elif c == '6': break
        else: print("Invalid.")
        
def agent_menu(user_email):
    while True:
        print("\n--- Agent menu  ---")
        print("1) Add property")
        print("2) Search property")
        print("3) Update Information")
        print("4) Logout")
        c = input("Choice: ").strip()
        if c == '1': add_property(user_email)
        elif c == '2': search_properties()
        elif c == '3': update_agent_info(user_email)
        elif c == '4': break
        else: print("Invalid.")
        
def register_user():

    # 1) Saisie des données communes
    email      = input("Email                 : ").strip()
    first_name = input("First name                : ").strip()
    last_name  = input("Last name                   : ").strip()

    # 2) Choix du type (casse non sensible à l'entrée)
    user_type = None
    while user_type not in ("Agent", "Renter"):
        utmp = input("Type ('Agent' ou 'Renter'): ").strip().lower()
        if utmp in ("agent", "renter"):
            user_type = utmp.capitalize()
        else:
            print("→ Error.")

    # 3) Connexion et début de transaction
    conn = get_connection()
    cur  = conn.cursor()
    try:
        # 3a) INSERT commun
        cur.execute(
            """
            INSERT INTO Users (
                user_email, first_name, last_name, user_type
            )
            VALUES (%s, %s, %s, %s);
            """,
            (email, first_name, last_name, user_type)
        )

        # 3b) INSERT spécifique selon le type
        if user_type == "Agent":
            # Pour un agent, on enregistre son numéro, son agence et son poste :contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}
            phone     = input("Phone number         : ").strip()
            agency    = input("Agency name          : ").strip()
            position  = input("Position/job title  : ").strip()
            cur.execute(
                """
                INSERT INTO Agents (
                    user_email, phone_number, agency, position
                )
                VALUES (%s, %s, %s, %s);
                """,
                (email, phone, agency, position)
            )

        else:  # Renter
            # Pour un locataire, on enregistre ses préférences de budget, date et lieu :contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3}
            age        = int(input("Age                  : ").strip())
            budget     = float(input("Budget               : ").strip())
            move_in    = input("Desired move-in date (YYYY-MM-DD): ").strip()
            location   = input("Preferred location   : ").strip()
            sq_ft      = int(input("Preferred square feet: ").strip())
            cur.execute(
                """
                INSERT INTO Prospective_Renters (
                    user_email, age, budget, move_in_date, preferred_location, preferred_sq_ft
                )
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (email, age, budget, move_in, location, sq_ft)
            )

        # 4) Commit si tout s'est bien passé
        conn.commit()
        print(f"\n✅ Congrats ! You are now on our DataBase as {email} ({user_type}) !")

    except IntegrityError:
        conn.rollback()
        print("\n❌ REGISTRATION FAIL : existing email or constraint violation.")
    finally:
        cur.close()
        conn.close()

def login_user():
    email = input("Email: ").strip()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT first_name, last_name, user_type FROM Users WHERE user_email = %s;",
        (email,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        print(f"✅ Hello {row[0]} {row[1]} ({row[2]})! ")
        return email, row[2]
    print("❌ Utilisateur non trouvé.")
    return None, None

# SEARCH FUNCTIONS
def search_properties():
    """
    Let a user search properties by:
      - City
      - Desired date (for rentals)
      - Kind: rental or sale
      - Property type: Residential, Commercial, Land, Vacation
      - Min bedrooms (Residential only)
      - Price range
      - Order by price or bedrooms
    """
    # 1) Gather filters
    city = input("City: ").strip()
    while True:
        ds = input("Date (YYYY-MM-DD): ").strip()
        try:
            desired_date = datetime.strptime(ds, "%Y-%m-%d").date()
            break
        except ValueError:
            print("Invalid date format.")
    kind = ""
    while kind.lower() not in ("rental", "sale"):
        kind = input("Search kind ('rental' or 'sale'): ").strip()
    prop_type = ""
    valid_types = ("Residential", "Commercial", "Land", "Vacation")
    while prop_type.capitalize() not in valid_types:
        prop_type = input(f"Property type {valid_types}: ").strip()
    prop_type = prop_type.capitalize()

    beds = input("Min bedrooms (Residential only, leave blank to skip): ").strip()
    min_beds = int(beds) if beds.isdigit() else None

    pmin = input("Min price (leave blank to skip): ").strip()
    pmax = input("Max price (leave blank to skip): ").strip()
    price_min = float(pmin) if pmin.replace('.','',1).isdigit() else None
    price_max = float(pmax) if pmax.replace('.','',1).isdigit() else None

    order = ""
    while order.lower() not in ("price", "bedrooms"):
        order = input("Order by ('price' or 'bedrooms'): ").strip()

    # 2) Build SQL dynamically
    sql = ["SELECT p.property_id, p.prop_type, a.city, p.price, p.description"]
    joins = ["FROM Property p JOIN Address a ON p.address_id = a.address_id"]
    where = ["WHERE a.city = %s", "AND p.prop_type = %s"]
    params = [city, prop_type]

    # Subtype JOIN and select extra fields
    if prop_type == "Residential":
        sql.append(", r.nb_rooms, p.sq_foot")
        joins.append("JOIN Residential_Property r ON p.property_id = r.property_id")
        if min_beds is not None:
            where.append("AND r.nb_rooms >= %s")
            params.append(min_beds)
    elif prop_type == "Commercial":
        sql.append(", c.type_business, p.sq_foot")
        joins.append("JOIN Commercial c ON p.property_id = c.property_id")
    elif prop_type == "Land":
        sql.append(", l.culture_type, p.sq_foot")
        joins.append("JOIN Land l ON p.property_id = l.property_id")
    else:  # Vacation
        sql.append(", v.nb_rooms, p.sq_foot")
        joins.append("JOIN Vacation v ON p.property_id = v.property_id")

    # Price filters
    if price_min is not None:
        where.append("AND p.price >= %s")
        params.append(price_min)
    if price_max is not None:
        where.append("AND p.price <= %s")
        params.append(price_max)

    # Exclude booked properties if rental
    if kind.lower() == "rental":
        joins.append(
            "LEFT JOIN Booking b "
            "ON p.property_id = b.property_id "
            "AND %s BETWEEN b.start_date AND b.end_date"
        )
        params.insert(0, desired_date)  # date param for BETWEEN
        where.append("AND b.property_id IS NULL")

    # Combine all parts
    query = "\n".join(sql + joins + where)

    # ORDER BY
    if order.lower() == "price":
        query += "\nORDER BY p.price"
    else:
        # Bedrooms only exist for Residential
        if prop_type == "Residential":
            query += "\nORDER BY r.num_bedrooms"
        else:
            print("Ordering by bedrooms only supported for Residential. Ordering by price.")
            query += "\nORDER BY p.price"

    # 3) Execute and display
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, params)
    results = cur.fetchall()
    cur.close()
    conn.close()

    if not results:
        print("\nNo properties match your criteria.")
        return

    print("\nSearch Results:")
    for r in results:
        line = (
            f"ID {r['property_id']:>3} | {r['prop_type']:<12} | "
            f"{r['city']:<10} | Price: {r['price']:<8} | "
        )
        if prop_type == "Residential":
            line += f"Beds: {r['num_bedrooms']:<2} | "
        line += f"{r['description']}"
        print(line)

def list_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_email FROM users;")
    rows = cur.fetchall()
    print("\n-- Utilisateurs --")
    for email in rows:
        # user_id et email sont extraits de la ligne (tuple)
        print(f"{email}")
    cur.close()
    conn.close()

def book_property(user_email):
    pid = int(input("Entrez l'ID de la propriété à réserver: ").strip())
    start = input("Start date (YYYY-MM-DD): ").strip()
    end   = input("End date   (YYYY-MM-DD): ").strip()
    card  = input("Numéro de carte à utiliser: ").strip()
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Booking (property_id, user_email, credit_card_num, start_date, end_date) "
            "VALUES (%s, %s, %s, %s, %s);",
            (pid, user_email, card, start, end)
        )
        conn.commit()
        print("✅ Réservation effectuée !")
    except Exception as e:
        conn.rollback()
        print("❌ Erreur réservation:", e)
    finally:
        cur.close(); conn.close()

def add_address(user_email):
    """Ajoute une adresse et met à jour Prospective_Renters.address_id."""
    street    = input("Street: ").strip()
    city      = input("City  : ").strip()
    state     = input("State : ").strip()
    zipc      = input("Zip code: ").strip()
    addr_type = input("Address type (home/billing): ").strip()
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Address (street, city, state, zip_code, address_type) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING address_id;",
            (street, city, state, zipc, addr_type)
        )
        addr_id = cur.fetchone()[0]
        cur.execute(
            "UPDATE Prospective_Renters SET address_id = %s WHERE user_email = %s;",
            (addr_id, user_email)
        )
        conn.commit()
        print(f"✅ Adresse ajoutée (ID={addr_id}) pour {user_email}.")
    except Exception as e:
        conn.rollback()
        print("❌ Erreur lors de l'ajout de l'adresse:", e)
    finally:
        cur.close()
        conn.close()

def add_credit_card(user_email):
    """Ajoute une carte de crédit pour un locataire."""
    num  = input("Card number (13-16 digits): ").strip()
    exp  = input("Expiry date (YYYY-MM-DD) : ").strip()
    name = input("Name on card           : ").strip()
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Credit_Card (credit_card_num, exp_date, name_on_card, user_email) "
            "VALUES (%s, %s, %s, %s);",
            (num, exp, name, user_email)
        )
        conn.commit()
        print(f"✅ Carte ajoutée pour {user_email} (Num={num}).")
    except IntegrityError:
        conn.rollback()
        print("❌ Échec : numéro invalide ou déjà existant.")
    finally:
        cur.close()
        conn.close()

def add_property(user_email):
    """Ajoute une nouvelle propriété."""
    prop_type = input("Type (Land/Commercial/Residential/Vacation): ").strip()
    city      = input("City: ").strip()
    desc      = input("Description: ").strip()
    price     = float(input("Price: ").strip())
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Property (prop_type, city, description, price) VALUES (%s, %s, %s, %s);",
            (prop_type, city, desc, price)
        )
        cur.execute(
            "INSERT INTO Manages (property_id, user_email) "
            "SELECT currval(pg_get_serial_sequence('Property','property_id')), %s;",
            (user_email,)
        )
        conn.commit()
        print("✅ Propriété ajoutée et assignée à l'agent.")
    except Exception as e:
        conn.rollback()
        print("❌ Erreur ajout propriété:", e)
    finally:
        cur.close()
        conn.close()

def view_payment_methods(email):
    """Return a list of saved cards for this user."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT credit_card_num, exp_date "
        "FROM Credit_Card WHERE user_email = %s;",
        (email,)
    )
    cards = cur.fetchall()
    cur.close()
    conn.close()
    return cards


def update_renter_info(user_email):
        """Allow a renter to update their information"""
        conn = get_connection()
        cur = conn.cursor()

        while True:
            try:
                print("\nWhich information would you like to update?")
                print("1) First Name")
                print("2) Last Name")
                print("3) User Type")
                print("4) Budget")
                print("5) Move-in Date")
                print("6) Preferred Location")
                print("7) Preferred Square Feet")
                print("8) Credit Card")
                print("9) Address")
                print("10) Exit")

                choice = input("Choice: ").strip()

                if choice == '1':
                    new_first_name = input("Enter new first name: ").strip()
                    cur.execute(
                        "UPDATE Users SET first_name = %s WHERE user_email = %s;",
                        (new_first_name, user_email)
                    )
                    conn.commit()
                    print("Information updated successfully!")
                elif choice == '2':
                    new_last_name = input("Enter new last name: ").strip()
                    cur.execute(
                        "UPDATE Users SET last_name = %s WHERE user_email = %s;",
                        (new_last_name, user_email)
                    )
                    conn.commit()
                    print("Information updated successfully!")

                elif choice == '3':
                    new_type = input("Enter 'renter' or 'agent' here: ").strip()
                    cur.execute(
                        "UPDATE Users SET user_type = %s WHERE user_email = %s;",
                        (new_type, user_email)
                    )
                    conn.commit()
                    print("Information updated successfully!")

                elif choice == '4':
                    new_budget = input("Enter new budget: ").strip()
                    if not new_budget.isdigit():
                        print("Invalid budget. Please input a number.")
                    else:
                        budget_value = int(new_budget)
                        cur.execute(
                            "UPDATE prospective_renters SET budget = %s WHERE user_email = %s;",
                            (budget_value, user_email)
                        )
                        conn.commit()
                        print("Information updated successfully!")

                elif choice == '5':
                    new_movein_date = input("Enter new movein date: ").strip()
                    try:
                        datetime.strptime(new_movein_date, "%Y-%m-%d")
                        cur.execute(
                        "UPDATE prospective_renters SET move_in_date = %s WHERE user_email = %s;",
                        (new_movein_date, user_email)
                        )
                        conn.commit()
                        print("Information updated successfully!")
                    except ValueError:
                        print("Invalid movein date. Please enter in YYYY-MM-DD format.")

                elif choice == '6':
                    new_preferred_location = input("Enter new preferred location: ").strip()
                    cur.execute(
                        "UPDATE prospective_renters SET preferred_location = %s WHERE user_email = %s;",
                        (new_preferred_location, user_email)
                    )
                    conn.commit()
                    print("Information updated successfully!")

                elif choice == '7':
                    new_preferred_sqft = input("Enter new preferred square footage: ").strip()
                    if not new_preferred_sqft.isdigit():
                        print("Invalid square footage. Please enter a numeric value.")
                    else:
                        cur.execute(
                            "UPDATE prospective_renters SET preferred_sqft = %s WHERE user_email = %s;",
                            (new_preferred_sqft, user_email)
                    )
                        conn.commit()
                        print("Information updated successfully!")

                elif choice == '8':
                    update_cc_information(user_email)

                elif choice == '9':
                    modify_address(user_email)

                elif choice == '10':
                    break

                else:
                    print("Invalid choice.")

            except Exception as e:
                conn.rollback()
                print("Error updating information:", e)

        cur.close()
        conn.close()

def update_agent_info(user_email):
    """Allow an agent to update their information"""
    conn = get_connection()
    cur = conn.cursor()

    while True:
        try:
            print("\nWhich information would you like to update?")
            print("1) First Name")
            print("2) Last Name")
            print("3) Phone Number")
            print("4) Agency")
            print("5) Position")
            print("6) Exit")

            choice = input("Choice: ").strip()

            if choice == '1':
                new_first_name = input("Enter new first name: ").strip()
                cur.execute(
                    "UPDATE Users SET first_name = %s WHERE user_email = %s;",
                    (new_first_name, user_email)
                )
                conn.commit()
                print("Information updated successfully!")

            elif choice == '2':
                new_last_name = input("Enter new last name: ").strip()
                cur.execute(
                    "UPDATE Users SET last_name = %s WHERE user_email = %s;",
                    (new_last_name, user_email)
                )
                conn.commit()
                print("Information updated successfully!")


            elif choice == '3':
                new_phone_num = input("Enter new phone number: ").strip()
                cur.execute("SELECT COUNT(*) FROM Agents WHERE phone_number = %s;",
                            (new_phone_num,))
                if cur.fetchone()[0] > 0:
                    print("This phone number is already in use.")
                else:
                    cur.execute(
                        "UPDATE Agents SET phone_number = %s WHERE user_email = %s;",
                        (new_phone_num, user_email)
                    )
                    conn.commit()
                    print("Information updated successfully!")

            elif choice == '4':
                new_agency = input("Enter new agency: ").strip()
                cur.execute("UPDATE Agents SET agency = %s WHERE user_email = %s;",
                            (new_agency, user_email)
                            )
                conn.commit()
                print("Information updated successfully!")

            elif choice == '5':
                new_position = input("Enter new position: ").strip()
                cur.execute("UPDATE Agents SET position = %s WHERE user_email = %s;",
                            (new_position, user_email))
                conn.commit()
                print("Information updated successfully!")

            elif choice == '6':
                break

            else:
                print("Invalid choice.")



        except Exception as e:
            conn.rollback()
            print("Error updating information:", e)

    cur.close()
    conn.close()

def update_cc_information(user_email):
    """Allow a user to update their credit card information"""
    conn = get_connection()
    cur = conn.cursor()

    while True:
        print("\nWhich information would you like to update?")
        print("1) Add a new payment method")
        print("2) Modify an existing payment method")
        print("3) Delete a payment method")
        print("4) List all payment methods")
        print("5) Exit")

        choice = input("Choice: ").strip()

        if choice == '1':
            while True:
                card_num = input("Enter new card number (13-16 digits): ").strip()
                if card_num.isdigit() and 13 <= len(card_num) <= 16:
                    break
                else:
                    print("Invalid card number.")

            exp_date = input("Enter exp date (YYYY/MM/DD): ").strip()
            cur.execute(
                "INSERT INTO credit_card (credit_card_num, exp_date, user_email) VALUES (%s, %s, %s);",
                (card_num, exp_date, user_email)
            )
            conn.commit()
            print("Payment method added successfully!")


        elif choice == '2':
            while True:
                card_num = input("Enter existing card number (13-16 digits): ").strip()
                if card_num.isdigit() and 13 <= len(card_num) <= 16:
                    cur.execute(
                        "SELECT * FROM credit_card WHERE credit_card_num = %s AND user_email = %s;",
                        (card_num, user_email)
                    )
                    if cur.fetchone():
                        break
                    else:
                        print("Credit card not found.")
                else:
                    print("Invalid card number.")

            exp_date = input("Enter exp date (YYYY/MM/DD): ").strip()

            try:
                cur.execute(
                        "UPDATE credit_card SET exp_date = %s WHERE user_email = %s;",
                        (exp_date, user_email)
                )
                conn.commit()
                print("Payment method modified successfully!")
            except Exception as e:
                conn.rollback()
                print("Error updating information:", e)


        elif choice == '3':
            cur.execute(
                "SELECT credit_card_num, exp_date FROM credit_card WHERE user_email = %s;",
                (user_email,)
            )

            cards = cur.fetchall()

            if not cards:
                print("No credit cards found.")
                return

            print("Select a credit card to delete:")

            for i, card in enumerate(cards, start=1):
                print(f"{i}) Number: {card[0]}, Exp: {card[1]}, Name: {card[2]}, Type: {card[3]}")

            try:

                selection = int(input("Enter number of card to delete: ").strip())
                if selection < 1 or selection > len(cards):
                    print("Invalid selection.")
                    return

                selected_card_num = cards[selection - 1][0]
                cur.execute(

                    "DELETE FROM credit_card WHERE credit_card_num = %s AND user_email = %s;",
                    (selected_card_num, user_email)
                )
                conn.commit()
                print("Credit card deleted successfully.")
            except ValueError:
                print("Invalid input. Please enter a number.")



        elif choice == '4':
            cur.execute("SELECT credit_card_num, exp_date FROM credit_card WHERE user_email = %s;",
                        (user_email,))
            cards = cur.fetchall()

            if not cards:
                print("No credit card found.")
            else:
                print("\nSaved Credit Cards:")
                for id, (card_num, exp_date) in enumerate(cards, start=1):
                    masked = '*' * (len(card_num) - 4) + card_num[-4:]
                    print(f"{id}) Card ending in {masked}, Exp: {exp_date}")

        elif choice == '5':
            break

def modify_address(user_email):
    conn = get_connection()
    cur = conn.cursor()

    while True:
        print("\nWhat would you like to do?")
        print("1) Add new address")
        print("2) Modify an existing address")
        print("3) Delete an existing address")
        print("4) List all addresses")
        print("5) Exit")

        choice = input("Choice: ").strip()
        #street, city, state, country, zip_code, address_type
        if choice == '1':
            street = input("Enter street address: ").strip()
            city = input("Enter city: ").strip()
            state = input("Enter state: ").strip()
            zipcode = input("Enter zipcode: ").strip()
            country = input("Enter country: ").strip()
            address_type = input("Enter address type (Business, Residential, Vacation, Land, Commercial): ").strip()

            cur.execute(
                "INSERT INTO Address (street, city, state, country, zip_code, address_type) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING address_id;",
                (street, city, state, country, zipcode, address_type)
            )
            addr_id = cur.fetchone()[0]
            cur.execute(
                "UPDATE prospective_renters SET address_id = %s WHERE user_email = %s;",
                (addr_id, user_email)
            )

            conn.commit()
            print("Address added successfully!")

        elif choice == '2':
            cur.execute(
                "SELECT address_id, street, city, state, zip_code, address_type FROM Address WHERE "
                "address_id IN (SELECT address_id FROM prospective_renters WHERE user_email = %s);",
                (user_email,)
            )
            addresses = cur.fetchall()

            if not addresses:
                print("No address found.")
                return

            print("Select an address to modify: ")
            for i in range(len(addresses)):
                addr = addresses[i]
                print(f"{i+1}, {addr[1]}, {addr[2]}, {addr[3]}, {addr[4]}, (Type: {addr[5]})")

            try:
                addr_choice = int(input("Select an address to modify: ").strip())
                if addr_choice < 1 or addr_choice > len(addresses):
                    print("Invalid choice.")
                    continue

                selected_address = addresses[addr_choice - 1]
                addr_id = selected_address[0]

                street = input("Enter street address: ").strip()
                city = input("Enter city: ").strip()
                state = input("Enter state: ").strip()
                zipcode = input("Enter zipcode: ").strip()
                country = input("Enter country: ").strip()
                address_type = input("Enter address type (Business, Residential, Vacation, Land, Commercial): ").strip()

                cur.execute(
                    "UPDATE address SET street = %s, city = %s, state = %s, country = %s, zip_code = %s, address_type = %s "
                    "WHERE address_id = %s; ",
                    (street, city, state, country, zipcode, address_type, addr_id)
                )
                conn.commit()
                print("Address modified successfully!")

            except ValueError:
                print("Invalid choice.")

        elif choice == '3':
            cur.execute(
                "SELECT address_id, street, city, state, zip_code, address_type FROM Address WHERE address_id IN "
                "(SELECT address_id FROM prospective_renters WHERE user_email = %s);",
                (user_email,)
            )
            addresses = cur.fetchall()

            if not addresses:
                print("No address found.")
                return

            print("Select an address to delete:")
            for i in range(len(addresses)):
                addr = addresses[i]
                print(f"{i+1}, {addr[1]}, {addr[2]}, {addr[3]}, {addr[4]}, (Type: {addr[5]})")

            try:
                addr_choice = int(input("Enter the number of the address you'd like to delete: ").strip())
                if addr_choice < 1 or addr_choice > len(addresses):
                    print("Invalid choice.")
                    return

                selected_add = addresses[addr_choice - 1]
                addr_id = selected_add[0]

                cur.execute(
                    "DELETE FROM Address WHERE address_id = %s;",
                    (addr_id,)
                )
                cur.execute(
                    "UPDATE prospective_renters SET address_id = NULL WHERE user_email = %s;",
                    (user_email,)
                )
                conn.commit()
                print("Address deleted successfully!")

            except ValueError:
                print("Invalid selection. Please choose one of the numbers listed.")

        elif choice == '4':
            cur.execute("SELECT a.street, a.city, a.state, a.zip_code FROM address a JOIN prospective_renters r "
                        "ON r.address_id = a.address_id WHERE r.user_email = %s;",
                        (user_email,))

            user_addresses = cur.fetchall()

            if not user_addresses:
                print("No address found.")
            else:
                print("\nSaved Addresses:")
                for id, address in enumerate(user_addresses, start=1):
                    street, city, state, zip_code = address
                    print(f"{id}) Street: {street}, City: {city}, State: {state}, Zip: {zip_code}")
        elif choice == '5':
            break

        else:
            print("Invalid choice.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    while True:
        print("\n=== REAL ESTATE CLI ===")
        print("1) Login")
        print("2) Register")
        print("3) Exit")
        choice = input("Choice: ").strip()
        if choice == '1':
            email, utype = login_user()
            if email:
                ut = utype.strip().casefold()
                if ut == 'agent':
                    agent_menu(email)
                else:
                    renter_menu(email)
        elif choice == '2':
            register_user()

        elif choice == '3':
            print("Bye!")
            break
        else:
            print("Invalid.")



