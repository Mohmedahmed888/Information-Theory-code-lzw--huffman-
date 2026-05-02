"""
BONUS: Noisy Channel Simulation + Hamming Code Error Correction
Implemented entirely from scratch.

Pipeline:
  data -> Hamming encode -> Noisy Channel -> Hamming decode+correct -> data
"""

import random  # pseudo-random bit flips for BSC simulation
import struct  # pack/unpack fixed-size header fields
import os      # (kept for parity; may be useful for size checks)


# ─────────────────────────────────────────────
#  HAMMING CODE (7,4)
#  Each 4 data bits → 7-bit Hamming codeword
#  Can detect and correct 1-bit errors
# ─────────────────────────────────────────────

def _encode_hamming_nibble(nibble: int) -> int:
    """
    Encode a 4-bit value (nibble) into a 7-bit Hamming(7,4) codeword.
    Bit positions (1-indexed): p1, p2, d1, p3, d2, d3, d4
    """
    d1 = (nibble >> 3) & 1  # MSB of nibble
    d2 = (nibble >> 2) & 1
    d3 = (nibble >> 1) & 1
    d4 = (nibble >> 0) & 1  # LSB of nibble

    p1 = d1 ^ d2 ^ d4        # parity for positions 1,3,5,7 (Hamming rule)
    p2 = d1 ^ d3 ^ d4        # parity for positions 2,3,6,7
    p3 = d2 ^ d3 ^ d4        # parity for positions 4,5,6,7

    # 7-bit codeword: p1 p2 d1 p3 d2 d3 d4
    codeword = (p1 << 6) | (p2 << 5) | (d1 << 4) | (p3 << 3) | (d2 << 2) | (d3 << 1) | d4  # 7 bits packed in int
    return codeword


def _decode_hamming_nibble(codeword: int) -> tuple:
    """
    Decode a 7-bit Hamming(7,4) codeword.
    Returns (corrected_nibble, error_position) where error_position=0 means no error.
    """
    p1 = (codeword >> 6) & 1  # extract bits in same order we encoded
    p2 = (codeword >> 5) & 1
    d1 = (codeword >> 4) & 1
    p3 = (codeword >> 3) & 1
    d2 = (codeword >> 2) & 1
    d3 = (codeword >> 1) & 1
    d4 = (codeword >> 0) & 1

    s1 = p1 ^ d1 ^ d2 ^ d4  # syndrome bit for parity-check set 1
    s2 = p2 ^ d1 ^ d3 ^ d4  # syndrome bit for set 2
    s3 = p3 ^ d2 ^ d3 ^ d4  # syndrome bit for set 3

    error_pos = (s3 << 2) | (s2 << 1) | s1  # syndrome as 1..7 bit position (0 means "no error")

    if error_pos != 0:
        # Flip the erroneous bit
        codeword ^= (1 << (7 - error_pos))  # convert 1-indexed position to 0-indexed bit in our packing
        # Re-extract data bits after correction
        d1 = (codeword >> 4) & 1
        d2 = (codeword >> 2) & 1
        d3 = (codeword >> 1) & 1
        d4 = (codeword >> 0) & 1

    nibble = (d1 << 3) | (d2 << 2) | (d3 << 1) | d4
    return nibble, error_pos


def hamming_encode(data: bytes) -> bytes:
    """
    Encode bytes using Hamming(7,4).
    Each byte → 2 nibbles → 2 codewords (7 bits each) = 14 bits per byte.
    We pack 14-bit pairs as 2 bytes (with some overhead).
    Storage: each byte of input → 2 bytes of Hamming-encoded output.
    """
    result = bytearray()  # each input byte becomes 2 output bytes (two 7-bit codewords)
    for byte in data:
        high_nibble = (byte >> 4) & 0xF  # upper 4 bits
        low_nibble = byte & 0xF          # lower 4 bits
        cw_high = _encode_hamming_nibble(high_nibble)  # 7 bits
        cw_low = _encode_hamming_nibble(low_nibble)    # 7 bits
        # Pack as 2 bytes: [cw_high in bits 7:1 of first byte] [cw_low...]
        # We'll store them simply: byte1=cw_high, byte2=cw_low (both fit in 7 bits, MSB=0)
        result.append(cw_high)  # stored as a byte with MSB=0 (values 0..127)
        result.append(cw_low)
    return bytes(result)


