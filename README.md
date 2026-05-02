<p align="center">
  <strong>Lossless Compression — Huffman &amp; LZW</strong><br/>
  <sub>Information Theory · From-scratch implementations · GUI + Web + Tests</sub>
</p>

<p align="center">
  <a href="https://github.com/Mohmedahmed888/Information-Theory-code-lzw--huffman-/actions/workflows/ci.yml">
    <img src="https://github.com/Mohmedahmed888/Information-Theory-code-lzw--huffman-/actions/workflows/ci.yml/badge.svg" alt="GitHub Actions CI"/>
  </a>
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
- [Continuous integration](#continuous-integration)
- [Docker (web UI)](#docker-web-ui)
- [Screenshots & documentation bundle](#screenshots--documentation-bundle)
- [Suggested GitHub topics](#suggested-github-topics)
- [Releases](#releases)
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
├── pyproject.toml         # ruff tooling config
├── requirements-dev.txt   # ruff (CI & local dev)
├── Dockerfile             # Containerized Flask web demo
├── .github/workflows/     # CI pipeline
├── test_all.py            # Integration-style scripted tests
├── docs/                   # REPORT, release notes, policies, screenshot folder
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

### Integration / demo suite

```bash
python test_all.py
```

Runs multi-file demos, prints throughput-style metrics (via `tracemalloc`), verifies **lossless** integrity with MD5, and executes the noisy-channel bonus harness.

### Lint (ruff, optional for contributors)

```bash
pip install -r requirements-dev.txt
ruff check .
```

---

## Continuous integration

GitHub Actions workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) executes on pushes/PRs to `main`:

1. **`ruff check .`** — static diagnostics on Python sources (optional PyQt prototype `gui/main_app.py` excluded to avoid heavyweight optional-deps noise)  
2. **`python test_all.py`** — scripted integration sweep (compress/decompress + bonus channel)

Badge status is shown near the top of this README once Actions have run successfully on GitHub.

---

## Docker (web UI)

Minimal image that serves **only** the Flask application (algorithms/utils/web assets copied in).

```bash
docker build -t compression-web .
docker run --rm -p 5000:5000 compression-web
# Browse http://127.0.0.1:5000
```

Environment knobs:

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLASK_HOST` | `127.0.0.1` locally / `0.0.0.0` inside Docker image | Listen address |
| `FLASK_PORT` | `5000` | TCP port |

---

## Screenshots & documentation bundle

Structured artifacts live under **`docs/`**:

| Path | Role |
|------|------|
| [`docs/REPORT.md`](docs/REPORT.md) | Long-form theory + architecture narrative (adapt for PDF submissions) |
| [`docs/screenshots/README.md`](docs/screenshots/README.md) | Where to drop PNG captures for README / slides |
| [`docs/ACADEMIC_POLICY.md`](docs/ACADEMIC_POLICY.md) | Guidance on plagiarism / institutional policies |
| [`docs/RELEASE_NOTES_v1.0.0.md`](docs/RELEASE_NOTES_v1.0.0.md) | Human changelog for tagging |

The web SPA now shows an amber **development-server banner** reminding users Flask is **not production-hardened** by itself.

---

## Suggested GitHub topics

GitHub Topics must be toggled manually in the repository **About** settings. Paste a subset (pick ~5–10) such as:

`python`, `flask`, `information-theory`, `huffman-coding`, `lzw`, `lossless-compression`, `education`, `tkinter`, `hamming-code`, `data-compression`

---

## Releases

Create an annotated milestone after CI is green:

```bash
git tag -a v1.0.0 -m "v1.0.0 coursework bundle"
git push origin v1.0.0
```

Release notes draft: [`docs/RELEASE_NOTES_v1.0.0.md`](docs/RELEASE_NOTES_v1.0.0.md)

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
