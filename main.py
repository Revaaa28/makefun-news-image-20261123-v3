"""Entry program for make.fun news-image-20261123, v3 (stdlib only).

The entry is the committed entry.png beside this file. Running the program
copies that image, byte for byte, into the output directory —
MAKEFUN_OUTPUT_DIR when set, /output otherwise:

    MAKEFUN_OUTPUT_DIR=out python3 main.py

The environment supplies a directory name and nothing else; the value is
read as data and never executed. The copy is verified against the source
before the program reports success, so two runs always write identical
bytes.
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGE = os.path.join(ROOT, "entry.png")


def run() -> int:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(IMAGE, dest)
    with open(IMAGE, "rb") as fh:
        want = fh.read()
    with open(dest, "rb") as fh:
        got = fh.read()
    if got != want:
        raise IOError("output entry.png does not match the committed image")
    return 0


if __name__ == "__main__":
    sys.exit(run())
