"""
tests/test_huffman.py — Unit Tests for the Huffman Engine
==========================================================
Run with:  python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from huffman import (
    frequency_table,
    build_huffman_tree,
    generate_codes,
    compress,
    decompress,
    compression_report,
    HuffmanNode,
)


# ─── frequency_table ───────────────────────────────────────────────

class TestFrequencyTable:
    def test_basic(self):
        freq = frequency_table("aabbc")
        assert freq['a'] == 2
        assert freq['b'] == 2
        assert freq['c'] == 1

    def test_single_char(self):
        freq = frequency_table("aaaa")
        assert freq == {'a': 4}

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            frequency_table("")

    def test_all_unique(self):
        freq = frequency_table("abcde")
        assert len(freq) == 5
        assert all(v == 1 for v in freq.values())


# ─── build_huffman_tree ────────────────────────────────────────────

class TestBuildHuffmanTree:
    def test_root_freq_equals_total(self):
        freq = frequency_table("aabbcc")
        root = build_huffman_tree(freq)
        assert root.freq == 6

    def test_leaves_are_chars(self):
        freq = {'a': 3, 'b': 1}
        root = build_huffman_tree(freq)
        # One child should be 'a', total freq = 4
        assert root.freq == 4

    def test_single_unique_char(self):
        freq = {'z': 5}
        root = build_huffman_tree(freq)
        assert root.left is not None
        assert root.left.char == 'z'


# ─── generate_codes ───────────────────────────────────────────────

class TestGenerateCodes:
    def test_all_chars_have_codes(self):
        freq  = frequency_table("abcde")
        root  = build_huffman_tree(freq)
        codes = generate_codes(root)
        assert set(codes.keys()) == set("abcde")

    def test_more_frequent_shorter_code(self):
        # 'a' appears 10x, 'b' appears 1x → code('a') ≤ code('b')
        freq  = {'a': 10, 'b': 1, 'c': 1}
        root  = build_huffman_tree(freq)
        codes = generate_codes(root)
        assert len(codes['a']) <= len(codes['b'])

    def test_codes_are_binary_strings(self):
        freq  = frequency_table("hello world")
        root  = build_huffman_tree(freq)
        codes = generate_codes(root)
        for code in codes.values():
            assert all(bit in '01' for bit in code)


# ─── compress / decompress round-trip ─────────────────────────────

ROUND_TRIP_CASES = [
    "hello",
    "aaaaaa",
    "abcdefghijklmnopqrstuvwxyz",
    "The quick brown fox jumps over the lazy dog",
    "12345!@#$%",
    "a" * 1000,
    "Huffman coding reduces file size efficiently.",
]

class TestRoundTrip:
    @pytest.mark.parametrize("text", ROUND_TRIP_CASES)
    def test_compress_decompress(self, text):
        freq       = frequency_table(text)
        root       = build_huffman_tree(freq)
        codes      = generate_codes(root)
        compressed = compress(text, codes)
        recovered  = decompress(compressed, root)
        assert recovered == text, f"Round-trip failed for: {text[:40]!r}"

    def test_compressed_smaller_than_original_long(self):
        text = "aaabbbbbcccccccddddddddddeeeeeeeeeeeeeeee"
        freq = frequency_table(text)
        root = build_huffman_tree(freq)
        codes = generate_codes(root)
        compressed = compress(text, codes)
        # Compressed bytes should be less than original chars
        assert len(compressed) < len(text)


# ─── compression_report ────────────────────────────────────────────

class TestCompressionReport:
    def test_report_keys(self):
        text  = "hello world"
        freq  = frequency_table(text)
        root  = build_huffman_tree(freq)
        codes = generate_codes(root)
        comp  = compress(text, codes)
        report = compression_report(text, comp, codes, freq)

        required_keys = [
            'original_chars', 'unique_chars', 'original_size_bits',
            'compressed_size_bits', 'compression_ratio', 'space_savings_pct',
            'avg_code_length',
        ]
        for key in required_keys:
            assert key in report

    def test_savings_between_0_and_100(self):
        text  = "the lazy dog jumps over the fence"
        freq  = frequency_table(text)
        root  = build_huffman_tree(freq)
        codes = generate_codes(root)
        comp  = compress(text, codes)
        report = compression_report(text, comp, codes, freq)
        assert 0 <= report['space_savings_pct'] <= 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
