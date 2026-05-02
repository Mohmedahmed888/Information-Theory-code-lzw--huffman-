from __future__ import annotations

from utils.entropy import calculate_entropy


def test_entropy_empty_zero():
    assert calculate_entropy(b"") == 0.0


def test_entropy_single_symbol():
    # One repeated symbol -> H(X)=0 bits/symbol under empirical distribution on bytes present
    data = b"AAAAAA"
    assert calculate_entropy(data) == 0.0


def test_entropy_uniform_four_symbols():
    # A,B,C,D each with p=1/4 -> H=2 bits
    assert abs(calculate_entropy(b"ABCD") - 2.0) < 1e-9
