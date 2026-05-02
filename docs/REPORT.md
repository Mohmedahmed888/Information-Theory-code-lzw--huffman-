# Technical report — Huffman & LZW lossless compression (course project)

This document summarizes the theory, engineering choices, and evaluation strategy used in this repository. Keep it aligned with whatever formal PDF/report your instructor requires — this file is a **structured outline** you can adapt.

---

## 1. Motivation / problem statement

The goal is to implement **lossless** compression utilities suitable for coursework demonstration:

1. Compress arbitrary binary payloads without losing information.  
2. Decompress reliably, without requiring hidden side-information beyond what is encoded in the file.  
3. Compare two classic approaches: **Huffman coding** vs **dictionary-based LZW**.

---

## 2. Theory (concise)

### 2.1 Information content and entropy

For an empirical distribution over symbols (bytes) with probabilities \(p_i\),

\[
H(X) = -\sum_i p_i \log_2 p_i \quad [\text{bits per symbol}]
\]

Interpretation: redundancy in data enables compression; highly random/high-entropy data approaches the maximum \(\log_2(256)=8\) bits/byte under a byte-aligned symbol model used here.

### 2.2 Huffman coding

Huffman codes are optimal **prefix codes** under a symbol-frequency model constructed from observed byte counts. Prefix-free structure ensures unique decodability given a synchronized bitstream and an agreed rule for padding.

Implementation detail relevant to interoperability: Huffman decoding requires reconstructing the code tree — this project achieves independence by embedding a serialized Huffman tree in the `.huf` header.

### 2.3 LZW (Lempel–Ziv–Welch)

LZW parses the input sequentially, emitting dictionary indices for maximal matching prefixes and extending the dictionary with new phrases. Decoder rebuilds identical dictionary dynamics from emitted codes alone (excluding certain edge synchronization cases handled by KwKwK logic).

Implementation trade-off in this codebase: codes are emitted as fixed **16-bit** values simplifying binary file handling while potentially increasing overhead for small payloads.

---

## 3. System architecture

Three user-facing interfaces share the same core modules:

| Interface | Purpose | Dependencies |
|-----------|---------|----------------|
| `gui/app.py` | Desktop demos | Tkinter (stdlib + OS UI) |
| `app.py` | Web demos/API | Flask (see `requirements.txt`) |
| `test_all.py` | Scripted evaluation | Standard library |

Core modules reside in `algorithms/` and utilities in `utils/`.

---

## 4. On-disk formats (high level)

### 4.1 Huffman `.huf`

Structured header storing:

- Original byte length  
- Serialized tree (+ bit-length metadata needed to discard padding artifacts)  
- Padding count for coded payload remainder  
- Encoded payload bitstream  

### 4.2 LZW `.lzw`

Header stores:

- Original byte length  
- Count of 16-bit codes  
- Subsequent big-endian shorts represent code stream  

---

## 5. Experimental methodology / evaluation metrics

Measured outputs include:

- **Compression ratio** (original compressed size interpretation depends on metric definition in UI/report)  
- **Space saved percentage**  
- Wall clock time segments (compression vs decompression phases)  
- Peak memory allocations using `tracemalloc` instrumentation in higher-level tooling  
- **Lossless correctness** validated by hashing original versus decompressed payloads

Interpretation caveat: randomized/pseudorandom data should not compress aggressively (and often expands slightly after overhead framing).

---

## 6. Bonus: noisy transmission model

Demonstrate robustness notions using:

1. Encode compressed bytes redundantly via **Hamming(7,4)** on nibbles  
2. Apply **binary symmetric channel** BER noise at bit granularity  
3. Decode with syndrome-based single-bit correction per codeword  
4. Optional attempt to decompress after correction (may fail beyond Hamming correction capacity).

---

## 7. Operational security note

Development Flask server is intentionally simple. Exposure on untrusted networks should be preceded by hardened deployment patterns (bounded hosts, HTTPS termination, hardened process manager).

---

## 8. Appendix (recommended figures for grading packets)

Screenshots placeholders live under:

- `docs/screenshots/` (instructions in `README` there)
