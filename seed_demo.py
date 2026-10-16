import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "farmintel.db"
DEMO_NOTE = "[DEMO DATA] Sample listing for FarmIntel presentation."

farmers = [
    ("Ravi Farms", "demo.ravi@farmintel.test", "farmer", "Kanchipuram"),
    ("Green Valley Farm", "demo.greenvalley@farmintel.test", "farmer", "Tiruvallur"),
    ("Kaveri Agro Farm", "demo.kaveri@farmintel.test", "farmer", "Chengalpattu"),
    ("Sunrise Organics", "demo.sunrise@farmintel.test", "farmer", "Vellore"),
    ("Riverbend Farm", "demo.riverbend@farmintel.test", "farmer", "Villupuram"),
    ("Village Fresh Farm", "demo.villagefresh@farmintel.test", "farmer", "Tiruvannamalai"),
]

buyers = [
    ("Chennai Fresh Wholesale", "demo.wholesale@farmintel.test", "buyer", "Koyambedu, Chennai"),
    ("Green Basket Stores", "demo.greenbasket@farmintel.test", "buyer", "Ambattur, Chennai"),
    ("Harvest Kitchen Supplies", "demo.kitchen@farmintel.test", "buyer", "Tambaram, Chennai"),
]

crops = [
    ("demo.ravi@farmintel.test", "Tomato", 500, 18, "Kanchipuram", "Fresh tomatoes; sample wholesale price."),
    ("demo.greenvalley@farmintel.test", "Onion", 1000, 25, "Tiruvallur", "Sorted onions; sample wholesale price."),
    ("demo.kaveri@farmintel.test", "Potato", 800, 22, "Chengalpattu", "Harvested potatoes; sample wholesale price."),
    ("demo.sunrise@farmintel.test", "Green Chilli", 200, 40, "Vellore", "Fresh green chillies; sample wholesale price."),
    ("demo.riverbend@farmintel.test", "Brinjal", 350, 24, "Villupuram", "Fresh brinjal; sample wholesale price."),
    ("demo.villagefresh@farmintel.test", "Cabbage", 600, 16, "Tiruvannamalai", "Fresh cabbage; sample wholesale price."),
    ("demo.ravi@farmintel.test", "Tomato", 250, 19, "Kanchipuram", "Second sample tomato lot; demo only."),
    ("demo.kaveri@farmintel.test", "Onion", 400, 24, "Chengalpattu", "Sample onion stock; demo only."),
]

requirements = [
    ("demo.wholesale@farmintel.test", "Tomato", 100, 20, "Koyambedu, Chennai"),
    ("demo.greenbasket@farmintel.test", "Onion", 500, 27, "Ambattur, Chennai"),
    ("demo.kitchen@farmintel.test", "Potato", 150, 24, "Tambaram, Chennai"),
    ("demo.wholesale@farmintel.test", "Green Chilli", 50, 42, "Koyambedu, Chennai"),
]

db = sqlite3.connect(DB_PATH)
db.execute("PRAGMA foreign_keys = ON")

try:
    # Create demo accounts only when their email is not already present.
    account_ids = {}

    for name, email, role, location in farmers + buyers:
        row = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if row:
            user_id = row[0]
        else:
            cursor = db.execute(
                """
                INSERT INTO users
                    (name, email, password_hash, role, location)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    generate_password_hash("FarmIntelDemo123!"),
                    role,
                    location,
                ),
            )
            user_id = cursor.lastrowid

        account_ids[email] = user_id

    # Insert each sample crop only once.
    for email, crop, quantity, price, location, notes in crops:
        farmer_id = account_ids[email]
        existing = db.execute(
            """
            SELECT id FROM listings
            WHERE farmer_id = ?
              AND crop = ?
              AND location = ?
              AND notes = ?
            LIMIT 1
            """,
            (farmer_id, crop, location, DEMO_NOTE + " " + notes),
        ).fetchone()

        if not existing:
            db.execute(
                """
                INSERT INTO listings
                    (farmer_id, crop, quantity_kg, price_per_kg,
                     location, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    farmer_id,
                    crop,
                    quantity,
                    price,
                    location,
                    DEMO_NOTE + " " + notes,
                ),
            )

    # Insert each sample buyer requirement only once.
    for email, crop, quantity, target_price, delivery_location in requirements:
        buyer_id = account_ids[email]
        existing = db.execute(
            """
            SELECT id FROM requirements
            WHERE buyer_id = ?
              AND crop = ?
              AND delivery_location = ?
              AND target_price = ?
            LIMIT 1
            """,
            (buyer_id, crop, delivery_location, target_price),
        ).fetchone()

        if not existing:
            db.execute(
                """
                INSERT INTO requirements
                    (buyer_id, crop, quantity_kg, target_price,
                     delivery_location)
                VALUES (?, ?, ?, ?, ?)
                """,
                (buyer_id, crop, quantity, target_price, delivery_location),
            )

    db.commit()

    print("\nFarmIntel demo data is ready!")
    print("Demo accounts:", len(farmers) + len(buyers))
    print("Crop listings:", db.execute(
        "SELECT COUNT(*) FROM listings WHERE notes LIKE '%[DEMO DATA]%'"
    ).fetchone()[0])
    print("Buyer requirements:", db.execute(
        """
        SELECT COUNT(*) FROM requirements
        WHERE buyer_id IN (
            SELECT id FROM users WHERE email LIKE 'demo.%@farmintel.test'
        )
        """
    ).fetchone()[0])
    print("\nDemo account password: FarmIntelDemo123!")
    print("All sample prices and profiles are fictional.")

except Exception:
    db.rollback()
    raise
finally:
    db.close()
