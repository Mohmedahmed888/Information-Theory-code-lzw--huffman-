"""
Huffman Coding - Implemented from scratch
Lossless compression algorithm using variable-length prefix codes.
"""

import heapq                 # priority queue (min-heap) for building Huffman tree
import struct                # pack/unpack fixed-size integers to/from bytes (file header)
import os                    # file size utilities
from collections import Counter  # frequency table (byte -> count)


class HuffmanNode:
    """Node in the Huffman binary tree."""
    def __init__(self, symbol, freq):
        self.symbol = symbol  # leaf: byte value (0-255); internal: None
        self.freq = freq      # subtree frequency used for heap ordering
        self.left = None      # left child (bit 0)
        self.right = None     # right child (bit 1)

    def __lt__(self, other):
        return self.freq < other.freq

    def __eq__(self, other):
        return self.freq == other.freq


def build_frequency_table(data: bytes) -> dict:
    """Count frequency of each byte in data."""
    return dict(Counter(data))  # Counter returns mapping byte->count; cast to dict for JSON-friendliness


def build_huffman_tree(freq_table: dict) -> HuffmanNode:
    """Build Huffman tree from frequency table using min-heap."""
    if not freq_table:
        return None  # no symbols to encode
    
    # Handle edge case: single unique symbol
    if len(freq_table) == 1:
        symbol, freq = list(freq_table.items())[0]
        root = HuffmanNode(None, freq)
        root.left = HuffmanNode(symbol, freq)  # use a single leaf as left child; code becomes "0"
        return root

    heap = [HuffmanNode(sym, freq) for sym, freq in freq_table.items()]  # one heap node per symbol
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)                      # smallest frequency subtree
        right = heapq.heappop(heap)                     # second smallest
        merged = HuffmanNode(None, left.freq + right.freq)  # internal parent combines the two
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0]


def generate_codes(node: HuffmanNode, prefix: str = "", codes: dict = None) -> dict:
    """Traverse Huffman tree to generate binary codes for each symbol."""
    if codes is None:
        codes = {}  # output mapping: byte -> string of '0'/'1'
    if node is None:
        return codes  # empty tree
    if node.symbol is not None:
        # Leaf node
        codes[node.symbol] = prefix if prefix else "0"  # single-symbol edge case uses "0"
        return codes
    generate_codes(node.left, prefix + "0", codes)   # left edge encodes bit 0
    generate_codes(node.right, prefix + "1", codes)  # right edge encodes bit 1
    return codes


def serialize_tree(node: HuffmanNode) -> bytes:
    """
    Serialize the Huffman tree into bytes for storage in file header.
    Format: 
      - Internal node: bit 0 + recurse left + recurse right
      - Leaf node: bit 1 + 1 byte symbol
    We store as a bitstream then pack into bytes.
    """
    bits = []                 # list[int] of 0/1 bits (will be packed into bytes)
    _serialize_node(node, bits)  # pre-order traversal with leaf markers + symbols
    # Pad to full bytes
    while len(bits) % 8 != 0:
        bits.append(0)        # padding for byte alignment (tree_bits_len tells real length)
    # Pack bits into bytes
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        result.append(byte)
    return bytes(result), len(bits)  # return packed bytes + number of valid bits (incl. pad bits)


def _serialize_node(node, bits):
    if node is None:
        return  # nothing to serialize
    if node.symbol is not None:
        # Leaf
        bits.append(1)                         # 1 = leaf marker
        sym_bits = format(node.symbol, '08b')  # store 8 bits of the symbol after marker
        for b in sym_bits:
            bits.append(int(b))
    else:
        # Internal
        bits.append(0)                 # 0 = internal node marker
        _serialize_node(node.left, bits)   # pre-order: node, left, right
        _serialize_node(node.right, bits)


def deserialize_tree(data: bytes, num_bits: int) -> HuffmanNode:
    """Reconstruct Huffman tree from serialized bytes."""
    bits = []  # unpack bytes into bit list (MSB first)
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    bits = bits[:num_bits]          # trim padding bits using the stored tree_bits length
    idx = [0]                       # use list as mutable "pointer" across recursion
    return _deserialize_node(bits, idx)  # build tree in the same pre-order format


