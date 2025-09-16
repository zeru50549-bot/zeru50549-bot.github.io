# upgrade_orders.py
import sqlite3

DB_FILE = "data.db"

def upgrade_orders_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # جلب الأعمدة الموجودة بالفعل
    c.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in c.fetchall()]

    # إضافة الأعمدة لو مش موجودة
    if "user_name" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN user_name TEXT")
        print("✅ تمت إضافة العمود user_name")

    if "user_phone" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN user_phone TEXT")
        print("✅ تمت إضافة العمود user_phone")

    if "user_address" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN user_address TEXT")
        print("✅ تمت إضافة العمود user_address")

    conn.commit()
    conn.close()
    print("🎉 الترقية تمت بنجاح!")

if __name__ == "__main__":
    upgrade_orders_table()
