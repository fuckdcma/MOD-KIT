"""Check the project-specific Python interpreter without PowerShell -c quoting."""
from __future__ import annotations
import argparse
import struct
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-deps", action="store_true")
    args = parser.parse_args()

    version = sys.version_info[:2]
    bits = struct.calcsize("P") * 8
    print(f"Python: {sys.version.split()[0]} ({bits}-bit)")
    print(f"Interpreter: {sys.executable}")
    if version != (3, 12) or bits != 64:
        print("ERROR: This project requires Python 3.12, 64-bit.", file=sys.stderr)
        return 1

    if args.check_deps:
        try:
            import UnityPy  # noqa: F401
            import lz4.frame  # noqa: F401
        except ImportError as exc:
            print(f"ERROR: Missing package: {exc}", file=sys.stderr)
            return 2
        print("UnityPy import: OK")
        print("lz4 import: OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
