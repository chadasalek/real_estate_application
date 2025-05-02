# cli.py
import os
from dotenv import load_dotenv

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError

from datetime import datetime
import re



load_dotenv()  


# CONNECTION & MENU
def get_connection():
    return psycopg2.connect(
        host     = "localhost",
        port     = "5434",
        dbname   = "hetpatel",
        user     = "hetpatel",
        password = "1234"
    )

           
            
def renter_menu(user_email):
    while True:
        print("\n--- Renter Menu ---")
        print("1) Add address")
        print("2) Add payment method")
        print("3) Search property")
        print("4) Book property")
        print("5) View my bookings")
        print("6) Logout")
        choice = input("Choice: ").strip()

        if choice == '1':
            add_address(user_email)
        elif choice == '2':
            add_credit_card(user_email)
        elif choice == '3':
            search_properties()
        elif choice == '4':
            book_property(user_email)
        elif choice == '5':
            search_bookings(user_email)
        elif choice == '6':
            break
        else:
            print("Invalid.")

      

def search_bookings(user_email):
    """
    Lists all bookings (reservations) for this renter, most recent first.
    """
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
          b.reservation_id,
          b.property_id,
          p.prop_type,
          a.city,
          b.start_date,
          b.end_date,
          b.price
        FROM Booking b
        JOIN Property p  ON b.property_id = p.property_id
        JOIN Address a   ON p.address_id    = a.address_id
        WHERE b.user_email = %s
        ORDER BY b.start_date DESC;
    """, (user_email,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("\nYou have no reservations yet.")
        return

    print(f"\nYour reservations ({len(rows)}):")
    for r in rows:
        print(
            f" • Reservation #{r['reservation_id']:>3} | Property {r['property_id']:>3} "
            f"({r['prop_type']} in {r['city']}) | {r['start_date']} → {r['end_date']} "
            f"| ${r['price']}"
        )
    print()
        
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

    # 
    email      = input("Email                 : ").strip()
    first_name = input("First name                : ").strip()
    last_name  = input("Last name                   : ").strip()

    # 
    user_type = None
    while user_type not in ("Agent", "Renter"):
        utmp = input("Type ('Agent' ou 'Renter'): ").strip().lower()
        if utmp in ("agent", "renter"):
            user_type = utmp.capitalize()
        else:
            print("→ Error.")

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

        if user_type == "Agent":
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
        print("\nSorry, no properties found with these filters.")
        print("Try different filters or check the database.")
        return

    print("\nWe found some matching property:")
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
        print(f"{email}")
    cur.close()
    conn.close()

def book_property(user_email):
    """
    1) Search or enter ID
    2) Pick dates
    3) Pick credit card
    4) Insert booking
    Typing 'b' at any prompt cancels and returns to the renter menu.
    """
    print("\n=== Book a Property ===")
    print("Type 'b' anytime to go back.\n")

    # 1) Property selection
    while True:
        choice = input("Search for a property? [Y/n]: ").strip().lower() or 'y'
        if choice == 'b':
            return
        if choice in ('y', 'yes'):
            props = search_properties(return_results=True)
            if not props:
                print("No matches—returning to menu.")
                return
            print("\nAvailable properties:")
            valid_ids = set()
            for r in props:
                valid_ids.add(r['property_id'])
                print(f"  ID {r['property_id']:>3} | {r['city']:<10} | ${r['price']:<8} | {r['description']}")
            while True:
                sel = input("Enter ID to book (or 'b'): ").strip().lower()
                if sel == 'b':
                    return
                if sel.isdigit() and int(sel) in valid_ids:
                    pid = int(sel)
                    break
                print("→ Pick a valid ID from the list.")
            break

        elif choice in ('n', 'no'):
            sel = input("Enter property ID to book (or 'b'): ").strip().lower()
            if sel == 'b':
                return
            if sel.isdigit():
                pid = int(sel)
                break
            print("→ Invalid ID; try again.")
        else:
            print("Please answer Y or N (or 'b' to back).")

    # 2) Date range
    while True:
        sd = input("Start date (YYYY-MM-DD) (or 'b'): ").strip()
        if sd.lower() == 'b': return
        ed = input("End date   (YYYY-MM-DD) (or 'b'): ").strip()
        if ed.lower() == 'b': return
        try:
            start = datetime.strptime(sd, "%Y-%m-%d").date()
            end   = datetime.strptime(ed, "%Y-%m-%d").date()
            if start > end:
                print("→ Start must be on or before end.")
                continue
            break
        except ValueError:
            print("→ Invalid format; use YYYY-MM-DD.")

    # 3) Credit card selection
    cards = view_payment_methods(user_email)
    if not cards:
        print("You have no saved credit cards. Please add one first.")
        return

    print("\nYour saved cards:")
    for i, c in enumerate(cards,  start=1):
        print(f"  {i}) {c['credit_card_num']} (exp {c['exp_date']})")
    while True:
        sel = input("Choose card number (or 'b'): ").strip().lower()
        if sel == 'b': return
        if sel.isdigit() and 1 <= int(sel) <= len(cards):
            card_num = cards[int(sel)-1]['credit_card_num']
            break
        print("→ Please pick one of the listed cards.")

    # 4) Fetch price
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT price FROM Property WHERE property_id = %s;", (pid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        print("❌ Property not found.")
        return
    prop_price = row[0]

    # 5) Insert booking
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO Booking (
                property_id, user_email, credit_card_num,
                start_date, end_date, price
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (pid, user_email, card_num, start, end, prop_price)
        )
        conn.commit()
        print("\n✅ Booking confirmed!")
    except Exception as e:
        conn.rollback()
        print("\n❌ Error booking reservation:", e)
    finally:
        cur.close()
        conn.close()

    # done—returns to renter menu
    return

def search_properties(return_results=False):
    """
    If return_results=True, returns a list of dicts matching the filters.
    Otherwise paginates & prints them as before.
    """
    # 1) Gather filters
    city = ""
    while not city:
        city = input("City (required): ").strip()

    zip_code = input("Zip code (blank=skip): ").strip()

    kind = input("Search kind ('rental','sale', blank=both): ").strip().lower()
    if kind not in ("", "rental", "sale"):
        print("Invalid kind; defaulting to both.")
        kind = ""

    desired_date = None
    if kind == "rental":
        ds = input("Desired move-in date (YYYY-MM-DD, blank=skip): ").strip()
        if ds:
            try:
                desired_date = datetime.strptime(ds, "%Y-%m-%d").date()
            except ValueError:
                print("Invalid date format; skipping date filter.")

    prop_type = input("Property type (Residential,Commercial,Land,Vacation, blank=all): ").strip().capitalize()
    if prop_type not in ("", "Residential", "Commercial", "Land", "Vacation"):
        print("Invalid type; searching all.")
        prop_type = ""

    beds = input("Min bedrooms (Residential only, blank=skip): ").strip()
    min_beds = int(beds) if beds.isdigit() else None

    pmin = input("Min price (blank=skip): ").strip()
    price_min = float(pmin) if pmin.replace('.','',1).isdigit() else None

    pmax = input("Max price (blank=skip): ").strip()
    price_max = float(pmax) if pmax.replace('.','',1).isdigit() else None

    order = input("Order by ('price','bedrooms', blank=price): ").strip().lower()
    if order not in ("price", "bedrooms", ""):
        print("Invalid order; defaulting to price.")
        order = "price"

    # 2) Build the SQL + params
    selects = ["p.property_id", "p.prop_type", "a.city", "p.price", "p.description"]
    joins   = ["FROM Property p", "JOIN Address a ON p.address_id = a.address_id"]
    where   = ["a.city = %s"]
    params  = [city]

    if zip_code:
        where.append("a.zip_code = %s")
        params.append(zip_code)

    if prop_type:
        where.append("p.prop_type = %s")
        params.append(prop_type)

    if min_beds is not None:
        joins.append("JOIN Residential_Property r ON p.property_id = r.property_id")
        selects.append("r.nb_rooms AS num_bedrooms")
        where.append("r.nb_rooms >= %s")
        params.append(min_beds)

    if price_min is not None:
        where.append("p.price >= %s")
        params.append(price_min)
    if price_max is not None:
        where.append("p.price <= %s")
        params.append(price_max)

    if kind == "rental" and desired_date:
        joins.append(
            "LEFT JOIN Booking b "
            "ON p.property_id = b.property_id "
            "AND %s BETWEEN b.start_date AND b.end_date"
        )
        # put desired_date at front for the BETWEEN
        params.insert(0, desired_date)
        where.append("b.property_id IS NULL")

    query  = "SELECT " + ", ".join(selects) + "\n" + "\n".join(joins)
    if where:
        query += "\nWHERE " + " AND ".join(where)

    if order == "bedrooms" and "num_bedrooms" in selects:
        query += "\nORDER BY num_bedrooms"
    else:
        query += "\nORDER BY p.price"

    # 3) Execute the SQL
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, params)
    results = cur.fetchall()
    cur.close()
    conn.close()

    # 4) If caller wants raw results, return them immediately
    if return_results:
        return results

    # 5) Otherwise paginate & print exactly as before
    page_size = 5
    total     = len(results)
    page      = 0

    while True:
        start = page * page_size
        end   = start + page_size
        chunk = results[start:end]

        print(f"\nShowing {start+1}-{min(end,total)} of {total} results:")
        for r in chunk:
            line = (
                f"ID {r['property_id']:>3} | {r['prop_type']:<12} | "
                f"{r['city']:<10} | ${r['price']:<8}"
            )
            if r.get("num_bedrooms") is not None:
                line += f"| Beds: {r['num_bedrooms']:<2}"
            line += f" | {r['description']}"
            print(line)

        nav = input("\n[N]ext, [P]rev, [Q]uit: ").strip().lower()
        if nav == 'n' and end < total:
            page += 1
        elif nav == 'p' and page > 0:
            page -= 1
        else:
            break

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
    """
    Ajoute une carte de crédit pour un locataire.
    - credit_card_num (13–16 digits)
    - exp_date      (YYYY-MM-DD or MMYY)
    - user_email
    """
    # 1) Card number validation
    while True:
        num = input("Card number (13-16 digits): ").strip()
        if not (num.isdigit() and 13 <= len(num) <= 16):
            print("→ Invalid. Must be 13–16 digits.")
            continue
        break

    # 2) Expiry date parsing
    while True:
        raw = input("Expiry date (YYYY-MM-DD or MMYY): ").strip()
        exp_date = None

        # Try full ISO date first
        try:
            exp_date = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            # If just MMYY, convert to the first of that month
            if re.fullmatch(r"\d{4}", raw):
                month = int(raw[:2])
                year  = int(raw[2:]) + 2000
                if 1 <= month <= 12:
                    exp_date = datetime(year, month, 1).date()
                else:
                    print("→ MMYY month must be 01–12.")
                    continue
            else:
                print("→ Invalid format. Use YYYY-MM-DD or MMYY.")
                continue

        # Ensure exp_date is not in the past
        if exp_date < datetime.today().date().replace(day=1):
            print("→ That card is already expired.")
            continue

        break

    # 3) Insert into DB
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO Credit_Card (
                credit_card_num,
                exp_date,
                user_email
            ) VALUES (%s, %s, %s);
            """,
            (num, exp_date, user_email)
        )
        conn.commit()
        print(f"✅ Credit card {num} added for {user_email}.")
    except IntegrityError as e:
        conn.rollback()
        print("❌ Failed to add credit card:", e)
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