def _deserialize_node(bits, idx):
    if idx[0] >= len(bits):
        return None  # malformed/short bitstream
    bit = bits[idx[0]]
    idx[0] += 1
    if bit == 1:
        # Leaf node
        sym = 0
        for i in range(8):
            sym = (sym << 1) | bits[idx[0]]
            idx[0] += 1
        return HuffmanNode(sym, 0)  # freq isn't needed for decoding
    else:
        # Internal node
        node = HuffmanNode(None, 0)
        node.left = _deserialize_node(bits, idx)   # parse left subtree first (pre-order)
        node.right = _deserialize_node(bits, idx)  # then right subtree
        return node


def compress(input_path: str, output_path: str) -> dict:
    """
    Compress a file using Huffman Coding.
    
    File format:
    [4 bytes: original size]
    [4 bytes: tree_bits length]
    [4 bytes: tree_bytes length]
    [N bytes: serialized tree]
    [4 bytes: number of padding bits in encoded data]
    [M bytes: encoded bitstream]
    
    Returns stats dict.
    """
    with open(input_path, 'rb') as f:
        data = f.read()  # read entire file as bytes (works for any file type)

    original_size = len(data)
    if original_size == 0:
        raise ValueError("Input file is empty.")

    freq_table = build_frequency_table(data)  # byte frequencies
    tree = build_huffman_tree(freq_table)     # optimal prefix-code tree
    codes = generate_codes(tree)              # byte -> bitstring mapping

    # Encode data as bitstream
    bit_string = ''.join(codes[byte] for byte in data)  # encode all bytes into 0/1 string
    padding = (8 - len(bit_string) % 8) % 8             # number of 0s to pad to full bytes
    bit_string += '0' * padding                         # pad at end; padding value stored in header

    # Pack bitstream into bytes
    encoded_bytes = bytearray()
    for i in range(0, len(bit_string), 8):
        encoded_bytes.append(int(bit_string[i:i+8], 2))  # pack each 8 bits into one output byte

    # Serialize tree
    tree_bytes, tree_bits_len = serialize_tree(tree)  # store decoding tree in file header

    with open(output_path, 'wb') as f:
        f.write(struct.pack('>I', original_size))         # 4B: size of original file (bytes)
        f.write(struct.pack('>I', tree_bits_len))         # 4B: number of bits in serialized tree
        f.write(struct.pack('>I', len(tree_bytes)))       # 4B: number of bytes used to store the tree
        f.write(tree_bytes)                               # NB: serialized tree (packed bits)
        f.write(struct.pack('>I', padding))               # 4B: number of padding bits in encoded stream
        f.write(bytes(encoded_bytes))                     # rest: encoded data bytes

    compressed_size = os.path.getsize(output_path)
    ratio = original_size / compressed_size if compressed_size > 0 else 0

    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'compression_ratio': ratio,
        'space_saved': round((1 - compressed_size / original_size) * 100, 2),
        'unique_symbols': len(freq_table),
        'codes': codes
    }


def decompress(input_path: str, output_path: str) -> dict:
    """
    Decompress a Huffman-encoded file.
    Reads the tree from the file header — completely independent from compression.
    """
    with open(input_path, 'rb') as f:
        original_size = struct.unpack('>I', f.read(4))[0]   # how many bytes to output
        tree_bits_len = struct.unpack('>I', f.read(4))[0]   # exact number of tree bits (trim padding)
        tree_bytes_len = struct.unpack('>I', f.read(4))[0]  # how many bytes follow for the tree
        tree_bytes = f.read(tree_bytes_len)                 # serialized tree blob
        padding = struct.unpack('>I', f.read(4))[0]         # how many bits to discard at end
        encoded_bytes = f.read()                            # remaining bytes are the encoded bitstream

    # Reconstruct tree from file header (independent of compression session)
    tree = deserialize_tree(tree_bytes, tree_bits_len)  # build decode tree from header (self-contained format)

    # Decode bitstream
    bit_string = ''.join(format(byte, '08b') for byte in encoded_bytes)  # bytes -> bits (MSB first)
    if padding > 0:
        bit_string = bit_string[:-padding]  # remove tail padding that was added during compression

    decoded = bytearray()
    node = tree  # walk the tree according to bits until reaching leaves
    for bit in bit_string:
        node = node.left if bit == '0' else node.right  # 0→left, 1→right
        if node.symbol is not None:
            decoded.append(node.symbol)  # emit decoded byte at leaf
            node = tree                 # restart from root for next symbol
            if len(decoded) == original_size:
                break  # stop once we reconstructed the expected original size

    with open(output_path, 'wb') as f:
        f.write(bytes(decoded))

    return {
        'decompressed_size': len(decoded),
        'expected_size': original_size,
        'success': len(decoded) == original_size
    }
