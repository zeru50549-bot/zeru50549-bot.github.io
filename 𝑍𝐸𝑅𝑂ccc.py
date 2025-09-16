import sqlite3
import os
import shutil
import glob

STATIC_IMG_DIR = "static/images"
STATIC_VIDEO_DIR = "static/videos"
EXTERNAL_VIDEO_DIRS = [
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Movies"),
    "/sdcard/Download",
    "/sdcard/Movies"
]

DB_FILES = ["data.db", "brands.db", "your_database.db", "your_data.db"]

os.makedirs(STATIC_IMG_DIR, exist_ok=True)
os.makedirs(STATIC_VIDEO_DIR, exist_ok=True)

def find_file_anywhere(filename, extra_dirs=None):
    # البحث في المجلد الحالي وكل المجلدات الفرعية
    found = glob.glob(f"**/{filename}", recursive=True)
    if found:
        return found[0]
    # البحث في أي مجلد إضافي
    if extra_dirs:
        for d in extra_dirs:
            candidate = os.path.join(d, filename)
            if os.path.exists(candidate):
                return candidate
    return None

def fix_and_clean_db(db_file):
    if not os.path.exists(db_file):
        print(f"⚠️ قاعدة البيانات {db_file} غير موجودة.")
        return

    print(f"\n🔹 فحص قاعدة البيانات: ./{db_file}")

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='brands'")
    if not cursor.fetchone():
        print(f"⚠️ لا يوجد جدول 'brands' في ./{db_file}")
        conn.close()
        return

    cursor.execute("SELECT id, name, price, image, video FROM brands")
    rows = cursor.fetchall()

    if not rows:
        print(f"لا توجد بيانات في جدول brands.")
        conn.close()
        return

    print(f"{'ID':<5} | {'Name':<40} | {'Price':<10} | {'Image':<40} | {'Video':<30} | Img✅ | Vid✅")
    print("-" * 130)

    row_map = {}
    for r in rows:
        id_, name, price, image, video = r
        image_name = os.path.basename(image) if image else ""
        video_name = os.path.basename(video) if video else ""
        image_exists = os.path.exists(os.path.join(STATIC_IMG_DIR, image_name)) if image_name else False
        video_exists = os.path.exists(os.path.join(STATIC_VIDEO_DIR, video_name)) if video_name else False
        row_map[id_] = [name, price, image_name, video_name, image_exists, video_exists]
        print(f"{id_:<5} | {name:<40} | {price:<10} | {image_name:<40} | {video_name:<30} | {'✅' if image_exists else '❌'} | {'✅' if video_exists else '❌'}")

    # حذف عناصر محددة برقمها
    select_delete = input("\nلو حاب تمسح عنصر محدد، اكتب رقمه أو اضغط Enter للتجاهل (أرقام مفصولة بفواصل): ")
    if select_delete:
        ids = [int(x.strip()) for x in select_delete.split(",") if x.strip().isdigit()]
        for id_ in ids:
            cursor.execute("DELETE FROM brands WHERE id=?", (id_,))
            print(f"✅ تم حذف row ID {id_} بالاختيار اليدوي")

    # حذف الصفوف التي صورتها ناقصة
    delete_missing = input(f"\nتمسح كل الصفوف في ./{db_file} اللي صورتها ناقصة؟ (y/n): ").strip().lower()
    if delete_missing == 'y':
        for id_, (name, price, image_name, video_name, image_exists, video_exists) in row_map.items():
            if not image_exists:
                cursor.execute("DELETE FROM brands WHERE id=?", (id_,))
                print(f"✅ تم حذف row ID {id_} لأنه الصورة مش موجودة")

    # حذف الصفوف التي الاسم فيها Imported
    delete_imported = input(f"\nتمسح كل الصفوف في ./{db_file} اللي الاسم فيها 'Imported'? (y/n): ").strip().lower()
    if delete_imported == 'y':
        for id_, (name, price, image_name, video_name, image_exists, video_exists) in row_map.items():
            if "imported" in (name or "").lower():
                cursor.execute("DELETE FROM brands WHERE id=?", (id_,))
                print(f"✅ تم حذف row ID {id_} لأنه الاسم فيه Imported")

    # نقل الصور والفيديوهات إلى مجلدها الصحيح وتحديث المسارات
    for id_, (name, price, image_name, video_name, image_exists, video_exists) in row_map.items():
        # الصور
        if image_name:
            path = find_file_anywhere(image_name)
            if path:
                dest = os.path.join(STATIC_IMG_DIR, image_name)
                if os.path.abspath(path) != os.path.abspath(dest):
                    shutil.copy2(path, dest)
                # ✅ خزن فقط اسم الملف في قاعدة البيانات
                cursor.execute("UPDATE brands SET image=? WHERE id=?", (image_name, id_))
            else:
                print(f"❌ الصورة {image_name} مش موجودة في أي مكان")

        # الفيديوهات
        if video_name:
            path = find_file_anywhere(video_name, extra_dirs=EXTERNAL_VIDEO_DIRS)
            if path:
                dest = os.path.join(STATIC_VIDEO_DIR, video_name)
                if os.path.abspath(path) != os.path.abspath(dest):
                    shutil.copy2(path, dest)
                # ✅ خزن فقط اسم الملف في قاعدة البيانات
                cursor.execute("UPDATE brands SET video=? WHERE id=?", (video_name, id_))
            else:
                print(f"❌ الفيديو {video_name} مش موجودة في أي مكان")

    conn.commit()
    conn.close()
    print(f"✅ الفحص والتحديث اكتمل لـ {db_file}.")

if __name__ == "__main__":
    for db in DB_FILES:
        fix_and_clean_db(db)
    print("\n🎉 الفحص الشامل لكل قواعد البيانات اكتمل.")
