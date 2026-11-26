#!/usr/bin/env python3
"""
main.py — Huffman File Compression System v1.0
============================================
CLI interface for Huffman-based file compression.

Usage:
  python main.py compress   <input_file>   [--out compressed_files/out.huff]
  python main.py decompress <compressed>   [--out decompressed_files/out.txt]
  python main.py analyze    <input_file>
  python main.py demo


import argparse
import os
import sys
import time

# Add src/ to path so we can import huffman
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from huffman import (
    frequency_table,
    build_huffman_tree,
    generate_codes,
    compress,
    decompress,
    save_compressed,
    load_compressed,
    compression_report,
)


# ─────────────────────────────────────────────
# Pretty Printing Helpers
# ─────────────────────────────────────────────

def banner():
    print("""
╔══════════════════════════════════════════════════════╗
║      Dynamic File Compression Utility v1.0           ║
║      Huffman Coding | DSA Project | Python           ║
╚══════════════════════════════════════════════════════╝
""")


def print_freq_table(freq_dict: dict, top_n: int = 20):
    print(f"\n{'─'*50}")
    print(f"  CHARACTER FREQUENCY TABLE  (top {top_n})")
    print(f"{'─'*50}")
    print(f"  {'Char':<12} {'Freq':>8}  {'Bar'}")
    print(f"{'─'*50}")
    total = sum(freq_dict.values())
    for i, (char, freq) in enumerate(freq_dict.items()):
        if i >= top_n:
            break
        display = repr(char) if char in ('\n', '\t', ' ') else char
        bar_len = int((freq / total) * 30)
        bar = '█' * bar_len
        print(f"  {display:<12} {freq:>8}  {bar}")
    if len(freq_dict) > top_n:
        print(f"  ... and {len(freq_dict) - top_n} more unique chars")
    print(f"{'─'*50}")


def print_huffman_codes(codes: dict, freq_dict: dict):
    print(f"\n{'─'*60}")
    print("  HUFFMAN CODE TABLE")
    print(f"{'─'*60}")
    print(f"  {'Char':<10} {'Freq':>8}  {'Code':<30} {'Bits':>5}")
    print(f"{'─'*60}")
    # Sort by code length, then by character
    sorted_codes = sorted(codes.items(), key=lambda x: (len(x[1]), x[0]))
    for char, code in sorted_codes:
        display = repr(char) if char in ('\n', '\t', ' ') else char
        freq = freq_dict.get(char, 0)
        print(f"  {display:<10} {freq:>8}  {code:<30} {len(code):>5}")
    print(f"{'─'*60}")


def print_report(report: dict):
    savings_bar = '█' * int(report['space_savings_pct'] / 5)
    print(f"""
