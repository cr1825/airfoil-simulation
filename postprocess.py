"""
postprocess.py
--------------
Reads the angle-of-attack parametric table exported from the ANSYS Workbench
Parameter Set and produces the plots that go into the report:

    1. Cl vs AOA, with the thin-airfoil-theory slope overlaid
    2. Cd vs AOA
    3. Lift-to-drag ratio (Cl/Cd) vs AOA
    4. Drag polar (Cl vs Cd)
    5. Cm vs AOA

It also prints a summary table: maximum Cl, the AOA at which the best L/D
occurs, and the first sign of stall (the AOA where Cl stops increasing).

Input format
------------
A CSV with the columns: aoa_deg, cl, cd, cm
Lines beginning with '#' are treated as comments and ignored, so you can keep
notes about the run conditions at the top of the file.

Export it from Workbench by right-clicking the Parameter Set table and
choosing "Export Table Data", then rename the columns to match.

Usage
-----
    python scripts/postprocess.py
    python scripts/postprocess.py --input data/results/aoa_results.csv --outdir results/plots
"""

import argparse
import csv
import math
import os

import matplotlib
matplotlib.use("Agg")           # no display needed; write straight to PNG
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# Flow conditions. Keep these in sync with the Fluent setup, they are only
# used for the Reynolds number printed in the summary.
# ----------------------------------------------------------------------
VELOCITY = 1.5          # m/s, inlet velocity magnitude
CHORD = 0.1             # m, airfoil chord
RHO = 1.225             # kg/m^3, air at sea level
MU = 1.7894e-5          # Pa.s, dynamic viscosity of air


def read_results(path):
    rows = []
    with open(path, "r") as f:
        lines = [ln for ln in f if not ln.lstrip().startswith("#") and ln.strip()]
    reader = csv.DictReader(lines)
    for r in reader:
        rows.append({
            "aoa": float(r["aoa_deg"]),
            "cl": float(r["cl"]),
            "cd": float(r["cd"]),
            "cm": float(r.get("cm", 0.0) or 0.0),
        })
    rows.sort(key=lambda d: d["aoa"])
    if not rows:
        raise ValueError(f"No data rows read from {path}")
    return rows


def reynolds_number():
    return RHO * VELOCITY * CHORD / MU


def save(fig, outdir, name):
    path = os.path.join(outdir, name)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved {path}")


def plot_all(rows, outdir):
    os.makedirs(outdir, exist_ok=True)
    aoa = [r["aoa"] for r in rows]
    cl = [r["cl"] for r in rows]
    cd = [r["cd"] for r in rows]
    cm = [r["cm"] for r in rows]
    ld = [c / d if d != 0 else 0.0 for c, d in zip(cl, cd)]

    # 1. Lift coefficient, against the 2*pi*alpha thin-airfoil result
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(aoa, cl, "o-", color="#1f77b4", label="CFD (Fluent, k-omega)")
    theory = [2 * math.pi * math.radians(a) for a in aoa]
    ax.plot(aoa, theory, "--", color="grey", label=r"Thin airfoil theory ($2\pi\alpha$)")
    ax.set_xlabel("Angle of attack (deg)")
    ax.set_ylabel(r"Lift coefficient $C_L$")
    ax.set_title("Lift coefficient vs angle of attack")
    ax.grid(alpha=0.3)
    ax.legend()
    save(fig, outdir, "cl_vs_aoa.png")

    # 2. Drag coefficient
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(aoa, cd, "s-", color="#d62728")
    ax.set_xlabel("Angle of attack (deg)")
    ax.set_ylabel(r"Drag coefficient $C_D$")
    ax.set_title("Drag coefficient vs angle of attack")
    ax.grid(alpha=0.3)
    save(fig, outdir, "cd_vs_aoa.png")

    # 3. Aerodynamic efficiency
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(aoa, ld, "^-", color="#2ca02c")
    best = max(range(len(ld)), key=lambda i: ld[i])
    ax.axvline(aoa[best], color="grey", ls=":", lw=1)
    ax.annotate(f"best L/D = {ld[best]:.1f}\nat {aoa[best]:.0f} deg",
                xy=(aoa[best], ld[best]), xytext=(8, -28),
                textcoords="offset points", fontsize=9)
    ax.set_xlabel("Angle of attack (deg)")
    ax.set_ylabel(r"$C_L/C_D$")
    ax.set_title("Aerodynamic efficiency vs angle of attack")
    ax.grid(alpha=0.3)
    save(fig, outdir, "ld_vs_aoa.png")

    # 4. Drag polar
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(cd, cl, "o-", color="#9467bd")
    for a, x, y in zip(aoa, cd, cl):
        ax.annotate(f"{a:.0f}", (x, y), textcoords="offset points",
                    xytext=(5, 4), fontsize=8, color="grey")
    ax.set_xlabel(r"$C_D$")
    ax.set_ylabel(r"$C_L$")
    ax.set_title("Drag polar (labels = AOA in degrees)")
    ax.grid(alpha=0.3)
    save(fig, outdir, "drag_polar.png")

    # 5. Moment coefficient
    if any(c != 0 for c in cm):
        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.plot(aoa, cm, "d-", color="#ff7f0e")
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_xlabel("Angle of attack (deg)")
        ax.set_ylabel(r"Moment coefficient $C_M$")
        ax.set_title("Pitching moment vs angle of attack")
        ax.grid(alpha=0.3)
        save(fig, outdir, "cm_vs_aoa.png")

    return aoa, cl, cd, ld


