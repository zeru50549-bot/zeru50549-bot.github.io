import sqlite3

DB_FILE = 'brands.db'

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# عرض كل الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("الجداول الموجودة في brands.db:")
for table in tables:
    print(table[0])

conn.close()
