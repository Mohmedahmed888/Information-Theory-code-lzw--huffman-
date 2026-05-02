"""
LZW (Lempel-Ziv-Welch) Compression - Implemented from scratch
Dictionary-based lossless compression algorithm.
"""

import struct  # binary header + 16-bit code packing
import os      # file size utilities


# LZW Parameters
INITIAL_DICT_SIZE = 256    # initial dictionary: every possible single byte (0..255)
MAX_DICT_SIZE = 65536      # maximum dictionary size (fits in 16-bit unsigned int)
CODE_BITS = 16             # fixed-width codes in file (keeps format simple)


def build_initial_dict_compress() -> dict:
    """Initialize compression dictionary with all single-byte strings."""
    return {bytes([i]): i for i in range(INITIAL_DICT_SIZE)}  # bytes-sequence -> code


def build_initial_dict_decompress() -> dict:
    """Initialize decompression dictionary with all single-byte strings."""
    return {i: bytes([i]) for i in range(INITIAL_DICT_SIZE)}  # code -> bytes-sequence


def compress(input_path: str, output_path: str) -> dict:
    """
    Compress a file using LZW algorithm.
    
    File format:
    [4 bytes: original file size]
    [4 bytes: number of codes]
    [N * 2 bytes: 16-bit LZW codes]
    
    The dictionary is rebuilt from scratch on decompression — no dict stored.
    """
    with open(input_path, 'rb') as f:
        data = f.read()  # raw bytes (works for any binary file)

    original_size = len(data)
    if original_size == 0:
        raise ValueError("Input file is empty.")

    dictionary = build_initial_dict_compress()  # current sequence -> code
    next_code = INITIAL_DICT_SIZE               # first free code after 0..255
    codes = []                                  # output code stream

    # LZW encoding loop (classic "w + c" growth)
    w = bytes([data[0]])  # current longest sequence found in dictionary
    for i in range(1, len(data)):
        c = bytes([data[i]])  # next input symbol as 1-byte sequence
        wc = w + c            # try extending current match
        if wc in dictionary:
            w = wc            # keep growing match while it exists in dict
        else:
            codes.append(dictionary[w])         # emit code for the longest known sequence w
            if next_code < MAX_DICT_SIZE:       # only add if we still have code space
                dictionary[wc] = next_code      # add new sequence wc to dictionary
                next_code += 1
            w = c                               # restart match from current symbol
    codes.append(dictionary[w])                 # emit code for final w

    # Write to file
    with open(output_path, 'wb') as f:
        f.write(struct.pack('>I', original_size))          # 4B: original file size (bytes)
        f.write(struct.pack('>I', len(codes)))             # 4B: number of 16-bit codes to read
        for code in codes:
            f.write(struct.pack('>H', code))               # 2B: each code (big-endian unsigned short)

    compressed_size = os.path.getsize(output_path)
    ratio = original_size / compressed_size if compressed_size > 0 else 0

    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'compression_ratio': ratio,
        'space_saved': round((1 - compressed_size / original_size) * 100, 2),
        'dictionary_size': next_code,
        'num_codes': len(codes)
    }


def decompress(input_path: str, output_path: str) -> dict:
    """
    Decompress an LZW-encoded file.
    Rebuilds the dictionary from scratch — completely independent from compression.
    The dictionary is NOT stored in the file; it is reconstructed algorithmically.
    """
    with open(input_path, 'rb') as f:
        original_size = struct.unpack('>I', f.read(4))[0]  # expected output length
        num_codes = struct.unpack('>I', f.read(4))[0]      # how many codes follow
        codes = []                                         # read code stream into memory
        for _ in range(num_codes):
            code = struct.unpack('>H', f.read(2))[0]       # each code is 2 bytes
            codes.append(code)

    if not codes:
        with open(output_path, 'wb') as f:
            pass
        return {'decompressed_size': 0, 'success': True}

    # LZW decoding — rebuilds dictionary from the code stream
    dictionary = build_initial_dict_decompress()  # code -> bytes
    next_code = INITIAL_DICT_SIZE                 # first free code for newly discovered sequences

    result = bytearray()               # output buffer
    w = dictionary[codes[0]]           # first code always exists in initial dictionary
    result.extend(w)                   # write first decoded sequence

    for code in codes[1:]:
        if code in dictionary:
            entry = dictionary[code]   # normal case: code already mapped
        elif code == next_code:
            # Special case: code not yet in dict
            entry = w + bytes([w[0]])  # KwKwK case: entry = w + first_char(w)
        else:
            raise ValueError(f"Invalid LZW code: {code}")  # corrupted stream / wrong file

        result.extend(entry)  # append decoded sequence to output

        if next_code < MAX_DICT_SIZE:
            dictionary[next_code] = w + bytes([entry[0]])  # add new sequence to dict
            next_code += 1

        w = entry  # shift window: previous sequence becomes current

    with open(output_path, 'wb') as f:
        f.write(bytes(result))

    return {
        'decompressed_size': len(result),
        'expected_size': original_size,               # size from header
        'success': len(result) == original_size       # simple integrity check
    }