def hamming_decode(data: bytes) -> tuple:
    """
    Decode Hamming-encoded bytes.
    Returns (decoded_bytes, errors_detected, errors_corrected).
    """
    result = bytearray()     # reconstructed bytes
    errors_detected = 0      # number of codewords with non-zero syndrome
    errors_corrected = 0     # for Hamming(7,4), detected==corrected for 1-bit errors

    for i in range(0, len(data), 2):
        if i + 1 >= len(data):
            break
        cw_high = data[i]       # first codeword for high nibble
        cw_low = data[i + 1]    # second codeword for low nibble

        high_nibble, err_h = _decode_hamming_nibble(cw_high)
        low_nibble, err_l = _decode_hamming_nibble(cw_low)

        if err_h != 0:
            errors_detected += 1
            errors_corrected += 1
        if err_l != 0:
            errors_detected += 1
            errors_corrected += 1

        byte = (high_nibble << 4) | low_nibble  # re-pack two nibbles into one byte
        result.append(byte)

    return bytes(result), errors_detected, errors_corrected


# ─────────────────────────────────────────────
#  BINARY SYMMETRIC CHANNEL (BSC)
#  Simulates noise by randomly flipping bits
# ─────────────────────────────────────────────

def simulate_bsc(data: bytes, error_probability: float, seed: int = None) -> tuple:
    """
    Pass data through a Binary Symmetric Channel.
    Each bit is independently flipped with probability p.
    
    Returns (noisy_data, num_bits_flipped, total_bits).
    """
    if seed is not None:
        random.seed(seed)  # deterministic runs (useful for demos/tests)

    total_bits = len(data) * 8   # number of Bernoulli trials (one per bit)
    bits_flipped = 0
    result = bytearray()

    for byte in data:
        noisy_byte = byte  # we flip bits in-place (XOR) to simulate errors
        for bit_pos in range(8):
            if random.random() < error_probability:
                noisy_byte ^= (1 << bit_pos)  # flip bit at position bit_pos (0=LSB)
                bits_flipped += 1
        result.append(noisy_byte)

    return bytes(result), bits_flipped, total_bits


# ─────────────────────────────────────────────
#  HIGH-LEVEL PIPELINE FUNCTIONS
# ─────────────────────────────────────────────

def encode_for_transmission(input_path: str, output_path: str) -> dict:
    """
    Hamming-encode a compressed file for safe transmission.
    
    File format:
    [4 bytes: original data length]
    [N bytes: Hamming-encoded data]
    """
    with open(input_path, 'rb') as f:
        data = f.read()  # raw compressed bytes (e.g., .huf / .lzw)

    original_len = len(data)      # stored so decode can trim back to exact length
    encoded = hamming_encode(data)  # add redundancy (2x bytes) for single-bit correction

    with open(output_path, 'wb') as f:
        f.write(struct.pack('>I', original_len))  # 4B header: original length
        f.write(encoded)                           # encoded payload

    return {
        'original_bytes': original_len,
        'encoded_bytes': len(encoded),
        'overhead_factor': round(len(encoded) / original_len, 2)
    }


def simulate_transmission(input_path: str, output_path: str, error_prob: float, seed: int = 42) -> dict:
    """Simulate passing encoded data through a noisy channel."""
    with open(input_path, 'rb') as f:
        header = f.read(4)        # protected header (not noised here for simplicity)
        encoded_data = f.read()   # encoded payload (this is what goes through the channel)

    noisy_data, flipped, total_bits = simulate_bsc(encoded_data, error_prob, seed)  # apply BSC bit flips

    with open(output_path, 'wb') as f:
        f.write(header)     # keep header uncorrupted for demo simplicity
        f.write(noisy_data) # noisy payload

    return {
        'total_bits': total_bits,
        'bits_flipped': flipped,
        'actual_ber': round(flipped / total_bits, 6) if total_bits > 0 else 0,
        'target_ber': error_prob
    }


def decode_after_transmission(input_path: str, output_path: str) -> dict:
    """
    Hamming-decode received data, correcting single-bit errors.
    """
    with open(input_path, 'rb') as f:
        original_len = struct.unpack('>I', f.read(4))[0]  # target length after decoding
        noisy_encoded = f.read()                           # received encoded bytes (with bit flips)

    decoded, detected, corrected = hamming_decode(noisy_encoded)  # correct single-bit errors per codeword
    decoded = decoded[:original_len]                               # trim to the original length from header

    with open(output_path, 'wb') as f:
        f.write(decoded)

    return {
        'errors_detected': detected,
        'errors_corrected': corrected,
        'output_bytes': len(decoded),
        'expected_bytes': original_len
    }
