"""
Run this once to create 3 test files for the compression project.
Place this file inside the compression_project folder and run:
    python create_test_files.py
"""

import os
import random

folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files")
os.makedirs(folder, exist_ok=True)

# ── 1. Text file (natural language, easy to compress) ──
text_path = os.path.join(folder, "sample_text.txt")
text = (
    "Information theory is the scientific study of the quantification, "
    "storage, and communication of digital information. "
    "A key measure in information theory is entropy. "
    "Entropy quantifies the amount of uncertainty involved in the value "
    "of a random variable or the outcome of a random process. "
    "Huffman coding and LZW are two classic lossless compression algorithms "
    "that exploit redundancy in data to reduce file size. "
    "The Egyptian Chinese University — Faculty of Computers and Information Systems.\n"
) * 100
with open(text_path, "w", encoding="utf-8") as f:
    f.write(text)
print(f"✅ Created: {text_path}  ({os.path.getsize(text_path):,} bytes)")

# ── 2. Repetitive binary (very easy to compress) ──
rep_path = os.path.join(folder, "repetitive.bin")
with open(rep_path, "wb") as f:
    f.write(bytes([0xAB, 0xCD, 0x00, 0xFF] * 8000))
print(f"✅ Created: {rep_path}  ({os.path.getsize(rep_path):,} bytes)")

# ── 3. Random binary (hard to compress — high entropy) ──
rand_path = os.path.join(folder, "random_data.bin")
random.seed(42)
with open(rand_path, "wb") as f:
    f.write(bytes([random.randint(0, 255) for _ in range(20000)]))
print(f"✅ Created: {rand_path}  ({os.path.getsize(rand_path):,} bytes)")

print("\n🎉 Done! Now open these files in the GUI using Browse.")
print(f"📂 Folder: {folder}")
