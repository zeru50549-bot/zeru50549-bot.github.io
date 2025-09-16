#!/usr/bin/env python3
"""
bulk_add_images.py

ينسخ الصور من مجلد المصدر إلى static/images/ ويضيف صفوف في جدول brands داخل data.db.
يحمي من التكرار عبر مقارنة SHA256 (محتوى الملف).
خيارات:
  --source PATH    : مجلد الصور المصدر (default: ~/downloads)
  --db PATH        : ملف قاعدة البيانات (default: ./data.db)
  --static PATH    : مجلد static المشروع (default: ./static)
  --price FLOAT    : السعر الافتراضي للبراندات الجديدة (default: 0.0)
  --name-prefix STR: بادئة اسم البراند المضافة (default: "Imported")
  --dry-run        : فقط افحص واطبع تقرير، من غير نسخ أو إدخال DB
  --apply          : طبق التغييرات فعلياً (انسخ وادخل DB)
  --extensions ex1,ex2 : امتدادات مسموحة مفصولة بفواصل (default: png,jpg,jpeg,gif,webp)
  --skip-existing  : لا تضيف ملف لو نفس الهاش موجود أساسا في static/images أو في DB
"""

import os
import sys
import argparse
import hashlib
import sqlite3
import shutil
import uuid

def compute_hash(path, chunk_size=8192):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def ensure_dirs(static_dir):
    img_dir = os.path.join(static_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    return img_dir

def find_existing_hashes(img_dir):
    """Return set of hashes for files already in static/images (by content)."""
    hashes = {}
    if not os.path.isdir(img_dir):
        return hashes
    for root, _, files in os.walk(img_dir):
        for fn in files:
            path = os.path.join(root, fn)
            try:
                h = compute_hash(path)
                rel = os.path.relpath(path, img_dir).replace("\\","/")
                hashes[h] = ("images/" + rel)
            except Exception as e:
                print("⚠️ error hashing", path, e)
    return hashes

def find_db_image_paths(conn):
    """Return set/list of image paths present in DB (normalized)."""
    c = conn.cursor()
    try:
        c.execute("SELECT image FROM brands WHERE image IS NOT NULL")
    except Exception:
        return set()
    rows = c.fetchall()
    vals = set()
    for (v,) in rows:
        if v:
            s = str(v).strip()
            # Normalize: remove leading "static/" if present
            if s.startswith("static/"):
                s = s[len("static/"):]
            vals.add(s)
    return vals

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default=os.path.expanduser("~/downloads"))
    p.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "data.db"))
    p.add_argument("--static", default=os.path.join(os.path.dirname(__file__), "static"))
    p.add_argument("--price", type=float, default=0.0)
    p.add_argument("--name-prefix", default="Imported")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--extensions", default="png,jpg,jpeg,gif,webp")
    p.add_argument("--skip-existing", action="store_true", help="skip files whose content hash is already present")
    args = p.parse_args()

    source = os.path.abspath(os.path.expanduser(args.source))
    db_file = os.path.abspath(os.path.expanduser(args.db))
    static_dir = os.path.abspath(os.path.expanduser(args.static))
    img_dir = ensure_dirs(static_dir)
    exts = set(e.lower().strip().lstrip(".") for e in args.extensions.split(","))

    if not os.path.isdir(source):
        print(f"❌ المصدر مش موجود: {source}")
        sys.exit(1)

    # collect candidate files
    candidates = []
    for fn in os.listdir(source):
        lp = fn.lower()
        if "." in lp:
            ext = lp.rsplit(".",1)[1]
            if ext in exts:
                candidates.append(os.path.join(source, fn))
    if not candidates:
        print("ℹ️ مفيش ملفات مناسبة في المجلد المصدر.")
        sys.exit(0)

    print(f"Found {len(candidates)} candidate files in {source}")

    # compute hashes for candidates
    cand_data = []
    for path in candidates:
        try:
            h = compute_hash(path)
            cand_data.append((path, h))
        except Exception as e:
            print("⚠️ failed hash:", path, e)

    # existing hashes in static/images
    existing_hashes = find_existing_hashes(img_dir)
    print(f"Found {len(existing_hashes)} existing files in static/images")

    # open DB to check existing image references and to insert
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    # ensure table exists similar to app.py schema
    c.execute('''CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT,
            video TEXT,
            price REAL NOT NULL DEFAULT 0
        )''')
    conn.commit()

    db_image_paths = find_db_image_paths(conn)
    print(f"Found {len(db_image_paths)} image refs in DB")

    # decide actions
    to_add = []  # list of dicts: {src, hash, dest_rel, dest_full, brand_name, price}
    for src, h in cand_data:
        if h in existing_hashes:
            existing_rel = existing_hashes[h]
            msg = f"SKIP (duplicate content) {os.path.basename(src)} -> already exists as {existing_rel}"
            if args.skip_existing:
                print(msg)
                continue
            # else: still skip adding file copy, but may add DB ref to existing_rel if not present
            if existing_rel not in db_image_paths:
                to_add.append({
                    "src": None,
                    "hash": h,
                    "dest_rel": existing_rel,
                    "dest_full": None,
                    "brand_name": f"{args.name_prefix} {os.path.splitext(os.path.basename(src))[0]}",
                    "price": args.price
                })
                print("WILL ADD DB REF for existing file:", existing_rel)
            else:
                print(msg)
            continue

        # not duplicate by content -> create unique filename
        ext = os.path.splitext(src)[1].lower()
        new_fn = str(uuid.uuid4()) + ext
        dest_rel = "images/" + new_fn
        dest_full = os.path.join(img_dir, new_fn)
        # if dest file already exists (very unlikely) generate another uuid
        while os.path.exists(dest_full):
            new_fn = str(uuid.uuid4()) + ext
            dest_rel = "images/" + new_fn
            dest_full = os.path.join(img_dir, new_fn)

        to_add.append({
            "src": src,
            "hash": h,
            "dest_rel": dest_rel,
            "dest_full": dest_full,
            "brand_name": f"{args.name_prefix} {os.path.splitext(os.path.basename(src))[0]}",
            "price": args.price
        })

    if not to_add:
        print("Nothing to add.")
        conn.close()
        sys.exit(0)

    # report
    print("\n--- Planned actions ---")
    for a in to_add:
        if a["src"]:
            print(f"COPY: {os.path.basename(a['src'])} -> {a['dest_rel']} (brand: {a['brand_name']})")
        else:
            print(f"DB-REF: use existing {a['dest_rel']} -> add brand {a['brand_name']}")

    if args.dry_run and not args.apply:
        print("\nDry-run mode — nothing changed. Run with --apply to perform copy+db insert.")
        conn.close()
        sys.exit(0)

    # apply: copy files and insert DB rows
    inserted = 0
    copied = 0
    for a in to_add:
        dest_rel = a["dest_rel"]
        if a["src"]:
            try:
                shutil.copy2(a["src"], a["dest_full"])
                copied += 1
                print("Copied:", a["src"], "->", a["dest_full"])
            except Exception as e:
                print("⚠️ Failed to copy:", a["src"], e)
                continue

        # insert DB row
        # Normalize stored image path to be relative to static (no leading 'static/')
        image_db_value = dest_rel  # already 'images/xxx'
        c.execute("INSERT INTO brands (name, image, video, price) VALUES (?, ?, ?, ?)",
                  (a["brand_name"], image_db_value, None, a["price"]))
        conn.commit()
        inserted += 1
        print("Inserted brand row:", a["brand_name"], image_db_value)

    conn.close()
    print(f"\nDone. Copied: {copied}. Inserted rows: {inserted}.")
    return 0

if __name__ == "__main__":
    main()
