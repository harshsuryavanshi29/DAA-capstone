# Algorithm Notes — Huffman Coding

## Why Huffman Works

### Shannon's Source Coding Theorem
The optimal average code length L* for a source satisfies:
  H(X) ≤ L* < H(X) + 1

Where H(X) is the entropy: H(X) = -∑ p(x) log₂ p(x)

Huffman coding achieves the lower bound L* = H(X) for any distribution.

## Min-Heap Invariant
- Parent.freq ≤ left_child.freq
- Parent.freq ≤ right_child.freq
- Guarantees O(log n) push and pop operations
- Python's `heapq` implements a min-heap (lowest value = highest priority)

## Why Greedy Works Here
Huffman's greedy proof (by exchange argument):
- Suppose an optimal code does NOT merge the two lowest-frequency nodes first.
- Swapping so it does can only improve or maintain the average code length.
- Therefore, always merging the two lowest is optimal.

## Prefix-Free Property
No Huffman code is a prefix of another code.
- This means decompression is unambiguous — no delimiter needed between codes.
- Achieved automatically because codes only appear at leaves of the tree.

## Complexity Summary
| Step | Time | Space |
|---|---|---|
| Frequency table | O(n) | O(k) |
| Build heap | O(k) | O(k) |
| Build tree (k-1 merges) | O(k log k) | O(k) |
| Generate codes | O(k) | O(k) |
| Compress text | O(n) | O(n) |
| Decompress | O(n) | O(n) |
| **Total** | **O(n + k log k)** | **O(n + k)** |

n = number of characters, k = number of unique characters (k ≤ 256 for ASCII)

## Compression Ratio Expected Values
| Text type | Expected savings |
|---|---|
| English text | 40–55% |
| Repeated single character | 80–90% |
| Already-random data | 0–5% |
| Source code | 35–50% |
