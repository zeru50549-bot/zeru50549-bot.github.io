from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_FILE = 'data.db'
IMAGES_FOLDER = 'static/images/'
VIDEOS_FOLDER = 'static/videos/'

EMAIL_ADDRESS = "zeru50549@gmail.com"
EMAIL_PASSWORD = "k n s r i w t k r y x e r p a h"  # App password

ADMIN_PASSWORD = "1234"

# ------------------- Database setup ------------------- #
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT,
            video TEXT,
            price REAL NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT "pending",
            FOREIGN KEY (brand_id) REFERENCES brands (id)
        )
    ''')
    conn.commit()
    conn.close()

# ------------------- Database functions ------------------- #
def get_brands():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, image, video, price FROM brands")
    brands = [{"id": r[0], "name": r[1], "image": r[2], "video": r[3], "price": r[4]} for r in c.fetchall()]
    conn.close()
    return brands

def get_orders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT orders.id, brands.name, orders.customer_name,
               orders.phone, orders.address, orders.status, brands.price
        FROM orders
        JOIN brands ON orders.brand_id = brands.id
    """)
    orders = [{"id": r[0], "brand_name": r[1], "customer_name": r[2],
               "phone": r[3], "address": r[4], "status": r[5], "price": r[6]} for r in c.fetchall()]
    conn.close()
    return orders

def add_order(brand_id, customer_name, phone, address):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (brand_id, customer_name, phone, address) VALUES (?, ?, ?, ?)",
              (brand_id, customer_name, phone, address))
    conn.commit()
    conn.close()
    send_email_notification(customer_name, brand_id, phone, address)

# ------------------- Email notifications ------------------- #
def send_email_notification(customer_name, brand_id, phone, address):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg['Subject'] = f"New Order from {customer_name}"
    body = f"""
Order Details:
- Customer: {customer_name}
- Phone: {phone}
- Address: {address}
- Brand ID: {brand_id}
"""
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Email error:", e)

# ------------------- Routes ------------------- #
@app.route('/')
def index():
    brands = get_brands()
    return render_template("index.html", brands=brands)

@app.route('/brands')
def show_brands():
    brands = get_brands()
    return render_template("brands.html", brands=brands)

@app.route('/prices')
def show_prices():
    brands = get_brands()
    return render_template("prices.html", brands=brands)

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    brands = get_brands()
    return render_template("gallery.html", brands=brands)

@app.route('/order/<int:brand_id>', methods=['GET', 'POST'])
def order(brand_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM brands WHERE id=?", (brand_id,))
    brand = c.fetchone()
    conn.close()

    if not brand:
        return "Product not found", 404

    if request.method == "POST":
        customer_name = request.form["customer_name"]
        phone = request.form["phone"]
        address = request.form["address"]
        add_order(brand_id, customer_name, phone, address)
        flash("Order submitted successfully ✅", "success")
        return redirect(url_for("show_brands"))

    return render_template("order.html", brand={"id": brand[0], "name": brand[1], "price": brand[2]})

@app.route('/my_orders')
def my_orders():
    orders = get_orders()
    return render_template("orders.html", orders=orders)

# ------------------- Admin ------------------- #
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_orders'))
        else:
            flash("Wrong password!", "danger")
    return render_template("admin_login.html")

@app.route('/admin/orders')
def admin_orders():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    orders = get_orders()
    return render_template("admin_orders.html", orders=orders)

@app.route('/update_order/<int:order_id>/<action>')
def update_order(order_id, action):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if action == "complete":
        c.execute("UPDATE orders SET status=? WHERE id=?", ("completed", order_id))
    elif action == "cancel":
        c.execute("UPDATE orders SET status=? WHERE id=?", ("canceled", order_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_orders'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash("Logged out", "info")
    return redirect(url_for('index'))

# ------------------- User login/logout ------------------- #
@app.route('/login', methods=['GET','POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['user'] = username
            flash(f"Logged in as {username}", "success")
            return redirect(url_for('index'))
        else:
            flash("Please enter your name", "danger")
    return render_template("user_login.html")

@app.route('/logout')
def user_logout():
    session.pop('user', None)
    flash("Logged out", "info")
    return redirect(url_for('index'))

# ------------------- Add Brand (password protected) ------------------- #

@app.route("/add_brand", methods=["GET", "POST"])
def add_brand():
    if request.method == "POST":
        password = request.form.get("password")
        if password != "zero123":
            flash("❌ Wrong password", "danger")
            return redirect(url_for("add_brand"))

        name = request.form["name"]
        price = request.form["price"]
        image = request.files.get("image")
        video_file = request.files.get("video_file")   # رفع ملف فيديو

        image_path = None
        video_path = None

        # حفظ الصورة
        if image and image.filename:
            image_filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
            image_path = os.path.join("static/images", image_filename)
            image.save(image_path)

        # حفظ الفيديو (ملف فقط)
        if video_file and video_file.filename:
            video_filename = str(uuid.uuid4()) + os.path.splitext(video_file.filename)[1]
            video_path = os.path.join("static/videos", video_filename)
            video_file.save(video_path)

        # إدخال البيانات في القاعدة
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO brands (name, image, video, price) VALUES (?, ?, ?, ?)",
                  (name, image_path, video_path, price))
        conn.commit()
        conn.close()

        flash("✅ Brand added successfully", "success")
        return redirect(url_for("show_brands"))  # بيرجع لصفحة البراندات

    return render_template("add_brand.html")

# ------------------- Run Server ------------------- #
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=9000, debug=True)
