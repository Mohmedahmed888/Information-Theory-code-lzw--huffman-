"""
ECU Compression Tool — Flask Web Server
Run: python app.py
Then open: http://localhost:5000
"""

import os, sys, time, tracemalloc  # stdlib utilities used across the API
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # allow importing local packages when run directly

from flask import Flask, request, jsonify, send_file
from algorithms import huffman, lzw, channel  # compression algorithms + bonus channel pipeline
from utils.entropy import calculate_entropy  # entropy/statistics helpers (entropy used in API response)

app = Flask(__name__)  # Flask application instance
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')  # where uploaded inputs are stored
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'output')   # where generated outputs are written
WEB_FOLDER    = os.path.join(os.path.dirname(__file__), 'web')      # static UI (single-page HTML)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def fmt_size(b):
    if b < 1024: return f"{b} B"                 # bytes
    if b < 1024**2: return f"{b/1024:.1f} KB"    # kilobytes
    return f"{b/1024**2:.2f} MB"                 # megabytes

@app.route('/')
def index():
    with open(os.path.join(WEB_FOLDER, 'index.html'), 'r', encoding='utf-8') as f:  # serve the SPA HTML
        return f.read()  # simple static serve (no templating)

@app.route('/ecu-logo.png')
def logo():
    return send_file(os.path.join(WEB_FOLDER, 'ecu-logo.png'))  # static image for header

