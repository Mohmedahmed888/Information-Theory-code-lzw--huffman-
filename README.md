<p align="center">
  <strong>Lossless Compression — Huffman &amp; LZW</strong><br/>
  <sub>Information Theory · From-scratch implementations · GUI + Web + Tests</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/flask-3.x-green?logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License MIT"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform"/>
</p>

---

## Overview

This repository provides **educational, from-scratch** implementations of:

- **Huffman coding** — prefix-free variable-length codes built with a min-heap; the **code tree is serialized in the `.huf` file header** so decompression is independent of prior runs.
- **LZW (Lempel–Ziv–Welch)** — dictionary-based compression using **16-bit codes**; the dictionary is **not stored in the file** and is reconstructed during decompression (`.lzw`).

Supporting components include **Shannon entropy** analysis (`utils/entropy.py`), a **Tkinter desktop UI**, a **Flask + single-page web UI**, and an optional **Binary Symmetric Channel (BSC) + Hamming(7,4)** demonstration (`algorithms/channel.py`).

**Institutional context:** ECU — *Information Theory &amp; Data Compression* · Spring 2026  

**Repository:** [github.com/Mohmedahmed888/Information-Theory-code-lzw--huffman-](https://github.com/Mohmedahmed888/Information-Theory-code-lzw--huffman-)

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Web API](#web-api)
- [File formats](#file-formats)
- [Project layout](#project-layout)
- [Testing](#testing)
- [Notes on compression limits](#notes-on-compression-limits)
- [Security (development server)](#security-development-server)
- [License](#license)

---

## Features

| Component | Description |
|-----------|-------------|
| **Huffman** | Frequency table → tree → bitstream; **lossless** round-trip via embedded tree |
| **LZW** | Classic encode/decode loop; **KwKwK** edge case handled in decoder |
| **Entropy** | Empirical Shannon entropy **H(X)** in bits per byte |
| **GUI** | `gui/app.py` — browse file, compress/decompress, metrics |
| **Web** | `app.py` — upload, compare algorithms, download results |
| **Bonus channel** | Hamming encode → BSC noise → decode/correct → optional decompress smoke test |

---

## Tech stack

| Layer | Technology |
|-------|---------------|
| Language | Python 3.8+ |
| Algorithms | Standard library (`heapq`, `struct`, `collections`, …) |
| Web | Flask 3.x (see `requirements.txt`) |
| Desktop UI | Tkinter (stdlib) |
| Frontend | Static HTML/CSS/JS under `web/` |

---

## Installation

### 1. Clone

```bash
git clone https://github.com/Mohmedahmed888/Information-Theory-code-lzw--huffman-.git
cd Information-Theory-code-lzw--huffman-
```

### 2. Virtual environment (recommended)

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

The **web app** requires Flask. The **GUI** and **test suite** run with the standard library only once Python is installed.

---

## Usage

### Option A — Windows launcher

Double-click **`run.bat`** and choose:

1. Web (Flask) — default `http://127.0.0.1:5000`  
2. GUI (Tkinter)  
3. Automated tests  

### Option B — Command line

```bash
# Web UI
python app.py
# Open http://127.0.0.1:5000 in your browser

# Desktop GUI
python gui/app.py

# Full test suite
python test_all.py
```

### Compress / decompress rules

| Mode | Input | Output |
|------|--------|--------|
| **Compress** | Any file | `originalname.huf` (Huffman) or `originalname.lzw` (LZW) |
| **Decompress** | `.huf` or `.lzw` **produced by this project** | Reconstructed file (original extension preserved when possible) |

Plain text (e.g. `.txt`) is **not** a valid decompress input unless it was compressed by this tool first.

---

## Web API

Base URL while the server runs locally: `http://127.0.0.1:5000`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Serve `web/index.html` |
| `GET` | `/ecu-logo.png` | Logo asset |
| `POST` | `/api/compress` | Multipart form: `file`, `algorithm` (`huffman` \| `lzw`), `mode` (`compress` \| `decompress`), optional `use_channel`, `ber` |
| `GET` | `/api/download/<filename>` | Download file from server `output/` |
| `GET` | `/api/ping` | Development: change notification for optional live reload in the SPA |

Responses are JSON (except downloads and static files). Typical success fields include `ratio`, `saved`, `time_ms`, `memory_kb`, and `entropy`.

---

## File formats

### Huffman (`.huf`)

Binary layout (big-endian integers where applicable):

1. Original size (4 bytes)  
2. Tree bit length (4 bytes)  
3. Tree byte length (4 bytes)  
4. Serialized tree (`tree byte length` bytes)  
5. Padding bit count for payload (4 bytes)  
6. Encoded payload (remaining bytes)

### LZW (`.lzw`)

1. Original size (4 bytes)  
2. Number of codes (4 bytes)  
3. Codes as **16-bit** big-endian shorts (`num_codes × 2` bytes)

---

## Project layout

```
.
├── app.py                 # Flask application entry
├── run.bat                # Windows menu launcher
├── requirements.txt       # Web dependency pin (Flask)
├── LICENSE                # MIT
├── test_all.py            # Automated tests
├── create_test_files.py   # Sample data helper
├── algorithms/
│   ├── huffman.py         # Huffman codec
│   ├── lzw.py             # LZW codec
│   └── channel.py        # Hamming + BSC bonus
├── utils/
│   └── entropy.py         # Entropy & file stats
├── gui/
│   └── app.py             # Tkinter UI
├── web/
│   ├── index.html
│   └── ecu-logo.png
└── test_files/            # Committed samples; channel temp files gitignored
```

Runtime directories `output/` and `uploads/` are created by the application and listed in `.gitignore`.

---

## Testing

```bash
python test_all.py
```

The suite exercises **compress → decompress** round-trips (integrity via hashing), reports ratios and timing, and includes **channel bonus** scenarios where configured.

---

## Notes on compression limits

Reference behaviour on representative datasets (see `test_all.py` / `test_files/`):

| Dataset profile | Typical behaviour |
|----------------|-------------------|
| Natural text | Moderate redundancy — both algorithms shrink the file |
| Highly repetitive input | Strong redundancy — large compression gains |
| High-entropy (pseudo-random) | Little to no redundancy — **compression may expand** output; this aligns with Shannon’s source coding theorem |

---

## Security (development server)

Flask’s built-in server is intended for **local development and coursework demos**. Do **not** expose it to the public internet without a production WSGI server, reverse proxy, and hardening.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE).

---

<p align="center">
  Built for coursework in <strong>Information Theory &amp; Data Compression</strong>
</p>
