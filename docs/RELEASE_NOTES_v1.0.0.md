# Release `v1.0.0` — Information Theory Compression Toolkit

Initial public release bundled for coursework demos and reproducible evaluation.

## Highlights

- Huffman codec with **serialized tree header** (`.huf`)
- LZW codec with **16-bit codes** and decoder **KwKwK** handling (`.lzw`)
- Shannon entropy estimation (`utils/entropy.py`)
- **Tkinter GUI** (`gui/app.py`)
- **Flask web UI** + JSON API (`app.py`, `web/index.html`)
- Optional **Hamming(7,4) + BSC** bonus pipeline (`algorithms/channel.py`)
- Automated integration suite (`test_all.py`)

## Developer experience

- `requirements-dev.txt` for **ruff** (lint-only dev helper)
- GitHub Actions **CI**: lint (`ruff`), `test_all.py` smoke pass
- `Dockerfile` for containerized Web UI (`FLASK_HOST=0.0.0.0`)

## Operational notes

- Flask’s built-in server is suitable for **local demos**, not unsecured public hosting.
- On Windows consoles, avoid Unicode-only separators in CLI logs (`test_all.py` uses ASCII separators for portability).

## Verify locally

```bash
pip install -r requirements-dev.txt
ruff check .
python test_all.py
```
