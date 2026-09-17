"""
generate_airfoil.py
-------------------
Generates NACA 4-digit series airfoil coordinates analytically and writes them
to CSV. Use this instead of manually downloading from airfoiltools.com when you
want a reproducible, version-controlled geometry.

The profile is built from the standard NACA 4-digit definitions:

    Thickness distribution (symmetric part):
        yt = 5*t*(0.2969*sqrt(x) - 0.1260*x - 0.3516*x^2
                  + 0.2843*x^3 - 0.1015*x^4)

    Mean camber line:
        yc =  m/p^2     * (2*p*x - x^2)              for 0 <= x <= p
        yc =  m/(1-p)^2 * ((1-2p) + 2*p*x - x^2)     for p <  x <= 1

Points are distributed with cosine spacing so the leading edge (where curvature
is highest) is resolved far better than with uniform spacing.

Usage
-----
    python scripts/generate_airfoil.py --naca 4412 --points 160 --chord 100
    python scripts/generate_airfoil.py --naca 2412 --out data/raw/naca2412.csv
"""

import argparse
import csv
import math
import os


def naca4_thickness(x, t):
    """Half-thickness of a NACA 4-digit section at chordwise station x (0..1)."""
    return 5.0 * t * (
        0.2969 * math.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x ** 2
        + 0.2843 * x ** 3
        - 0.1015 * x ** 4
    )


def naca4_camber(x, m, p):
    """Return (camber ordinate yc, camber slope dyc/dx) at station x."""
    if m == 0.0 or p == 0.0:
        return 0.0, 0.0
    if x <= p:
        yc = (m / p ** 2) * (2 * p * x - x ** 2)
        dyc = (2 * m / p ** 2) * (p - x)
    else:
        yc = (m / (1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x - x ** 2)
        dyc = (2 * m / (1 - p) ** 2) * (p - x)
    return yc, dyc


def generate(naca="4412", n_points=160, chord=100.0, closed_te=True):
    """
    Build airfoil coordinates in Selig order: trailing edge -> upper surface ->
    leading edge -> lower surface -> trailing edge.

    Returns a list of (x, y) tuples scaled to the requested chord length in mm.
    """
    if len(naca) != 4 or not naca.isdigit():
        raise ValueError("NACA code must be exactly 4 digits, e.g. 4412")

    m = int(naca[0]) / 100.0        # max camber, fraction of chord
    p = int(naca[1]) / 10.0         # location of max camber
    t = int(naca[2:]) / 100.0       # max thickness, fraction of chord

    # Cosine spacing clusters points near the leading and trailing edges.
    beta = [math.pi * i / (n_points - 1) for i in range(n_points)]
    xs = [(1 - math.cos(b)) / 2.0 for b in beta]

    upper, lower = [], []
    for x in xs:
        yt = naca4_thickness(x, t)
        yc, dyc = naca4_camber(x, m, p)
        theta = math.atan(dyc)
        upper.append((x - yt * math.sin(theta), yc + yt * math.cos(theta)))
        lower.append((x + yt * math.sin(theta), yc - yt * math.cos(theta)))

    if closed_te:
        # The analytical polynomial leaves a small gap at the trailing edge.
        # A gap breaks the Boolean subtract in DesignModeler, so force closure.
        upper[-1] = (1.0, 0.0)
        lower[-1] = (1.0, 0.0)

    # Selig order, dropping the duplicated leading-edge and trailing-edge points
    coords = list(reversed(upper)) + lower[1:-1]

    return [(x * chord, y * chord) for x, y in coords]


def main():
    ap = argparse.ArgumentParser(description="Generate NACA 4-digit airfoil coordinates.")
    ap.add_argument("--naca", default="4412", help="4-digit NACA code (default: 4412)")
    ap.add_argument("--points", type=int, default=160,
                    help="Number of points per surface (default: 160)")
    ap.add_argument("--chord", type=float, default=100.0,
                    help="Chord length in mm (default: 100)")
    ap.add_argument("--out", default=None, help="Output CSV path")
    args = ap.parse_args()

    coords = generate(args.naca, args.points, args.chord)

    out = args.out or os.path.join("data", "raw", f"naca{args.naca}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x_mm", "y_mm"])
        w.writerows([[f"{x:.6f}", f"{y:.6f}"] for x, y in coords])

    print(f"NACA {args.naca}: wrote {len(coords)} points to {out}")
    print(f"Chord = {args.chord} mm | max thickness = {int(args.naca[2:])}% chord")


if __name__ == "__main__":
    main()
