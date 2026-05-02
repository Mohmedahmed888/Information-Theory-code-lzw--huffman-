"""
Automated Test Suite for the Compression Project.
Tests Huffman, LZW, and Channel Bonus on 3 file types.
Run: python test_all.py
"""

import os
import sys
import time
import hashlib
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from algorithms import huffman, lzw, channel
from utils.entropy import calculate_entropy, get_file_stats

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_files")
OUT_DIR  = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(TEST_DIR, exist_ok=True)
os.makedirs(OUT_DIR,  exist_ok=True)


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def create_test_files():
    """Generate 3 different test file types."""
    # 1. Text file (natural English text)
    text_path = os.path.join(TEST_DIR, "sample_text.txt")
    if not os.path.exists(text_path):
        text = (
            "Information theory is the scientific study of the quantification, storage, "
            "and communication of digital information. The field was fundamentally established "
            "by the works of Harry Nyquist and Ralph Hartley in the 1920s, and Claude Shannon "
            "in the 1940s. A key measure in information theory is entropy. "
            "Entropy quantifies the amount of uncertainty involved in the value of a random "
            "variable or the outcome of a random process.\n"
        ) * 80
        with open(text_path, 'w') as f:
            f.write(text)

    # 2. Highly repetitive file (easy to compress)
    rep_path = os.path.join(TEST_DIR, "repetitive.bin")
    if not os.path.exists(rep_path):
        with open(rep_path, 'wb') as f:
            f.write(bytes([0xAB, 0xCD] * 5000))

    # 3. Random-ish binary (hard to compress — simulates bitmap data)
    import random
    rand_path = os.path.join(TEST_DIR, "pseudo_random.bin")
    if not os.path.exists(rand_path):
        random.seed(42)
        data = bytes([random.randint(0, 255) for _ in range(10000)])
        with open(rand_path, 'wb') as f:
            f.write(data)

    return {
        "Text File": text_path,
        "Repetitive Binary": rep_path,
        "Pseudo-Random Binary": rand_path
    }


def run_test(name, src_path, alg_name, alg_mod, ext):
    print(f"\n  [{alg_name}] → {name}")
    comp_path   = os.path.join(OUT_DIR, os.path.basename(src_path) + ext)
    decomp_path = os.path.join(OUT_DIR, os.path.basename(src_path) + "_decompressed" + os.path.splitext(src_path)[1])

    orig_size = os.path.getsize(src_path)

    # Compress
    tracemalloc.start()
    t0 = time.perf_counter()
    stats_c = alg_mod.compress(src_path, comp_path)
    t_comp = time.perf_counter() - t0
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Decompress
    t0 = time.perf_counter()
    stats_d = alg_mod.decompress(comp_path, decomp_path)
    t_decomp = time.perf_counter() - t0

    # Verify lossless
    ok = md5(src_path) == md5(decomp_path)

    comp_size = os.path.getsize(comp_path)
    ratio = orig_size / comp_size if comp_size > 0 else 0

    with open(src_path, 'rb') as f:
        data = f.read()
    entropy = calculate_entropy(data)

    print(f"    Original Size    : {orig_size:,} bytes")
    print(f"    Compressed Size  : {comp_size:,} bytes")
    print(f"    Ratio            : {ratio:.4f}x  |  Saved: {(1-comp_size/orig_size)*100:.1f}%")
    print(f"    H(X) Entropy     : {entropy:.6f} bits/symbol")
    print(f"    Compress Time    : {t_comp*1000:.2f} ms")
    print(f"    Decompress Time  : {t_decomp*1000:.2f} ms")
    print(f"    Peak Memory      : {peak_mem/1024:.1f} KB")
    print(f"    Lossless Check   : {'✅ PASS' if ok else '❌ FAIL'}")

    return {
        'orig_size': orig_size, 'comp_size': comp_size,
        'ratio': ratio, 'entropy': entropy,
        't_comp': t_comp, 't_decomp': t_decomp,
        'memory_kb': peak_mem / 1024, 'lossless': ok
    }


def run_bonus(src_path):
    print(f"\n  [BONUS] Channel Simulation on: {os.path.basename(src_path)}")
    comp_path   = os.path.join(OUT_DIR, "bonus_compressed.huf")
    enc_path    = comp_path + ".hamming"
    noisy_path  = comp_path + ".noisy"
    fixed_path  = comp_path + ".fixed"
    recover_path = comp_path + ".recovered"

    huffman.compress(src_path, comp_path)

    for ber in [0.001, 0.01]:
        print(f"\n    BER = {ber}")
        enc_s = channel.encode_for_transmission(comp_path, enc_path)
        ch_s  = channel.simulate_transmission(enc_path, noisy_path, ber, seed=42)
        fix_s = channel.decode_after_transmission(noisy_path, fixed_path)
        try:
            huffman.decompress(fixed_path, recover_path)
            ok = open(src_path,'rb').read() == open(recover_path,'rb').read()
            print(f"    Bits flipped     : {ch_s['bits_flipped']}")
            print(f"    Errors corrected : {fix_s['errors_corrected']}")
            print(f"    Recovery         : {'✅ SUCCESS' if ok else '⚠️  PARTIAL'}")
        except Exception as e:
            print(f"    Recovery         : ❌ FAILED ({e})")


if __name__ == "__main__":
    print("=" * 60)
    print("  ECU Information Theory — Compression Project Test Suite")
    print("=" * 60)

    files = create_test_files()

    for file_name, file_path in files.items():
        print(f"\n{'─'*60}")
        print(f"  FILE: {file_name} ({os.path.getsize(file_path):,} bytes)")
        print(f"{'─'*60}")
        run_test(file_name, file_path, "Huffman", huffman, ".huf")
        run_test(file_name, file_path, "LZW",     lzw,     ".lzw")

    print(f"\n{'─'*60}")
    print("  BONUS: Noisy Channel + Hamming Error Correction")
    print(f"{'─'*60}")
    text_path = list(files.values())[0]
    run_bonus(text_path)

    print(f"\n{'='*60}")
    print("  All tests complete!")
    print(f"{'='*60}\n")
