"""
format_for_ansys.py
-------------------
Converts a 2-column airfoil coordinate file (x, y) into the 5-column,
tab-delimited text file that ANSYS DesignModeler expects under
    Concept > 3D Curve > Coordinates File.

DesignModeler coordinate file format, one point per line:

    <group>  <point number>  <X>  <Y>  <Z>

Rules this script follows:
  * group  = 1 for every point (a single curve).
  * point number increments 1, 2, 3, ... down the file.
  * the final line repeats the first point with point number 0, which tells
    DesignModeler to close the curve back onto its start. An unclosed curve
    cannot be turned into a surface and the Boolean subtract will fail.
  * Z = 0 for every point, because this is a 2D analysis.

This replaces the manual Excel step (blank columns A/B, fill with 1s and point
numbers, save as tab-delimited .txt) and removes the usual source of errors.

Usage
-----
    python scripts/format_for_ansys.py data/raw/naca4412.csv
    python scripts/format_for_ansys.py data/raw/naca4412.csv --scale 0.001
    python scripts/format_for_ansys.py airfoiltools_download.dat --out fluent/airfoil.txt

Note on units: DesignModeler reads the numbers in whatever unit system the
sketch is set to. If you set DesignModeler units to mm, use --scale 1 with
mm coordinates. If you work in metres, use --scale 0.001.
"""

import argparse
import csv
import os


def read_points(path):
    """Read (x, y) pairs from a CSV, DAT or TXT file, skipping header/label lines."""
    points = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.replace(",", " ").split()
            if len(parts) < 2:
                continue
            try:
                x, y = float(parts[0]), float(parts[1])
            except ValueError:
                # Header row, or the airfoil name line that airfoiltools.com
                # puts at the top of a .dat file. Skip it.
                continue
            # airfoiltools .dat files sometimes carry a "counts" line such as
            # "61. 61." which is not geometry.
            if abs(x) > 1e4 or abs(y) > 1e4:
                continue
            points.append((x, y))
    if len(points) < 10:
        raise ValueError(f"Only {len(points)} usable points found in {path}")
    return points


def write_ansys_file(points, out_path, scale=1.0, close_curve=True):
    with open(out_path, "w") as f:
        for i, (x, y) in enumerate(points, start=1):
            f.write(f"1\t{i}\t{x * scale:.6f}\t{y * scale:.6f}\t0\n")
        if close_curve:
            x0, y0 = points[0]
            f.write(f"1\t0\t{x0 * scale:.6f}\t{y0 * scale:.6f}\t0\n")
    return len(points)


def main():
    ap = argparse.ArgumentParser(description="Format airfoil coordinates for ANSYS DesignModeler.")
    ap.add_argument("input", help="Input coordinate file (.csv, .dat or .txt)")
    ap.add_argument("--out", default=None, help="Output .txt path")
    ap.add_argument("--scale", type=float, default=1.0,
                    help="Multiply all coordinates by this factor (default: 1.0)")
    ap.add_argument("--no-close", action="store_true",
                    help="Do not append the closing point-0 line")
    args = ap.parse_args()

    points = read_points(args.input)

    out = args.out or os.path.join(
        "fluent", os.path.splitext(os.path.basename(args.input))[0] + "_ansys.txt"
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)

    n = write_ansys_file(points, out, args.scale, not args.no_close)

    xs = [p[0] * args.scale for p in points]
    ys = [p[1] * args.scale for p in points]
    print(f"Wrote {n} points -> {out}")
    print(f"  chord extent : {min(xs):.3f} to {max(xs):.3f}")
    print(f"  thickness    : {min(ys):.3f} to {max(ys):.3f}")
    print("Import in DesignModeler via Concept > 3D Curve > Coordinates File.")


if __name__ == "__main__":
    main()
