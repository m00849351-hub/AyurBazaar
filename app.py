from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    return sqlite3.connect("database.db")

# HOME + SEARCH + CATEGORY
@app.route("/")
def home():
    q = request.args.get("q")
    cat = request.args.get("category")

    con = db()

    if cat:
        products = con.execute("SELECT * FROM products WHERE category=?", (cat,)).fetchall()
    elif q:
        products = con.execute("SELECT * FROM products WHERE name LIKE ?", ('%'+q+'%',)).fetchall()
    else:
        products = con.execute("SELECT * FROM products").fetchall()

    return render_template("index.html", products=products)

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        try:
            con = db()
            con.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
            con.commit()
        except:
            return "User already exists"

        return redirect("/login")

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        user = db().execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()

        if user:
            session["user"] = u
            return redirect("/")

    return render_template("login.html")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ADD TO CART
@app.route("/add/<int:id>")
def add(id):
    cart = session.get("cart", {})

    if str(id) in cart:
        cart[str(id)] += 1
    else:
        cart[str(id)] = 1

    session["cart"] = cart
    return redirect("/cart")

# CART
@app.route("/cart")
def cart():
    con = db()
    items = session.get("cart", {})
    products = []
    total = 0

    for pid, qty in items.items():
        p = con.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if p:
            subtotal = p[2] * qty
            total += subtotal
            products.append((p, qty, subtotal))

    return render_template("cart.html", products=products, total=total)

#REMOVE FROM CART
@app.route("/remove/<int:id>")
def remove(id):
    cart = session.get("cart", {})

    if str(id) in cart:
        del cart[str(id)]

    session["cart"] = cart
    return redirect("/cart")

#PAYMENT PAGE
@app.route("/payment")
def payment():
    if "user" not in session:
        return redirect("/login")

    cart = session.get("cart", {})
    total = 0
    con = db()

    for pid, qty in cart.items():
        p = con.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if p:
            total += p[2] * qty

    return render_template("payment.html", total=total)

#PAY
@app.route("/pay_success")
def pay_success():
    if "user" not in session:
        return redirect("/login")

    con = db()
    cart = session.get("cart", {})

    for pid, qty in cart.items():
        p = con.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if p:
            for _ in range(qty):
                con.execute("INSERT INTO orders(username,product,price) VALUES(?,?,?)",
                            (session["user"], p[1], p[2]))

    con.commit()
    session["cart"] = {}

    return redirect("/orders")

# ORDER
@app.route("/order")
def order():
    if "user" not in session:
        return redirect("/login")

    con = db()
    items = session.get("cart", [])

    for i in items:
        p = con.execute("SELECT * FROM products WHERE id=?", (i,)).fetchone()
        if p:
            con.execute("INSERT INTO orders(username,product,price) VALUES(?,?,?)",
                        (session["user"], p[1], p[2]))

    con.commit()
    session["cart"] = []

    return redirect("/orders")

# VIEW ORDERS
@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect("/login")

    data = db().execute("SELECT * FROM orders WHERE username=?", (session["user"],)).fetchall()
    return render_template("orders.html", orders=data)

# ✅ ADMIN PANEL WITH IMAGE UPLOAD
@app.route("/admin", methods=["GET","POST"])
def admin():
    if "user" not in session:
        return redirect("/login")

    role = db().execute("SELECT role FROM users WHERE username=?", (session["user"],)).fetchone()

    if role[0] != "admin":
        return "Access Denied"

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        category = request.form["category"]

        file = request.files["image"]
        filename = file.filename

        # Save image
        filepath = os.path.join("static/images", filename)
        file.save(filepath)

        con = db()
        con.execute("INSERT INTO products(name,price,category,image) VALUES(?,?,?,?)",
                    (name,price,category,filename))
        con.commit()

    return render_template("admin.html")

app.run(debug=True)