def summarise(aoa, cl, cd, ld):
    print("\n" + "=" * 58)
    print("SUMMARY")
    print("=" * 58)
    print(f"Reynolds number (chord-based) : {reynolds_number():,.0f}")
    print(f"Inlet velocity                : {VELOCITY} m/s")
    print(f"Chord length                  : {CHORD * 1000:.0f} mm")
    print("-" * 58)
    print(f"{'AOA (deg)':>10} {'CL':>10} {'CD':>10} {'CL/CD':>10}")
    for a, l, d, e in zip(aoa, cl, cd, ld):
        print(f"{a:>10.1f} {l:>10.4f} {d:>10.5f} {e:>10.2f}")
    print("-" * 58)

    i_max_cl = max(range(len(cl)), key=lambda i: cl[i])
    i_best_ld = max(range(len(ld)), key=lambda i: ld[i])
    print(f"Maximum CL      : {cl[i_max_cl]:.4f} at {aoa[i_max_cl]:.1f} deg")
    print(f"Best CL/CD      : {ld[i_best_ld]:.2f} at {aoa[i_best_ld]:.1f} deg")
    print(f"Minimum CD      : {min(cd):.5f}")

    # Lift-curve slope from the first two points, in per-radian terms
    if len(aoa) > 1 and aoa[1] != aoa[0]:
        slope = (cl[1] - cl[0]) / math.radians(aoa[1] - aoa[0])
        print(f"Lift-curve slope: {slope:.3f} per rad "
              f"(thin airfoil theory: {2 * math.pi:.3f})")

    if i_max_cl < len(cl) - 1:
        print(f"Stall indicated : CL peaks at {aoa[i_max_cl]:.1f} deg "
              f"and falls beyond it")
    else:
        print("Stall indicated : not captured; extend the AOA sweep further")
    print("=" * 58)


def main():
    ap = argparse.ArgumentParser(description="Plot CFD angle-of-attack sweep results.")
    ap.add_argument("--input", default=os.path.join("data", "results", "aoa_results.csv"))
    ap.add_argument("--outdir", default=os.path.join("results", "plots"))
    args = ap.parse_args()

    rows = read_results(args.input)
    print(f"Read {len(rows)} design points from {args.input}\nGenerating plots:")
    aoa, cl, cd, ld = plot_all(rows, args.outdir)
    summarise(aoa, cl, cd, ld)


if __name__ == "__main__":
    main()
