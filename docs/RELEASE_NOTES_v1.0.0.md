# Release notes — Information Theory Compression Toolkit

## Bundled tooling

- Huffman + LZW codecs (`algorithms/`)
- Flask web UI + Tkinter GUI + `test_all.py`
- **`tests/`** — `pytest` regressions for codecs & entropy
- **`requirements-dev.txt`** — `pytest` + `ruff`
- **GitHub Actions CI** — `ruff`, `pytest`, `test_all.py`
- **Dockerfile** — optional Flask container (`FLASK_HOST=0.0.0.0`)

## Verify locally

```bash
pip install -r requirements-dev.txt
ruff check .
pytest tests/ -v
python test_all.py
```
