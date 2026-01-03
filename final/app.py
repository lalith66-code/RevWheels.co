from flask import Flask, render_template, request, redirect, session
import os, json 
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")

PRODUCTS = os.path.join(DATA_DIR, "products.json")
ORDERS = os.path.join(DATA_DIR, "orders.json")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- HELPERS ----------------
def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- ADMINS ----------------
ADMINS = {
    "prithick": "rocket2026",
    "lalith": "lalithniksha6645"
}

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")

# ---------------- SHOP ----------------
@app.route("/shop")
def shop():
    products = load(PRODUCTS)
    return render_template("shop.html", products=products)

# ---------------- CART ----------------
@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    cart = session.get("cart", {})

    # convert old list cart to new dict format
    if isinstance(cart, list):
        new_cart = {}
        for i in cart:
            i = str(i)
            new_cart[i] = new_cart.get(i, 0) + 1
        cart = new_cart
        session["cart"] = cart

    products = load(PRODUCTS)

    items = []
    total = 0

    for index, qty in cart.items():
        index = int(index)
        if index < len(products):
            product = products[index]
            product_total = int(product["offer"]) * qty
            total += product_total

            items.append({
                "name": product["name"],
                "image": product["image"],
                "price": product["offer"],
                "qty": qty,
                "subtotal": product_total,
                "index": index
            })

    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add/<int:index>", methods=["POST"])
def add_to_cart(index):
    cart = session.get("cart")

    # 🔒 convert old list cart to dict
    if not isinstance(cart, dict):
        cart = {}

    index = str(index)

    if index in cart:
        cart[index] += 1
    else:
        cart[index] = 1

    session["cart"] = cart
    return redirect("/shop")
    

@app.route("/cart/update/<int:index>", methods=["POST"])
def update_cart(index):
    cart = session.get("cart", {})
    qty = int(request.form.get("qty", 1))
    if qty <= 0:
        cart.pop(str(index), None)
    else:
        cart[str(index)] = qty
    session["cart"] = cart
    return redirect("/cart")


# ---------------- CHECKOUT ----------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        orders = load(ORDERS)
        
        # Calculate total from cart
        cart = session.get("cart", {})
        products = load(PRODUCTS)
        total = 0
        for index, qty in cart.items():
            index = int(index)
            if index < len(products):
                product = products[index]
                total += int(product["offer"]) * qty
        
        # Handle payment screenshot
        payment_file = request.files.get("payment_screenshot")
        screenshot_filename = None
        if payment_file and payment_file.filename:
            screenshot_filename = secure_filename(payment_file.filename)
            payment_file.save(os.path.join(app.config["UPLOAD_FOLDER"], screenshot_filename))
        
        orders.append({
    "name": request.form["name"],
    "phone": request.form["phone"],
    "email": request.form["email"],
    "address": request.form["address"],
    "items": session.get("cart", {}),   # ✅ MUST be dict
    "total": total,
    "payment_screenshot": screenshot_filename,
    "status": "Pending"
})

        save(ORDERS, orders)

        session["cart"] = {}   # clear cart
        return render_template("success.html")

    return render_template("checkout.html")



# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None

    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")

        if not user or not pw:
            error = "Missing username or password"
        elif ADMINS.get(user) == pw:
            session["admin"] = user
            return redirect("/admin/dashboard")
        else:
            error = "Invalid login"

    return render_template("admin/login.html", error=error)

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    products = load(PRODUCTS)

    if request.method == "POST":
        image = request.files.get("image")

        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        else:
            filename = "default.png"

        products.append({
            "name": request.form.get("name"),
            "image": filename,
            "price": request.form.get("price"),
            "offer": request.form.get("offer"),
            "deal": request.form.get("deal")
        })

        save(PRODUCTS, products)
        return redirect("/admin/dashboard")

    return render_template("admin/dashboard.html", products=products)

# ---------------- EDIT PRODUCT ----------------
@app.route("/admin/edit/<int:i>", methods=["GET", "POST"])
def edit_product(i):
    if not session.get("admin"):
        return redirect("/admin")

    products = load(PRODUCTS)
    product = products[i]

    if request.method == "POST":
        product["name"] = request.form.get("name")
        product["price"] = request.form.get("price")
        product["offer"] = request.form.get("offer")
        product["deal"] = request.form.get("deal")

        image = request.files.get("image")
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            product["image"] = filename

        save(PRODUCTS, products)
        return redirect("/admin/dashboard")

    return render_template("admin/edit.html", p=product)

# ---------------- DELETE PRODUCT ----------------
@app.route("/admin/delete/<int:i>")
def delete_product(i):
    if not session.get("admin"):
        return redirect("/admin")

    products = load(PRODUCTS)
    products.pop(i)
    save(PRODUCTS, products)

    return redirect("/admin/dashboard")

# ---------------- ADMIN ORDERS ----------------
@app.route("/admin/orders")
def admin_orders():
    if not session.get("admin"):
        return redirect("/admin")

    orders = load(ORDERS)
    products = load(PRODUCTS)
    return render_template("admin/orders.html", orders=orders, products=products)

# ---------------- UPDATE ORDER STATUS ----------------
@app.route("/admin/order/status/<int:i>", methods=["POST"])
def update_order_status(i):
    if not session.get("admin"):
        return redirect("/admin")

    orders = load(ORDERS)
    orders[i]["status"] = request.form.get("status")
    save(ORDERS, orders)

    return redirect("/admin/orders")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

