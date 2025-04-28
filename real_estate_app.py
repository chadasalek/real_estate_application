# cli.py
import os
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
        print("5) Logout")
        c = input("Choice: ").strip()
        if c == '1': add_address(user_email)
        elif c == '2': add_credit_card(user_email)
        elif c == '3': search_properties()
        elif c == '4': book_property(user_email)
        elif c == '5': break
        else: print("Invalid.")
        
def agent_menu(user_email):
    while True:
        print("\n--- Agent menu  ---")
        print("1) Add property")
        print("2) Search property")
        print("3) Logout")
        c = input("Choice: ").strip()
        if c == '1': add_property(user_email)
        elif c == '2': search_properties()
        elif c == '3': break
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


if __name__ == "__main__":
    while True:
        print("\n=== REAL ESTATE CLI ===")
        print("1) Login")
        print("2) Register")
        print("3) Quit")
        choice = input("Choice: ").strip()
        if choice == '1':
            email, utype = login_user()
            if email:
                ut = utype.strip().casefold()
                if ut == 'agent': agent_menu(email)
                else : renter_menu(email)
        elif choice == '2':
            register_user()
        elif choice == '3':
            print("Bye!")
            break
        else:
            print("Invalid.")
