"""
huffman.py — Core Huffman Coding Engine
========================================
Implements:
  • HuffmanNode  — binary tree node
  • frequency_table() — character frequency counter
  • build_huffman_tree() — min-heap based tree construction
  • generate_codes() — DFS code table builder
  • compress() — text → bit-string → padded bytes
  • decompress() — padded bytes → bit-string → text
  • compression_report() — stats and ratio
"""

import heapq
import os
import pickle
from collections import Counter


# ─────────────────────────────────────────────
# 1. Node Class
# ─────────────────────────────────────────────

class HuffmanNode:
    """
    A node in the Huffman Binary Tree.

    Attributes:
        char  : The character (None for internal nodes)
        freq  : Frequency / weight of this node
        left  : Left child  (represents bit '0')
        right : Right child (represents bit '1')
    """

    def __init__(self, char, freq):
        self.char  = char
        self.freq  = freq
        self.left  = None
        self.right = None

    # Needed so heapq can compare nodes
    def __lt__(self, other):
        return self.freq < other.freq

    def __repr__(self):
        return f"HuffmanNode(char={self.char!r}, freq={self.freq})"


# ─────────────────────────────────────────────
# 2. Frequency Table
# ─────────────────────────────────────────────

def frequency_table(text: str) -> dict:
    """
    Count how many times each character appears in `text`.

    Returns:
        dict  {char: count}  sorted descending by count
    """
    if not text:
        raise ValueError("Input text is empty — nothing to compress.")

    counts = Counter(text)
    # Sort by frequency descending (for display), then by char for stability
    return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))


# ─────────────────────────────────────────────
# 3. Build Huffman Tree (Min-Heap / Priority Queue)
# ─────────────────────────────────────────────

