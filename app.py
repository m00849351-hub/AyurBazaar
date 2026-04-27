from flask import Flask, render_template, redirect, session, request
from database import create_tables, connect_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# -------- USERS --------
users = {}
# -------- PRODUCTS --------
products = [
    {"id": 1, "name": "Exe Punch Tulsi Oil", "price": 399, "category": "health", "image": "images/image1.jpeg", "rating": 4.2},
    {"id": 2, "name": "Exe Aloevera Cucumber Cream", "price": 350, "category": "skin", "image": "images/image2.jpeg", "rating": 4.5},
    {"id": 3, "name": "Immunity Booster", "price": 2999, "category": "health", "image": "images/image3.jpeg", "rating": 4.7},
    {"id": 4, "name": "Eco Arogya Tea", "price": 249, "category": "food", "image": "images/image4.jpeg", "rating": 4.1},
    {"id": 5, "name": "Hair Shine Conditioner", "price": 399, "category": "hair", "image": "images/image5.jpeg", "rating": 4.4},
    {"id": 6, "name": "Body Lotion", "price": 499, "category": "body", "image": "images/image6.jpeg", "rating": 4.3}
]

def get_product(pid):
    return next((p for p in products if p["id"] == pid), None)

# -------- HOME --------
@app.route("/")
def home():
    category = request.args.get("category")
    query = request.args.get("q")

    filtered = products

    if query:
        filtered = [p for p in filtered if query.lower() in p["name"].lower()]

    if category:
        filtered = [p for p in filtered if p["category"] == category]

    return render_template("index.html", products=filtered)

# -------- PRODUCT --------
@app.route("/product/<int:id>")
def product_detail(id):
    product = get_product(id)
    if product:
        return render_template("product.html", product=product)
    return "Product not found"

# -------- SIGNUP --------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            conn.commit()
        except Exception as e:
            conn.close()
            return str(e)

        conn.close()
        return redirect("/login")

    return render_template("signup.html")

# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# -------- CART --------
@app.route("/add/<int:id>")
def add(id):
    if "user" not in session:
        return redirect("/login")

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]
    cart[str(id)] = cart.get(str(id), 0) + 1
    session["cart"] = cart

    return redirect("/cart")

@app.route("/increase/<int:id>")
def increase(id):
    if "cart" in session:
        cart = session["cart"]
        cart[str(id)] = cart.get(str(id), 0) + 1
        session["cart"] = cart
    return redirect("/cart")

@app.route("/decrease/<int:id>")
def decrease(id):
    if "cart" in session:
        cart = session["cart"]
        if str(id) in cart:
            if cart[str(id)] > 1:
                cart[str(id)] -= 1
            else:
                del cart[str(id)]
        session["cart"] = cart
    return redirect("/cart")

@app.route("/remove/<int:id>")
def remove(id):
    if "cart" in session:
        cart = session["cart"]
        if str(id) in cart:
            del cart[str(id)]
        session["cart"] = cart
    return redirect("/cart")

@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/login")

    items = []
    total = 0

    if "cart" in session:
        for pid, qty in session["cart"].items():
            p = get_product(int(pid))
            if p:
                item = p.copy()
                item["quantity"] = qty
                items.append(item)
                total += p["price"] * qty

    return render_template("cart.html", products=items, total=total)

# -------- WISHLIST --------
@app.route("/wishlist")
def wishlist():
    if "wishlist" not in session:
        session["wishlist"] = []

    items = []
    for pid in session["wishlist"]:
        p = get_product(pid)
        if p:
            items.append(p)

    return render_template("wishlist.html", products=items)


@app.route("/add_wishlist/<int:id>")
def add_wishlist(id):
    if "wishlist" not in session:
        session["wishlist"] = []

    wishlist = session["wishlist"]

    if id not in wishlist:
        wishlist.append(id)

    session["wishlist"] = wishlist   

    return redirect("/")


@app.route("/remove_wishlist/<int:id>")
def remove_wishlist(id):
    if "wishlist" in session:
        session["wishlist"] = [p for p in session["wishlist"] if p != id]

    return redirect("/wishlist")

# -------- CHECKOUT --------
@app.route("/checkout")
def checkout():
    if "user" not in session:
        return redirect("/login")

    if "cart" not in session or not session["cart"]:
        return "Cart is empty 😢"

    items = []
    total = 0

    for pid, qty in session["cart"].items():
        p = get_product(int(pid))
        if p:
            item = p.copy()
            item["quantity"] = qty
            items.append(item)
            total += p["price"] * qty

    return render_template("checkout.html", products=items, total=total)

# -------- PLACE ORDER --------
@app.route("/place_order", methods=["POST"])
def place_order():
    name = request.form["name"]
    payment = request.form["payment"]

    session.pop("cart", None)

    return render_template("success.html", name=name, payment=payment)

# -------- RECOMMENDATION --------
@app.route("/recommend", methods=["POST"])
def recommend():
    symptom = request.form.get("symptom", "").lower()

    recommended = []

    for p in products:
        if "hair" in symptom and p["category"] == "hair":
            recommended.append(p)
        elif "skin" in symptom and p["category"] == "skin":
            recommended.append(p)
        elif "immunity" in symptom and p["category"] == "health":
            recommended.append(p)

    return render_template("index.html", products=products, recommendation=recommended)

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
