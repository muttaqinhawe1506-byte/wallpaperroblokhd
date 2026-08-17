import os
import json
import re
from datetime import datetime
from PIL import Image

# Konfigurasi Path
RAW_DIR = "raw_images"
FULL_DIR = os.path.join("wallpapers", "full")
THUMB_DIR = os.path.join("wallpapers", "thumbs")
JSON_FILE = "wallpapers.json"

# Konfigurasi Gambar
THUMB_MAX_WIDTH = 480       # Lebar maksimal thumbnail
FULL_QUALITY = 85           # Kualitas WebP Full (0-100)
THUMB_QUALITY = 75          # Kualitas WebP Thumbnail (0-100)

def slugify(text):
    """Membersihkan nama file untuk ID dan Title"""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '_', text)

def format_title(filename_no_ext):
    """Mengubah 'roblox_cool_sword_01' menjadi 'Roblox Cool Sword 01'"""
    cleaned = filename_no_ext.replace('_', ' ').replace('-', ' ')
    return ' '.join(word.capitalize() for word in cleaned.split())

def ensure_directories():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(FULL_DIR, exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)

def load_existing_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {item["id"]: item for item in data.get("wallpapers", [])}
        except Exception as e:
            print(f"Peringatan: Gagal membaca {JSON_FILE} lama: {e}")
    return {}

def process_images():
    ensure_directories()
    existing_items = load_existing_data()
    updated_items = {}
    
    # Ambil info repo dari environment variable GitHub Actions
    repo_owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "your-username")
    repo_name = os.environ.get("GITHUB_REPOSITORY", "your-username/repo").split("/")[-1]
    branch = "main"
    base_raw_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}"

    raw_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    raw_files.sort()

    print(f"Ditemukan {len(raw_files)} gambar di {RAW_DIR}...")

    for file_name in raw_files:
        base_name, _ = os.path.splitext(file_name)
        item_id = slugify(base_name)
        
        raw_path = os.path.join(RAW_DIR, file_name)
        full_webp_name = f"{item_id}.webp"
        thumb_webp_name = f"{item_id}_thumb.webp"
        
        full_path = os.path.join(FULL_DIR, full_webp_name)
        thumb_path = os.path.join(THUMB_DIR, thumb_webp_name)

        try:
            with Image.open(raw_path) as img:
                img = img.convert("RGB")
                orig_width, orig_height = img.size
                resolution_str = f"{orig_width}x{orig_height}"

                # 1. Simpan WebP Full HD/4K
                img.save(full_path, "WEBP", quality=FULL_QUALITY, method=6)

                # 2. Buat & Simpan Thumbnail WebP
                thumb_img = img.copy()
                if orig_width > THUMB_MAX_WIDTH:
                    ratio = THUMB_MAX_WIDTH / float(orig_width)
                    thumb_height = int(float(orig_height) * float(ratio))
                    thumb_img = thumb_img.resize((THUMB_MAX_WIDTH, thumb_height), Image.Resampling.LANCZOS)
                
                thumb_img.save(thumb_path, "WEBP", quality=THUMB_QUALITY, method=6)

            # Metadata item
            date_today = datetime.now().strftime("%Y-%m-%d")
            
            # Jika item sudah pernah ada di JSON, pertahankan tags / category yang sudah diedit manual
            if item_id in existing_items:
                item_data = existing_items[item_id]
                item_data["resolution"] = resolution_str
                item_data["thumbnail_url"] = f"{base_raw_url}/{THUMB_DIR}/{thumb_webp_name}"
                item_data["image_url"] = f"{base_raw_url}/{FULL_DIR}/{full_webp_name}"
            else:
                item_data = {
                    "id": item_id,
                    "title": format_title(base_name),
                    "category_id": "general",
                    "thumbnail_url": f"{base_raw_url}/{THUMB_DIR}/{thumb_webp_name}" ,
                    "image_url": f"{base_raw_url}/{FULL_DIR}/{full_webp_name}",
                    "resolution": resolution_str,
                    "tags": ["roblox", "wallpaper", "hd"],
                    "is_featured": False,
                    "created_at": date_today
                }

            updated_items[item_id] = item_data
            print(f"[OK] Berhasil memproses: {file_name} -> {item_id}.webp ({resolution_str})")

        except Exception as e:
            print(f"[ERROR] Gagal memproses {file_name}: {e}")

    # Susun output akhir
    final_output = {
        "total_wallpapers": len(updated_items),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "wallpapers": list(updated_items.values())
    }

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"\nSelesai! {JSON_FILE} berhasil diperbarui dengan {len(updated_items)} wallpaper.")

if __name__ == "__main__":
    process_images()
