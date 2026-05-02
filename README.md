# Information Theory — LZW & Huffman Compression

Lossless **Huffman coding** and **LZW (Lempel–Ziv–Welch)** implementations from scratch, with a **Tkinter GUI**, a **Flask web UI**, entropy analysis, and an optional **binary symmetric channel + Hamming(7,4)** bonus demo.

**Course context:** ECU — Information Theory & Data Compression · Spring 2026

---

## Features

| Area | Description |
|------|-------------|
| **Huffman** | Min-heap tree, variable-length prefix codes; tree stored in `.huf` file header |
| **LZW** | 16-bit fixed codes; dictionary rebuilt on decompress; `.lzw` format |
| **Entropy** | Shannon \(H(X)\) in bits per byte (symbol) |
| **GUI** | `gui/app.py` — file pick, compress/decompress, metrics |
| **Web** | `app.py` — upload, API, comparison mode, download outputs |
| **Bonus** | BSC bit flips + Hamming(7,4) encode/decode pipeline |

---

## Requirements

- **Python 3.8+**
- **Algorithms / GUI / tests:** standard library only  
- **Web app:** [Flask](https://flask.palletsprojects.org/) (install from `requirements.txt`)

```bash
pip install -r requirements.txt
```

---

## Quick start

### Windows (`run.bat`)

Double-click **`run.bat`** and choose:

1. **Web** — Flask server at `http://localhost:5000`  
2. **GUI** — Tkinter desktop app  
3. **Tests** — automated suite  

### Command line

```bash
# Clone
git clone https://github.com/Mohmedahmed888/Information-Theory-code-lzw--huffman-.git
cd Information-Theory-code-lzw--huffman-

# Web
pip install -r requirements.txt
python app.py
# Open http://localhost:5000

# GUI
python gui/app.py

# Tests
python test_all.py
```

### Compress / decompress rules (web & API)

- **Compress:** any file → output `originalname.huf` or `originalname.lzw`  
- **Decompress:** upload the **`.huf` or `.lzw`** file produced by this project (not plain `.txt`)

---

## Repository layout

```
.
├── app.py                 # Flask web server + /api/compress, /api/download
├── run.bat               # Windows launcher (web / gui / tests)
├── requirements.txt      # Flask (web only)
├── test_all.py           # Automated Huffman/LZW/channel tests
├── create_test_files.py  # Helper to generate sample inputs
├── algorithms/
│   ├── __init__.py
│   ├── huffman.py        # Huffman compress/decompress (.huf)
│   ├── lzw.py             # LZW compress/decompress (.lzw)
│   └── channel.py         # Hamming + BSC bonus
├── utils/
│   └── entropy.py        # Shannon entropy & file stats
├── gui/
│   └── app.py            # Tkinter GUI
├── web/
│   ├── index.html        # Single-page UI
│   └── ecu-logo.png
├── test_files/           # Sample inputs (e.g. demo text)
├── output/               # Generated outputs (gitignored if present)
└── uploads/             # Web uploads (gitignored if present)
```

---

## Design notes

### Huffman — self-contained `.huf` files  

The Huffman tree is **serialized into the compressed file header** (pre-order bit encoding). Decompression **does not** need the original frequencies or a separate side file.

### LZW — no dictionary on disk  

The dictionary is **rebuilt from the code stream** during decompression (standard LZW property).

### Bonus — Hamming(7,4)  

Each input byte → two nibbles → two 7-bit codewords. The simulator flips bits with probability BER; single-bit errors per codeword can be corrected. High BER may cause uncorrectable multi-bit errors.

---

## Test results (typical datasets)

| File type | Huffman ratio | LZW ratio | Entropy H(X) |
|-----------|---------------|-----------|--------------|
| Text (~33 KB) | ~1.79× | ~3.78× | ~4.40 bits |
| Repetitive (~10 KB) | ~7.88× | ~24.63× | ~1.00 bits |
| Pseudorandom (~10 KB) | ~1× | &lt;1× expansion | ~7.98 bits |

High-entropy data is hard to compress (Shannon’s source coding theorem).

---

## Author / repo

- **GitHub:** [Mohmedahmed888/Information-Theory-code-lzw--huffman-](https://github.com/Mohmedahmed888/Information-Theory-code-lzw--huffman-)

---

## License

Educational use — adjust as needed for your course submission policy.