╔══════════════════════════════════════════════════╗
║           COMPRESSION REPORT                     ║
╠══════════════════════════════════════════════════╣
║  Original characters  : {report['original_chars']:>10,}              ║
║  Unique characters    : {report['unique_chars']:>10}              ║
║  Original size        : {report['original_size_bits']:>10,} bits           ║
║  Original size        : {report['original_size_bytes']:>10,} bytes          ║
║  Compressed size      : {report['compressed_size_bits']:>10,} bits           ║
║  Compressed size      : {report['compressed_size_bytes']:>10,} bytes          ║
║  Compression ratio    : {report['compression_ratio']:>10.4f}              ║
║  Space saved          : {report['space_savings_pct']:>9.2f}%              ║
║  Avg code length      : {report['avg_code_length']:>10.4f} bits/char    ║
╠══════════════════════════════════════════════════╣
║  Savings: {savings_bar:<38} ║
╚══════════════════════════════════════════════════╝
""")


# ─────────────────────────────────────────────
# Core Commands
# ─────────────────────────────────────────────

def cmd_compress(input_path: str, output_path: str):
    """Read → Frequency → Huffman Tree → Codes → Compress → Save."""
    banner()
    print(f"  [1/5] Reading input file: {input_path}")

    if not os.path.exists(input_path):
        print(f"  ERROR: File not found → {input_path}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    if not text.strip():
        print("  ERROR: Input file is empty.")
        sys.exit(1)

    print(f"        {len(text):,} characters read.")

    print("  [2/5] Building frequency table...")
    freq = frequency_table(text)
    print_freq_table(freq)

    print("\n  [3/5] Building Huffman Tree (min-heap)...")
    t0 = time.perf_counter()
    root = build_huffman_tree(freq)
    t1 = time.perf_counter()
    print(f"        Tree built in {(t1-t0)*1000:.2f} ms | Unique chars: {len(freq)}")

    print("\n  [4/5] Generating Huffman codes...")
    codes = generate_codes(root)
    print_huffman_codes(codes, freq)

    print("\n  [5/5] Compressing and saving file...")
    t0 = time.perf_counter()
    compressed = compress(text, codes)
    t1 = time.perf_counter()

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    save_compressed(compressed, root, output_path)

    report = compression_report(text, compressed, codes, freq)
    print_report(report)

    print(f"  ✓ Compressed file saved → {output_path}")
    print(f"  ✓ Compression time: {(t1-t0)*1000:.2f} ms\n")

    # Save report to outputs/
    report_path = os.path.join('outputs', os.path.basename(input_path) + '_report.txt')
    os.makedirs('outputs', exist_ok=True)
    with open(report_path, 'w') as rf:
        rf.write(f"Compression Report\n{'='*40}\n")
        for k, v in report.items():
            rf.write(f"{k:<30}: {v}\n")
        rf.write(f"\nHuffman Codes:\n{'='*40}\n")
        for char, code in sorted(codes.items(), key=lambda x: len(x[1])):
            rf.write(f"  {repr(char):<12}: {code}\n")
    print(f"  ✓ Report saved → {report_path}\n")


def cmd_decompress(compressed_path: str, output_path: str):
    """Load compressed file → decompress → save text."""
    banner()
    print(f"  [1/3] Loading compressed file: {compressed_path}")

    if not os.path.exists(compressed_path):
        print(f"  ERROR: File not found → {compressed_path}")
        sys.exit(1)

    compressed_bytes, root = load_compressed(compressed_path)
    print(f"        {len(compressed_bytes):,} bytes loaded.")

    print("  [2/3] Decompressing using Huffman tree...")
    t0 = time.perf_counter()
    recovered = decompress(compressed_bytes, root)
    t1 = time.perf_counter()
    print(f"        {len(recovered):,} characters recovered in {(t1-t0)*1000:.2f} ms")

    print(f"  [3/3] Saving decompressed file → {output_path}")
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(recovered)

    print(f"  ✓ Done! Decompressed text saved → {output_path}\n")


def cmd_analyze(input_path: str):
    """Show frequency table and Huffman codes without compressing."""
    banner()
    print(f"  Analyzing: {input_path}\n")

    if not os.path.exists(input_path):
        print(f"  ERROR: File not found → {input_path}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    freq  = frequency_table(text)
    root  = build_huffman_tree(freq)
    codes = generate_codes(root)

    print_freq_table(freq, top_n=30)
    print_huffman_codes(codes, freq)

    compressed = compress(text, codes)
    report = compression_report(text, compressed, codes, freq)
    print_report(report)


def cmd_demo():
    """Run a mini end-to-end demo with a hard-coded string."""
    banner()
    demo_text = (
        "Huffman coding is a lossless data compression algorithm. "
        "The idea is to assign shorter binary codes to more frequent characters "
        "and longer codes to less frequent characters."
    )

    print("  DEMO — compressing a sample string\n")
    print(f"  Input text ({len(demo_text)} chars):")
    print(f"  {demo_text[:80]}...")

    freq  = frequency_table(demo_text)
    root  = build_huffman_tree(freq)
    codes = generate_codes(root)

    print_freq_table(freq)
    print_huffman_codes(codes, freq)

    compressed  = compress(demo_text, codes)
    decompressed = decompress(compressed, root)
    report = compression_report(demo_text, compressed, codes, freq)
    print_report(report)

    match = demo_text == decompressed
    print(f"  ✓ Decompression check: {'PASSED ✅' if match else 'FAILED ❌'}")
    print(f"  Original  : {demo_text[:60]}...")
    print(f"  Recovered : {decompressed[:60]}...\n")


# ─────────────────────────────────────────────
# Argument Parser
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog='huffman',
        description='Dynamic File Compression Utility — Huffman Coding',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # compress sub-command
    p_compress = sub.add_parser('compress', help='Compress a text file')
    p_compress.add_argument('input',  help='Path to input .txt file')
    p_compress.add_argument('--out',  default=None, help='Output .huff file path')

    # decompress sub-command
    p_decompress = sub.add_parser('decompress', help='Decompress a .huff file')
    p_decompress.add_argument('input', help='Path to .huff compressed file')
    p_decompress.add_argument('--out', default=None, help='Output .txt file path')

    # analyze sub-command
    p_analyze = sub.add_parser('analyze', help='Analyze a file without compressing')
    p_analyze.add_argument('input', help='Path to input .txt file')

    # demo sub-command
    sub.add_parser('demo', help='Run a quick demonstration')

    args = parser.parse_args()

    if args.command == 'compress':
        base = os.path.splitext(os.path.basename(args.input))[0]
        out  = args.out or os.path.join('compressed_files', base + '.huff')
        cmd_compress(args.input, out)

    elif args.command == 'decompress':
        base = os.path.splitext(os.path.basename(args.input))[0]
        out  = args.out or os.path.join('decompressed_files', base + '_recovered.txt')
        cmd_decompress(args.input, out)

    elif args.command == 'analyze':
        cmd_analyze(args.input)

    elif args.command == 'demo':
        cmd_demo()


if __name__ == '__main__':
    main()
