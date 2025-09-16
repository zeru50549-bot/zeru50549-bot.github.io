import sqlite3
import os

DB_FILE = "data.db"
IMAGES_FOLDER = "static/images/"
VIDEOS_FOLDER = "static/videos/"

def add_media_to_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # جلب الصور والفيديوهات
    images = [f for f in os.listdir(IMAGES_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    videos = [f for f in os.listdir(VIDEOS_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.avi'))]

    # لو نفس اسم الصورة موجود في جدول brands، ما نضيفوش
    existing = c.execute("SELECT image FROM brands").fetchall()
    existing_images = set([row[0] for row in existing])

    for img in images:
        image_path = os.path.join(IMAGES_FOLDER, img)
        if image_path in existing_images:
            continue  # نتخطى اللي موجودين
        # نختار فيديو لو موجود بنفس الاسم تقريبًا
        video_file = None
        base_name = os.path.splitext(img)[0]
        for v in videos:
            if base_name in v:
                video_file = os.path.join(VIDEOS_FOLDER, v)
                break

        # إضافة البراند
        c.execute("INSERT INTO brands (name, image, video, price) VALUES (?, ?, ?, ?)",
                  (base_name, image_path, video_file, 1000))
        print(f"تم إضافة البراند: {base_name} | صورة: {image_path} | فيديو: {video_file}")

    conn.commit()
    conn.close()
    print("✅ تم إضافة كل الصور والفيديوهات المتاحة للقاعدة بنجاح!")

if __name__ == "__main__":
    add_media_to_db()
