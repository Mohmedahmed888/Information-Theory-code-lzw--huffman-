from __future__ import annotations

from utils.entropy import calculate_entropy


def test_entropy_empty_zero():
    assert calculate_entropy(b"") == 0.0


def test_entropy_single_symbol():
    assert calculate_entropy(b"AAAAAA") == 0.0


def test_entropy_uniform_four_symbols():
    assert abs(calculate_entropy(b"ABCD") - 2.0) < 1e-9
