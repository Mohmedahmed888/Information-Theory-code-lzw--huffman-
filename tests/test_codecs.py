"""Unit tests for Huffman and LZW codecs (lossless round-trips, edge cases)."""

from __future__ import annotations

import hashlib
import os
import tempfile

import pytest

from algorithms import huffman, lzw


def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def test_huffman_rejects_empty_file():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "empty.bin")
        out = os.path.join(td, "empty.huf")
        open(src, "wb").close()
        with pytest.raises(ValueError, match="empty"):
            huffman.compress(src, out)


def test_lzw_rejects_empty_file():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "empty.bin")
        out = os.path.join(td, "empty.lzw")
        open(src, "wb").close()
        with pytest.raises(ValueError, match="empty"):
            lzw.compress(src, out)


def test_huffman_single_byte_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "one.bin")
        comp = os.path.join(td, "one.huf")
        dec = os.path.join(td, "one.dec.bin")
        with open(src, "wb") as f:
            f.write(b"\x00")
        huffman.compress(src, comp)
        huffman.decompress(comp, dec)
        assert _md5(src) == _md5(dec)


def test_lzw_single_byte_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "one.bin")
        comp = os.path.join(td, "one.lzw")
        dec = os.path.join(td, "one.dec.bin")
        with open(src, "wb") as f:
            f.write(b"Z")
        lzw.compress(src, comp)
        lzw.decompress(comp, dec)
        assert _md5(src) == _md5(dec)


@pytest.mark.parametrize("payload", [b"abababab", os.urandom(256), bytes(range(256)) * 40])
def test_huffman_roundtrip_binary_payload(payload):
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.bin")
        comp = os.path.join(td, "in.huf")
        dec = os.path.join(td, "out.bin")
        with open(src, "wb") as f:
            f.write(payload)
        huffman.compress(src, comp)
        huffman.decompress(comp, dec)
        assert _md5(src) == _md5(dec)


@pytest.mark.parametrize("payload", [b"a" * 5000 + b"b" * 3000, os.urandom(2048)])
def test_lzw_roundtrip_binary_payload(payload):
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.bin")
        comp = os.path.join(td, "in.lzw")
        dec = os.path.join(td, "out.bin")
        with open(src, "wb") as f:
            f.write(payload)
        lzw.compress(src, comp)
        lzw.decompress(comp, dec)
        assert _md5(src) == _md5(dec)


def test_lzw_kwkwk_edge_pattern_roundtrip():
    payload = b"a" + b"a" * 200
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "kw.bin")
        comp = os.path.join(td, "kw.lzw")
        dec = os.path.join(td, "kw.out.bin")
        with open(src, "wb") as f:
            f.write(payload)
        lzw.compress(src, comp)
        lzw.decompress(comp, dec)
        assert payload == open(dec, "rb").read()


def test_huffman_all_same_byte_large():
    payload = b"\xEE" * 50_000
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "rep.bin")
        comp = os.path.join(td, "rep.huf")
        dec = os.path.join(td, "rep.out.bin")
        with open(src, "wb") as f:
            f.write(payload)
        huffman.compress(src, comp)
        huffman.decompress(comp, dec)
        assert payload == open(dec, "rb").read()
