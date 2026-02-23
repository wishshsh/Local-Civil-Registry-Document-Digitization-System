"""
Sample Data Generator for CRNN+CTC Civil Registry OCR
Run this script to create fake training data and test if everything works.

Usage:
    python generate_sample_data.py
"""

import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

# ── Folder structure ──────────────────────────────────────────────────────────
FOLDERS = [
    "data/train/form1a",
    "data/train/form2a",
    "data/val/form1a",
    "data/val/form2a",
    "checkpoints",
    "logs",
]

# ── Sample Filipino names and places ─────────────────────────────────────────
FIRST_NAMES = ["Juan", "Maria", "Jose", "Ana", "Pedro", "Rosa", "Carlos", "Luz"]
LAST_NAMES  = ["Dela Cruz", "Santos", "Reyes", "Garcia", "Torres", "Flores"]
PLACES      = ["Tarlac City", "Manila", "Quezon City", "Cebu City", "Davao City"]
DATES       = ["01/15/1990", "03/22/1985", "07/04/2000", "11/30/1995", "05/18/1988"]

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_text(form_type):
    if form_type == "form1a":
        return random.choice([
            random_name(),
            random.choice(DATES),
            random.choice(PLACES),
            f"{random_name()} Jr.",
        ])
    else:  # form2a
        return random.choice([
            random_name(),
            random.choice(DATES),
            random.choice(PLACES),
            "Cardiac Arrest",
            "Natural Causes",
        ])

def create_text_image(text, width=200, height=64, noise=True):
    """Create a simple white image with black text."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Try to use a basic font; fall back to default if unavailable
    try:
        font = ImageFont.truetype("arial.ttf", size=20)
    except Exception:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = max((width - text_w) // 2, 2)
    y = max((height - text_h) // 2, 2)

    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    # Optional: add slight noise to simulate scanned documents
    if noise:
        arr = np.array(img, dtype=np.float32)
        arr += np.random.normal(0, 8, arr.shape)
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)

    return img

def generate_dataset(folder, form_type, count):
    annotations = []
    for i in range(count):
        text = random_text(form_type)
        img  = create_text_image(text)

        img_filename = f"{form_type}_{i+1:04d}.jpg"
        img_path     = os.path.join(folder, img_filename)
        img.save(img_path)

        # Save matching label file
        txt_path = img_path.replace(".jpg", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        annotations.append({"image": img_path, "label": text})

    return annotations

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("📁 Creating folder structure...")
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)
    print("   ✅ Done\n")

    print("🖼️  Generating training images...")
    train_ann  = generate_dataset("data/train/form1a", "form1a", 50)
    train_ann += generate_dataset("data/train/form2a", "form2a", 50)
    with open("data/train_annotations.json", "w") as f:
        json.dump(train_ann, f, indent=2)
    print(f"   ✅ {len(train_ann)} training images created\n")

    print("🖼️  Generating validation images...")
    val_ann  = generate_dataset("data/val/form1a", "form1a", 20)
    val_ann += generate_dataset("data/val/form2a", "form2a", 20)
    with open("data/val_annotations.json", "w") as f:
        json.dump(val_ann, f, indent=2)
    print(f"   ✅ {len(val_ann)} validation images created\n")

    print("=" * 50)
    print("🎉 Sample data generation COMPLETE!")
    print("=" * 50)
    print("\nFolder structure created:")
    print("  data/")
    print("    train/form1a/  ← 50 images")
    print("    train/form2a/  ← 50 images")
    print("    val/form1a/    ← 20 images")
    print("    val/form2a/    ← 20 images")
    print("  data/train_annotations.json")
    print("  data/val_annotations.json")
    print("\n✅ Now you can run:  python train.py")

if __name__ == "__main__":
    main()
