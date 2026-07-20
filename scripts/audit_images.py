#!/usr/bin/env python3
"""Walk images/players, print each file's pixel dimensions, and flag anything
under the 400px-short-side threshold as poor quality. Uses macOS `sips` (no
Pillow dependency) to read real dimensions rather than trusting file size.

Usage: python3 scripts/audit_images.py [image_dir]
"""
import os
import subprocess
import sys

THRESHOLD = 400


def get_dimensions(path):
    out = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
        capture_output=True, text=True
    ).stdout
    width = height = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("pixelWidth:"):
            width = int(line.split(":")[1].strip())
        elif line.startswith("pixelHeight:"):
            height = int(line.split(":")[1].strip())
    return width, height


def main():
    image_dir = sys.argv[1] if len(sys.argv) > 1 else "images/players"
    if not os.path.isdir(image_dir):
        print(f"No such directory: {image_dir}")
        sys.exit(1)

    results = []
    for fname in sorted(os.listdir(image_dir)):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(image_dir, fname)
        width, height = get_dimensions(path)
        if width is None or height is None:
            print(f"UNREADABLE  {fname}")
            continue
        short_side = min(width, height)
        quality = "poor" if short_side < THRESHOLD else "good"
        results.append((fname, width, height, quality))
        flag = "  <-- POOR" if quality == "poor" else ""
        print(f"{quality.upper():5s} {fname:40s} {width}x{height}{flag}")

    poor = [r for r in results if r[3] == "poor"]
    print(f"\n{len(results)} images checked, {len(poor)} below {THRESHOLD}px threshold")


if __name__ == "__main__":
    main()
