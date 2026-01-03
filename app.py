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

# ---------------- HOTWHEELS ----------------
@app.route("/hotwheels")
def hotwheels():
    all_products = load(PRODUCTS)
    products = [(p, i) for i, p in enumerate(all_products) if p.get("category") == "hotwheels"]
    return render_template("hotwheels.html", products=products, is_admin=False)

# ---------------- CUSTOM T-SHIRT ----------------
@app.route("/custom-t-shirt", methods=["GET", "POST"])
def custom_t_shirt():
    if request.method == "POST":
        size = request.form.get("size")
        qty = int(request.form.get("qty", 1))
        front_file = request.files.get("front_image")
        back_file = request.files.get("back_image")
        
        front_filename = None
        if front_file and front_file.filename:
            front_filename = secure_filename(front_file.filename)
            front_file.save(os.path.join(app.config["UPLOAD_FOLDER"], front_filename))
        
        back_filename = None
        if back_file and back_file.filename:
            back_filename = secure_filename(back_file.filename)
            back_file.save(os.path.join(app.config["UPLOAD_FOLDER"], back_filename))
        
        custom_item = {
            "name": f"Custom T-shirt ({size})",
            "size": size,
            "front_image": front_filename,
            "back_image": back_filename,
            "qty": qty,
            "price": 500
        }
        
        custom_cart = session.get("custom_cart", [])
        custom_cart.append(custom_item)
        session["custom_cart"] = custom_cart
        
        return redirect("/cart")
    
    return render_template("custom-t-shirt.html")

# ---------------- DIECAST CARS ----------------
@app.route("/diecast-cars")
def diecast_cars():
    all_products = load(PRODUCTS)
    products = [(p, i) for i, p in enumerate(all_products) if p.get("category") == "diecast-cars"]
    return render_template("diecast-cars.html", products=products, is_admin=False)

# ---------------- RC CARS ----------------
@app.route("/rc-cars")
def rc_cars():
    all_products = load(PRODUCTS)
    products = [(p, i) for i, p in enumerate(all_products) if p.get("category") == "rc-cars"]
    return render_template("rc-cars.html", products=products, is_admin=False)

# ---------------- CART ----------------
@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    custom_cart = session.get("custom_cart", [])

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

    for item in custom_cart:
        item_total = item["price"] * item["qty"]
        total += item_total

        items.append({
            "name": item["name"],
            "image": item.get("front_image", ""),
            "price": item["price"],
            "qty": item["qty"],
            "subtotal": item_total,
            "custom": True
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
    return redirect(f"{request.referrer}?added=1")
    

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
        
        # Calculate total from cart and custom_cart
        cart = session.get("cart", {})
        custom_cart = session.get("custom_cart", [])
        products = load(PRODUCTS)
        total = 0
        for index, qty in cart.items():
            index = int(index)
            if index < len(products):
                product = products[index]
                total += int(product["offer"]) * qty
        for item in custom_cart:
            total += item["price"] * item["qty"]
        
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
    "items": session.get("cart", {}),   # dict for products
    "custom_items": session.get("custom_cart", []),  # list for custom
    "total": total,
    "payment_screenshot": screenshot_filename,
    "status": "Pending"
})

        save(ORDERS, orders)

        session["cart"] = {}   # clear cart
        session["custom_cart"] = []  # clear custom cart
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
            return redirect("/admin/categories")
        else:
            error = "Invalid login"

    return render_template("admin/login.html", error=error)

# ---------------- ADMIN CATEGORIES ----------------
@app.route("/admin/categories")
def admin_categories():
    if not session.get("admin"):
        return redirect("/admin")
    return render_template("admin/categories.html")

# ---------------- ADMIN VIEW ORDERS ----------------
@app.route("/admin/view-orders")
def admin_view_orders():
    if not session.get("admin"):
        return redirect("/admin")
    return render_template("admin/view-orders.html")

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
            "category": request.form.get("category"),
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

    hotwheels_orders = [(o, orders.index(o)) for o in orders if any(products[int(i)]["category"] == "hotwheels" for i in o.get("items", {}) if i.isdigit() and int(i) < len(products))]
    custom_orders = [(o, orders.index(o)) for o in orders if o.get("custom_items")]
    diecast_orders = [(o, orders.index(o)) for o in orders if any(products[int(i)]["category"] == "diecast-cars" for i in o.get("items", {}) if i.isdigit() and int(i) < len(products))]
    rc_orders = [(o, orders.index(o)) for o in orders if any(products[int(i)]["category"] == "rc-cars" for i in o.get("items", {}) if i.isdigit() and int(i) < len(products))]

    return render_template("admin/orders.html", hotwheels_orders=hotwheels_orders, custom_orders=custom_orders, diecast_orders=diecast_orders, rc_orders=rc_orders, products=products)

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

