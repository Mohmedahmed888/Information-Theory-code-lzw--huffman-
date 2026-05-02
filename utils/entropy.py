"""
Information Theory Utilities
Entropy calculation and analysis tools.
"""

import math                     # log2 for Shannon entropy
from collections import Counter # symbol frequency counts
import os                       # file size access for analysis


def calculate_entropy(data: bytes) -> float:
    """
    Calculate Shannon Entropy H(X) of a byte sequence.
    
    H(X) = -Σ p(x) * log2(p(x))
    
    Returns entropy in bits per symbol.
    """
    if not data:
        return 0.0  # define H(X)=0 for empty input

    n = len(data)         # total symbols
    freq = Counter(data)  # frequency of each byte value
    entropy = 0.0         # accumulator for -Σ p log2 p

    for count in freq.values():
        p = count / n                 # empirical probability of a symbol
        entropy -= p * math.log2(p)   # Shannon entropy contribution

    return entropy


def calculate_entropy_from_file(filepath: str) -> float:
    """Calculate entropy of a file."""
    with open(filepath, 'rb') as f:
        data = f.read()               # read entire file as bytes
    return calculate_entropy(data)    # reuse in-memory entropy function


def get_file_stats(filepath: str) -> dict:
    """Get comprehensive statistics about a file."""
    with open(filepath, 'rb') as f:
        data = f.read()  # read raw bytes for statistics

    size = len(data)     # file length in bytes
    if size == 0:
        return {}        # empty file → no meaningful stats

    freq = Counter(data)           # frequency table
    entropy = calculate_entropy(data)  # H(X) in bits/symbol

    # Theoretical minimum bits needed
    theoretical_min_bits = entropy * size      # lower bound bits ≈ H(X) * number_of_symbols
    theoretical_min_bytes = theoretical_min_bits / 8  # convert bits to bytes

    return {
        'file_size_bytes': size,                         # raw size
        'unique_symbols': len(freq),                     # distinct byte values present
        'entropy_bits_per_symbol': round(entropy, 6),     # H(X)
        'max_possible_entropy': 8.0,                     # log2(256) for bytes
        'entropy_efficiency': round(entropy / 8.0 * 100, 2),  # % of maximum uncertainty
        'theoretical_min_bytes': round(theoretical_min_bytes, 2),  # Shannon lower bound (ideal coder)
        'most_common': freq.most_common(5),              # top-5 frequent bytes
        'least_common': freq.most_common()[:-6:-1]       # bottom-5 frequent bytes
    }


def get_compression_analysis(original_path: str, compressed_path: str, algorithm: str) -> dict:
    """Full analysis comparing original vs compressed file."""
    orig_size = os.path.getsize(original_path)    # bytes before compression
    comp_size = os.path.getsize(compressed_path)  # bytes after compression

    with open(original_path, 'rb') as f:
        data = f.read()  # needed to compute entropy of original source

    entropy = calculate_entropy(data)                               # H(X) of original data
    ratio = orig_size / comp_size if comp_size > 0 else 0          # compression ratio (>1 is good)
    space_saved = (1 - comp_size / orig_size) * 100 if orig_size > 0 else 0  # % reduction

    return {
        'algorithm': algorithm,  # label only (no effect on calculations)
        'original_size': orig_size,
        'compressed_size': comp_size,
        'compression_ratio': round(ratio, 4),
        'space_saved_percent': round(space_saved, 2),
        'entropy': round(entropy, 6),
        'bits_per_byte_original': 8,  # baseline representation (1 byte = 8 bits)
        'bits_per_byte_compressed': round(comp_size * 8 / orig_size, 4) if orig_size > 0 else 0,  # avg bits/source byte
    }
