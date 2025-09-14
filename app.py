from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_FILE = 'data.db'

# ------------------- إعداد قاعدة البيانات ------------------- #
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # جدول البراندات
    c.execute('''
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT,
            price REAL NOT NULL
        )
    ''')
    # جدول الطلبات
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            product TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    # إضافة بيانات افتراضية للبراندات إذا كانت فارغة
    c.execute("SELECT COUNT(*) FROM brands")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO brands (name, image, price) VALUES (?, ?, ?)", [
            ("Brand A", "0773c820-6838-4623-a567-72da0cc1acfe.jpeg", 100),
            ("Brand B", "534b95d8-82d3-4206-9641-5580fdfd6b39.jpeg", 150),
        ])
    conn.commit()
    conn.close()

def get_brands():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM brands")
    brands = [{"id": row[0], "name": row[1], "image": row[2], "price": row[3]} for row in c.fetchall()]
    conn.close()
    return brands

def get_orders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders")
    orders = [{"id": row[0], "user": row[1], "product": row[2], "price": row[3], "status": row[4]} for row in c.fetchall()]
    conn.close()
    return orders

def add_order(user, product, price):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (user, product, price, status) VALUES (?, ?, ?, ?)",
              (user, product, price, "قيد الانتظار"))
    conn.commit()
    conn.close()

def update_order_db(order_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

# ------------------- Routes ------------------- #

@app.route('/')
def index():
    brands = get_brands()
    return render_template("index.html", brand_images=brands, videos=[])

@app.route('/brands')
def brands():
    brands = get_brands()
    return render_template("brands.html", brands=brands)

@app.route('/prices')
def prices():
    brands = get_brands()
    return render_template("prices.html", brands=brands)

@app.route('/videos')
def videos_page():
    return render_template("videos.html", videos=[])

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        return render_template("success.html", message="تم إرسال رسالتك بنجاح!")
    return render_template("contact.html")

@app.route('/orders')
def orders_page():
    orders = get_orders()
    return render_template("orders.html", orders=orders)

@app.route('/place_order/<int:brand_id>')
def place_order(brand_id):
    brands = get_brands()
    brand = next((b for b in brands if b["id"] == brand_id), None)
    if brand:
        add_order("زائر", brand["name"], brand["price"])
        flash(f"تم طلب {brand['name']} بنجاح!", "success")
    return redirect(url_for('brands'))

# ------------------- Admin ------------------- #
ADMIN_PASSWORD = "1234"

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_orders'))
        else:
            flash("كلمة المرور خاطئة!", "danger")
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
    if action == "complete":
        update_order_db(order_id, "تم")
    elif action == "cancel":
        update_order_db(order_id, "ملغي")
    return redirect(url_for('admin_orders'))

# ------------------- Run App ------------------- #
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)
