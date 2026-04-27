import sqlite3

def connect_db():
    return sqlite3.connect("ayurbazaar.db")

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    def insert_products():
        conn = connect_db
        cursor = conn.cursor()

    products = [
        ("Tulsi Oil", 399, "health", "images/image1.jpeg"),
        ("Aloe Cream", 350, "skin", "images/image2.jpeg"),
        ("Immunity Booster", 2999, "health", "images/image3.jpeg"),
        ("Herbal Tea", 249, "food", "images/image4.jpeg"),
        ("Hair Conditioner", 399, "hair", "images/image5.jpeg"),
        ("Body Lotion", 499, "body", "images/image6.jpeg")
    ]

    cursor.executemany(
        "INSERT INTO products (name, price, category, image) VALUES (?, ?, ?, ?)",
        products
    )

    conn.commit()
    conn.close()