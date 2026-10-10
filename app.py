from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "cafe_secret_key"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("cafe.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Menu table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL
        )
    """)

    # Orders table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            items TEXT NOT NULL,
            total INTEGER NOT NULL
        )
    """)

    # Reservations table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            people INTEGER NOT NULL
        )
    """)

    # Add menu items only once
    count = conn.execute(
        "SELECT COUNT(*) FROM menu"
    ).fetchone()[0]

    if count == 0:

        menu_items = [
            ("Cappuccino",
             "Rich coffee with creamy milk foam",
             120),

            ("Cold Coffee",
             "Refreshing chilled coffee",
             100),

            ("Chicken Burger",
             "Juicy chicken burger with fresh vegetables",
             180),

            ("Veg Pizza",
             "Cheesy pizza loaded with fresh vegetables",
             200),

            ("Chocolate Cake",
             "Soft and delicious chocolate cake",
             150),

            ("Cheese Sandwich",
             "Fresh sandwich with cheese and vegetables",
             100)
        ]

        conn.executemany("""
            INSERT INTO menu
            (name, description, price)
            VALUES (?, ?, ?)
        """, menu_items)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- MENU ----------------

@app.route("/menu")
def menu():

    conn = get_db()

    items = conn.execute(
        "SELECT * FROM menu"
    ).fetchall()

    conn.close()

    return render_template(
        "menu.html",
        items=items
    )


# ---------------- CART ----------------

@app.route("/add_to_cart/<int:item_id>")
def add_to_cart(item_id):

    conn = get_db()

    item = conn.execute(
        "SELECT * FROM menu WHERE id = ?",
        (item_id,)
    ).fetchone()

    conn.close()

    if item:

        cart = session.get("cart", [])

        cart.append({
            "id": item["id"],
            "name": item["name"],
            "price": item["price"]
        })

        session["cart"] = cart

    return redirect("/menu")


@app.route("/cart")
def cart():

    cart_items = session.get("cart", [])

    total = sum(
        item["price"]
        for item in cart_items
    )

    return render_template(
        "cart.html",
        cart=cart_items,
        total=total
    )


@app.route("/clear_cart")
def clear_cart():

    session.pop("cart", None)

    return redirect("/cart")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, password))

            conn.commit()

            flash("Registration successful!")
            return redirect("/login")

        except sqlite3.IntegrityError:

            flash("Email already registered.")

        finally:

            conn.close()

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ? AND password = ?
        """, (email, password)).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/")

        else:

            flash("Invalid email or password.")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- RESERVATION ----------------

@app.route("/reservation", methods=["GET", "POST"])
def reservation():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        date = request.form["date"]
        time = request.form["time"]
        people = request.form["people"]

        conn = get_db()

        conn.execute("""
            INSERT INTO reservations
            (name, phone, date, time, people)
            VALUES (?, ?, ?, ?, ?)
        """, (name, phone, date, time, people))

        conn.commit()
        conn.close()

        flash("Table reserved successfully!")

        return redirect("/reservation")

    return render_template("reservation.html")


# ---------------- ORDER ----------------

@app.route("/order", methods=["GET", "POST"])
def order():

    cart_items = session.get("cart", [])

    if not cart_items:

        flash("Your cart is empty.")

        return redirect("/menu")

    total = sum(
        item["price"]
        for item in cart_items
    )

    if request.method == "POST":

        customer_name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]

        items = ", ".join(
            item["name"]
            for item in cart_items
        )

        conn = get_db()

        conn.execute("""
            INSERT INTO orders
            (customer_name, phone, address, items, total)
            VALUES (?, ?, ?, ?, ?)
        """, (
            customer_name,
            phone,
            address,
            items,
            total
        ))

        conn.commit()
        conn.close()

        session.pop("cart", None)

        flash("Order placed successfully!")

        return redirect("/")

    return render_template(
        "orders.html",
        total=total
    )


# ---------------- CONTACT ----------------

@app.route("/contact")
def contact():

    return render_template("contact.html")


# ---------------- RUN APP ----------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)