def build_huffman_tree(freq_dict: dict) -> HuffmanNode:
    """
    Build the Huffman Tree using a Min-Heap (Priority Queue).

    Algorithm:
      1. Create one leaf node per unique character.
      2. Push all leaf nodes onto a min-heap (lowest freq = highest priority).
      3. Repeatedly:
           a. Pop two nodes with smallest frequencies  →  left, right
           b. Create an internal node  (freq = left.freq + right.freq)
           c. Push internal node back onto heap
      4. When only one node remains → it's the root.

    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    if len(freq_dict) == 1:
        # Edge case: only one unique character
        char, freq = next(iter(freq_dict.items()))
        root = HuffmanNode(None, freq)
        root.left = HuffmanNode(char, freq)
        return root

    heap = []
    for char, freq in freq_dict.items():
        node = HuffmanNode(char, freq)
        heapq.heappush(heap, node)

    while len(heap) > 1:
        left  = heapq.heappop(heap)   # smallest freq
        right = heapq.heappop(heap)   # second smallest

        # Internal node: no character, freq = sum of children
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left  = left
        merged.right = right

        heapq.heappush(heap, merged)

    return heap[0]   # root of Huffman Tree


# ─────────────────────────────────────────────
# 4. Generate Huffman Codes (DFS traversal)
# ─────────────────────────────────────────────

def generate_codes(root: HuffmanNode) -> dict:
    """
    Traverse the Huffman Tree depth-first to build code table.

    Left branch  → append '0'
    Right branch → append '1'

    Returns:
        dict  {char: binary_code_string}
    """
    codes = {}

    def _dfs(node, current_code):
        if node is None:
            return
        if node.char is not None:           # Leaf node
            codes[node.char] = current_code or '0'
            return
        _dfs(node.left,  current_code + '0')
        _dfs(node.right, current_code + '1')

    _dfs(root, '')
    return codes


# ─────────────────────────────────────────────
# 5. Compress
# ─────────────────────────────────────────────

def compress(text: str, codes: dict) -> bytes:
    """
    Convert text into a compressed byte sequence.

    Steps:
      1. Replace each character with its Huffman binary code.
      2. Pad the bit-string to a multiple of 8 (so it fits into bytes).
      3. Store the padding length in the first byte.
      4. Convert each group of 8 bits into one byte.

    Returns:
        bytes  (padded_info_byte + compressed_data_bytes)
    """
    # Step 1: Build the full bit-string
    bit_string = ''.join(codes[char] for char in text)

    # Step 2: Pad to multiple of 8
    padding = 8 - (len(bit_string) % 8)
    if padding == 8:
        padding = 0
    bit_string += '0' * padding

    # Step 3: First byte encodes how many padding bits were added
    padded_info = f"{padding:08b}"        # 8-bit binary string of padding count

    full_bits = padded_info + bit_string

    # Step 4: Convert 8-bit chunks → bytes
    byte_array = bytearray()
    for i in range(0, len(full_bits), 8):
        byte = int(full_bits[i:i+8], 2)
        byte_array.append(byte)

    return bytes(byte_array)


# ─────────────────────────────────────────────
# 6. Decompress
# ─────────────────────────────────────────────

def decompress(compressed_bytes: bytes, root: HuffmanNode) -> str:
    """
    Reconstruct original text from compressed bytes + Huffman tree.

    Steps:
      1. Convert bytes → bit-string.
      2. Read padding length from first byte.
      3. Remove padding bits from the end.
      4. Walk the Huffman Tree bit-by-bit:
           '0' → go left
           '1' → go right
         When a leaf is reached → emit character, return to root.

    Returns:
        str  (original text)
    """
    # Step 1: Convert every byte to 8-bit binary string
    bit_string = ''.join(f"{byte:08b}" for byte in compressed_bytes)

    # Step 2: Extract padding info from first byte
    padding = int(bit_string[:8], 2)

    # Step 3: Remove padding info byte and trailing padding bits
    data_bits = bit_string[8:]
    if padding:
        data_bits = data_bits[:-padding]

    # Step 4: Decode using the Huffman Tree
    decoded_chars = []
    current = root

    for bit in data_bits:
        if bit == '0':
            current = current.left
        else:
            current = current.right

        if current.char is not None:       # Reached a leaf
            decoded_chars.append(current.char)
            current = root                  # Reset to root

    return ''.join(decoded_chars)


# ─────────────────────────────────────────────
# 7. Save / Load compressed file
# ─────────────────────────────────────────────

def save_compressed(compressed_bytes: bytes, tree: HuffmanNode, output_path: str):
    """
    Save compressed bytes + Huffman tree (for decompression) to disk.
    Uses Python pickle to serialize the tree alongside the data.
    """
    with open(output_path, 'wb') as f:
        pickle.dump({'tree': tree, 'data': compressed_bytes}, f)


def load_compressed(file_path: str):
    """
    Load compressed file.
    Returns: (compressed_bytes, huffman_tree_root)
    """
    with open(file_path, 'rb') as f:
        payload = pickle.load(f)
    return payload['data'], payload['tree']


# ─────────────────────────────────────────────
# 8. Compression Ratio Report
# ─────────────────────────────────────────────

def compression_report(original_text: str, compressed_bytes: bytes,
                        codes: dict, freq_dict: dict) -> dict:
    """
    Calculate compression statistics.

    Returns dict with:
        original_size_bits    : bits required with 8-bit ASCII
        compressed_size_bits  : bits after Huffman coding
        compression_ratio     : compressed / original  (lower = better)
        space_savings_pct     : % bits saved
        avg_code_length       : weighted average code length
    """
    original_bits    = len(original_text) * 8
    # Compressed size = compressed_bytes * 8 minus 8 bits (padding info byte)
    compressed_bits  = (len(compressed_bytes) - 1) * 8

    total_chars = sum(freq_dict.values())
    avg_code_len = sum(
        (freq / total_chars) * len(codes[ch])
        for ch, freq in freq_dict.items()
    )

    ratio   = compressed_bits / original_bits if original_bits else 0
    savings = (1 - ratio) * 100

    return {
        'original_chars'      : len(original_text),
        'unique_chars'        : len(freq_dict),
        'original_size_bits'  : original_bits,
        'original_size_bytes' : original_bits // 8,
        'compressed_size_bits': compressed_bits,
        'compressed_size_bytes': len(compressed_bytes),
        'compression_ratio'   : round(ratio, 4),
        'space_savings_pct'   : round(savings, 2),
        'avg_code_length'     : round(avg_code_len, 4),
    }
