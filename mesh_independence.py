"""
mesh_independence.py
--------------------
A grid convergence check. Any CFD result is only credible once you have shown
that refining the mesh further stops changing the answer, and this is the
single most common question an examiner will ask about a Fluent project.

Method
------
Run the same case (fix the AOA, typically 4 or 6 degrees) at three or more
element sizes, record the resulting Cl and Cd, and list them here. The script
reports the percentage change between successive meshes. Once the change drops
below about 1 percent, the solution is grid independent and you can use the
coarser of the two meshes for the full AOA sweep to save time.

Edit the MESHES list below with your own numbers, then run:

    python scripts/mesh_independence.py
"""

# (label, element size in m, cell count, Cl, Cd)
# REPLACE THESE WITH YOUR OWN RUNS. The zeros are placeholders.
MESHES = [
    ("Coarse",  0.100, 0, 0.0, 0.0),
    ("Medium",  0.050, 0, 0.0, 0.0),
    ("Fine",    0.025, 0, 0.0, 0.0),
    ("Finest",  0.0125, 0, 0.0, 0.0),
]

THRESHOLD = 1.0  # percent change below which we call the mesh converged


def pct_change(new, old):
    if old == 0:
        return float("nan")
    return abs(new - old) / abs(old) * 100.0


def main():
    print("=" * 72)
    print("MESH INDEPENDENCE STUDY")
    print("=" * 72)
    header = f"{'Mesh':<10}{'Elem size':>11}{'Cells':>10}{'CL':>10}{'CD':>10}{'dCL %':>10}{'dCD %':>10}"
    print(header)
    print("-" * 72)

    converged_at = None
    for i, (label, size, cells, cl, cd) in enumerate(MESHES):
        if i == 0:
            dcl = dcd = float("nan")
        else:
            dcl = pct_change(cl, MESHES[i - 1][3])
            dcd = pct_change(cd, MESHES[i - 1][4])
            if dcl == dcl and dcd == dcd and dcl < THRESHOLD and dcd < THRESHOLD:
                converged_at = converged_at or label

        dcl_s = "-" if dcl != dcl else f"{dcl:.2f}"
        dcd_s = "-" if dcd != dcd else f"{dcd:.2f}"
        print(f"{label:<10}{size:>11.4f}{cells:>10d}{cl:>10.4f}{cd:>10.5f}{dcl_s:>10}{dcd_s:>10}")

    print("-" * 72)
    if converged_at:
        print(f"Grid independence reached at the {converged_at} mesh "
              f"(successive change below {THRESHOLD}%).")
        print("Use that mesh for the full angle-of-attack sweep.")
    else:
        print("No converged level found yet. Either the placeholder values are")
        print("still in place, or the mesh needs further refinement.")
    print("=" * 72)


if __name__ == "__main__":
    main()