@app.route('/api/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400  # client didn't include multipart field "file"
    file      = request.files['file']                       # Werkzeug FileStorage
    mode      = request.form.get('mode', 'compress')         # 'compress' | 'decompress'
    use_ch    = request.form.get('use_channel', 'false') == 'true'  # bonus pipeline toggle (compress-only)
    ber       = float(request.form.get('ber', 0.01))         # target bit error rate for BSC simulation
    filename  = file.filename                               # original filename as sent by browser
    algorithm = request.form.get('algorithm', 'huffman')     # 'huffman' | 'lzw'
    src_path  = os.path.join(UPLOAD_FOLDER, filename)        # persist upload to disk (algorithms work with paths)
    file.save(src_path)                                     # write uploaded bytes to uploads/
    # If user is decompressing, infer algorithm from extension when possible.
    # This avoids confusing UX when the user picks the wrong algorithm.
    if mode == 'decompress':
        lower = (filename or '').lower()
        inferred = 'huffman' if lower.endswith('.huf') else ('lzw' if lower.endswith('.lzw') else None)
        if inferred and inferred != algorithm:
            algorithm = inferred

    alg_mod   = huffman if algorithm == 'huffman' else lzw   # module with compress()/decompress()
    ext       = '.huf' if algorithm == 'huffman' else '.lzw' # expected extension for this algorithm
    alg_label = 'Huffman Coding' if algorithm == 'huffman' else 'LZW'  # pretty label for UI
    try:
        if mode == 'decompress' and not filename.lower().endswith(ext):
            return jsonify({
                'error': f'For DECOMPRESS, please upload a {ext} file (you uploaded: {filename}).'
            }), 400
        with open(src_path, 'rb') as f:
            data = f.read()                                 # raw bytes used for entropy calculation
        entropy = calculate_entropy(data)                   # Shannon entropy (bits/symbol)
        if mode == 'compress':
            out_path = os.path.join(OUTPUT_FOLDER, filename + ext)  # append algorithm extension
        else:
            base = filename[:-len(ext)] if filename.endswith(ext) else filename  # strip .huf/.lzw if present
            _, orig_ext = os.path.splitext(base)                                # try to preserve original extension
            out_path = os.path.join(OUTPUT_FOLDER, base + '_decompressed' + (orig_ext or '.bin'))  # safe default .bin
        tracemalloc.start()                                # enable peak-memory measurement
        t0 = time.perf_counter()                           # high-resolution timer
        if mode == 'compress':
            stats = alg_mod.compress(src_path, out_path)    # algorithm produces output file on disk
        else:
            try:
                stats = alg_mod.decompress(src_path, out_path)  # reconstruct original bytes from compressed format
            except Exception as e:
                msg = str(e) or e.__class__.__name__
                # Common symptom when a non-compressed file is passed to decompress.
                if 'buffer of 4 bytes' in msg or 'unpack' in msg:
                    return jsonify({
                        'error': f'Invalid input for DECOMPRESS. Please upload a valid {ext} file produced by this tool.'
                    }), 400
                raise
        elapsed = time.perf_counter() - t0                  # seconds
        _, peak_mem = tracemalloc.get_traced_memory()       # bytes
        tracemalloc.stop()                                  # stop tracing to reduce overhead
        orig_size = os.path.getsize(src_path)               # input size (uploaded)
        out_size  = os.path.getsize(out_path)               # produced output size
        if mode == 'compress':
            ratio = orig_size / out_size if out_size > 0 else 0                  # >1 means smaller output
            saved = (1 - out_size / orig_size) * 100 if orig_size > 0 else 0     # percent reduction
        else:
            ratio = out_size / orig_size if orig_size > 0 else 0                 # invert for decompress view
            saved = (1 - orig_size / out_size) * 100 if out_size > 0 else 0      # typically negative in decompress
        result = {
            'success': True, 'algorithm': alg_label, 'mode': mode,
            'filename': os.path.basename(out_path),
            'original_size': fmt_size(orig_size), 'output_size': fmt_size(out_size),
            'ratio': round(ratio, 4), 'saved': round(saved, 2),
            'time_ms': round(elapsed * 1000, 2), 'memory_kb': round(peak_mem / 1024, 1),
            'entropy': round(entropy, 6),
            'lossless': stats.get('success', True) if mode == 'decompress' else None,
            'channel': None
        }
        if mode == 'compress' and use_ch:
            enc_path = out_path + '.hamming'; noisy_path = out_path + '.noisy'       # intermediate artifacts (debuggable)
            fixed_path = out_path + '.fixed'; recover_path = out_path + '.recovered' # decoded bytes + recovered original
            enc_s  = channel.encode_for_transmission(out_path, enc_path)             # Hamming(7,4) encode compressed file
            ch_s   = channel.simulate_transmission(enc_path, noisy_path, ber, seed=42) # BSC flips bits with probability ber
            fix_s  = channel.decode_after_transmission(noisy_path, fixed_path)       # correct single-bit errors per codeword
            try:
                alg_mod.decompress(fixed_path, recover_path)                         # attempt full recovery after FEC
                recovery = 'success'
            except:
                recovery = 'failed' if ber <= 0.05 else 'high_ber'                   # heuristic for UI messaging
            result['channel'] = {
                'ber': ber, 'encoded_size': fmt_size(enc_s['encoded_bytes']),
                'overhead': enc_s['overhead_factor'],
                'bits_flipped': ch_s['bits_flipped'], 'total_bits': ch_s['total_bits'],
                'actual_ber': ch_s['actual_ber'], 'errors_corrected': fix_s['errors_corrected'],
                'recovery': recovery
            }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # unexpected server-side error (stack trace stays in console)

@app.route('/api/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)  # only serves files from output/
    if os.path.exists(path):
        return send_file(path, as_attachment=True)  # browser downloads instead of viewing in-tab
    return jsonify({'error': 'File not found'}), 404 # missing output (or wrong filename)

# ── Live Reload ────────────────────────────────────
import hashlib, threading

_file_hashes = {}
_changed_flag = [False]

def _hash_file(path):
    try:
        return hashlib.md5(open(path, 'rb').read()).hexdigest()  # content hash to detect edits
    except:
        return ''  # file missing/unreadable → treat as unchanged

def _watch_files():
    watch = [
        os.path.join(WEB_FOLDER, 'index.html'),
        os.path.join(os.path.dirname(__file__), 'app.py'),
    ]
    for p in watch:
        _file_hashes[p] = _hash_file(p)  # seed initial hashes
    while True:
        time.sleep(1)  # polling interval (simple + good enough for local dev)
        for p in watch:
            h = _hash_file(p)
            if h != _file_hashes.get(p, ''):
                _file_hashes[p] = h
                _changed_flag[0] = True  # set flag; client will reload once it sees "changed"

@app.route('/api/ping')
def ping():
    changed = _changed_flag[0]     # read current "changed" state
    _changed_flag[0] = False       # reset after reporting (edge-triggered)
    return jsonify({'changed': changed, 'ok': True})  # client polls this endpoint

if __name__ == '__main__':
    t = threading.Thread(target=_watch_files, daemon=True)
    t.start()
    # Avoid UnicodeEncodeError on some Windows consoles (cp1252).
    print("\nECU Compression Tool")
    bind_host = os.environ.get('FLASK_HOST', '127.0.0.1')  # set FLASK_HOST=0.0.0.0 for Docker / LAN demos
    print(f"Listening on http://{bind_host}:5000")
    print("Live reload: ON — saving index.html reloads automatically\n")
    app.run(
        debug=False,
        host=bind_host,
        port=int(os.environ.get('FLASK_PORT', '5000')),
        use_reloader=False,
    )  # disable Flask reloader (we use our own ping-based reload)
