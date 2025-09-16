import os
import shutil

# اسم النسخة القديمة والنسخة الجديدة
old_project = os.path.expanduser("~/brands_website")
new_project = os.path.expanduser("~/zeyad_kingng")

# اسم المشروع الجديد في الواجهة
new_name = "𝑍𝐸𝑌𝐴𝐷 𝑲𝐈𝐍𝐆"

# بورت النسخة الجديدة
new_port = 8000

# ملفات قواعد البيانات الموجودة في المشروع
db_files = ["data.db", "brands.db", "your_database.db", "your_data.db"]

# 1️⃣ نسخ المشروع بالكامل
print(f"✅ نسخ المشروع من {old_project} إلى {new_project} ...")
shutil.copytree(old_project, new_project, dirs_exist_ok=True)

# 2️⃣ نسخ قواعد البيانات مع إضافة suffix _copy
for db in db_files:
    old_db_path = os.path.join(old_project, db)
    if os.path.exists(old_db_path):
        new_db_path = os.path.join(new_project, db.replace(".db", "_copy.db"))
        shutil.copy2(old_db_path, new_db_path)
        print(f"✅ تم نسخ {db} → {new_db_path}")
    else:
        print(f"⚠️ لم يتم العثور على {db}")

# 3️⃣ تعديل app.py للنسخة الجديدة
app_py_path = os.path.join(new_project, "app.py")
if os.path.exists(app_py_path):
    with open(app_py_path, "r") as f:
        content = f.read()

    # تغيير اسم المشروع في البانر أو أي print
    content = content.replace("𝑍𝐸𝑅𝑂", new_name)

    # تغيير قواعد البيانات لتشير للنسخ الجديدة
    for db in db_files:
        old_db_name = db
        new_db_name = db.replace(".db", "_copy.db")
        content = content.replace(f'"{old_db_name}"', f'"{new_db_name}"')

    # تغيير البورت
    import re
    content = re.sub(r"port\s*=\s*\d+", f"port={new_port}", content)

    with open(app_py_path, "w") as f:
        f.write(content)
    print(f"✅ تم تعديل app.py للنسخة الجديدة")
else:
    print(f"⚠️ لم يتم العثور على app.py في {new_project}")

print("\n🎉 النسخة الجديدة جاهزة للتشغيل:")
print(f"cd {new_project} && python app.py")
