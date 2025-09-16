import os

TEMPLATES_DIR = "."  # لو انت بالفعل داخل مجلد templates

print("Checking for empty or very small template files...\n")

for filename in os.listdir(TEMPLATES_DIR):
    if filename.endswith(".html"):
        filepath = os.path.join(TEMPLATES_DIR, filename)
        size = os.path.getsize(filepath)
        if size < 100:  # أقل من 100 بايت غالبًا فارغ أو ناقص
            print(f"⚠️ {filename} حجم صغير جدًا ({size} bytes)")
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                if "{% block" not in content and "<html" not in content:
                    print(f"❌ {filename} قد يكون فارغ أو ناقص tags أساسية")
