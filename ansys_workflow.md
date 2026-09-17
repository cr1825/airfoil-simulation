# ANSYS Workflow

Full reproduction steps for the case, from an empty Workbench project to the
angle-of-attack parametric table. Follow it top to bottom.

---

## Step 1 — Geometry

1. Open ANSYS Workbench and drag a **Fluid Flow (Fluent)** analysis system into
   the project schematic.
2. Right-click **Geometry → New DesignModeler Geometry**. Set units to **mm**.
3. Generate the airfoil coordinates:

   ```bash
   python scripts/generate_airfoil.py --naca 4412 --chord 100 --points 160
   python scripts/format_for_ansys.py data/raw/naca4412.csv --out fluent/naca4412_ansys.txt
   ```

   (Alternatively download the coordinate file from airfoiltools.com and pass
   the `.dat` straight into `format_for_ansys.py` — it handles that format too.)
4. In DesignModeler: **Concept → 3D Curve → Coordinates File**, browse to
   `fluent/naca4412_ansys.txt`, then **Generate**.

> The coordinate file must have five tab-separated columns — group, point
> number, X, Y, Z — and the last line must repeat the first point with point
> number `0`. If the curve does not close, the Boolean subtract in Step 2 fails.

---

## Step 2 — Fluid domain

1. Select the **XY plane** and start a new sketch.
2. Draw a rectangle around the airfoil:

   | Dimension | Value | Meaning |
   |---|---|---|
   | H1 | 1500 mm | total domain length (15 chords) |
   | V2 | 1000 mm | total domain height (10 chords) |
   | H3 | 500 mm | upstream distance ahead of the airfoil (5 chords) |
   | V6 | 500 mm | distance to the far-field top/bottom |

   The domain has to be large enough that the outer boundaries do not
   artificially constrain the flow. Roughly 5 chords upstream and 10 chords
   downstream is the accepted minimum for subsonic external aerodynamics.

3. **Concept → Surface from Sketches** → select the rectangle → Apply → Generate.
4. **Concept → Surface from Edges** → select the airfoil curve → Apply → Generate.
5. **Create → Boolean → Subtract**. Target body = rectangular surface,
   Tool body = airfoil surface → Generate.
6. Set the remaining surface body type to **Fluid** and rename it
   `Fluid Domain`. Close DesignModeler.

---

## Step 3 — Meshing

1. Right-click **Mesh → Edit**.
2. **Method** — right-click Mesh → Insert → Method, select the fluid domain.
3. **Sizing** — right-click Mesh → Insert → Sizing, select the fluid domain,
   element size `0.05 m`.
4. **Inflation** — right-click Mesh → Insert → Inflation. Geometry = fluid
   domain, Boundary = airfoil edge, Number of layers = **10**.

   The inflation layer is what resolves the boundary layer on the airfoil
   surface. Without it the k-omega model has nothing to work with near the wall
   and the drag coefficient will be badly under-predicted.

5. **Generate Mesh**.
6. Named selections (right-click the edge → Create Named Selection):

   | Edge | Name |
   |---|---|
   | Upstream (left) | `inlet` |
   | Downstream (right) | `outlet` |
   | Top and bottom (Ctrl-select both) | `walls` |
   | Airfoil profile | `airfoil` |

   The names must match exactly — Fluent uses them to assign boundary
   conditions, and the journal file in `fluent/setup.jou` refers to them.

7. Right-click **Mesh → Update**, then close the meshing window.
8. Run a grid convergence check before trusting any result — repeat the case at
   several element sizes and record them in `scripts/mesh_independence.py`.

---

## Step 4 — Fluent setup

1. Right-click **Setup → Edit**, tick **Double Precision**, launch.
2. **Models → Viscous** → **k-omega (2 eqn), Standard**.
3. **Boundary conditions → inlet** → velocity magnitude `1.5 m/s`.
4. **Reference Values** → set the area to the measured airfoil surface area
   (approximately `1000e-6 m²` for a 100 mm chord; read the exact value from the
   geometry properties). Every force coefficient is divided by this number, so
   an incorrect reference area scales all your results.
5. **Report Definitions → New → Force Report**, one each for:
   - **Lift (C_L)** — force vector `(0, 1)` at AOA = 0
   - **Drag (C_D)** — force vector `(1, 0)` at AOA = 0
   - **Moment (C_M)** — about the quarter-chord point

   For each, tick **Report File**, **Report Plot** and **Print to Console**.

   At a non-zero AOA the lift and drag directions rotate with the airfoil:
   lift direction = `(-sin α, cos α)`, drag direction = `(cos α, sin α)`.
   Because this project rotates the *geometry* rather than the inlet flow, the
   vectors stay at `(0,1)` and `(1,0)` — but say so explicitly in your report,
   as it is a standard examiner question.

6. **Residual Monitors** → absolute convergence criteria `1e-6` for all
   equations.
7. **Hybrid Initialization → Initialize**.
8. **Run Calculation** → 500 iterations → **Calculate**.

---

## Step 5 — Post-processing

Open **Results** from the Workbench panel.

| Output | How |
|---|---|
| Pressure contour | Insert → Contour, location `symmetry 1`, variable `Pressure` |
| Velocity contour | Same, variable `Velocity` |
| Streamlines | Insert → Streamline, start from `inlet`, direction Forward and Backward, points = 250 |

Save each image into `docs/images/` and reference it from the README.

---

## Step 6 — Angle-of-attack parametric study

1. Re-open DesignModeler and **delete the Boolean operation**.
2. **Create → Body Transformation → Rotate**. Select the airfoil, axis = XY
   plane, angle = `2°`.
3. Click the small checkbox next to the angle field to promote it to a
   parameter, and rename it **AOA**.
4. Re-apply the Boolean subtract, close DesignModeler.
5. Right-click **Mesh → Update**.
6. In Fluent, for each of the C_L, C_D and C_M report definitions, tick
   **Create Output Parameter**.
7. Update the reference area, re-initialise, set 300 iterations, test-run, close.
8. Double-click **Parameter Set** in the Workbench schematic.
9. Enter the angles under the **P1 (AOA)** input column: `0, 2, 4, 6, 8, 10`.
10. Tick **Retain** on all design points so the solved data is kept.
11. Select rows DP0–DP5, right-click → **Update Selected Design Points**.
12. When it finishes, right-click the table → **Export Table Data** and paste the
    columns into `data/results/aoa_results.csv`.
13. Generate the plots:

    ```bash
    python scripts/postprocess.py
    ```

To view the contours for one specific angle, right-click that design point and
**Set as Current**, then reopen Results.

---

## Common problems

| Symptom | Cause | Fix |
|---|---|---|
| Boolean subtract fails | Airfoil curve not closed | Check the final `0` point line in the coordinate file |
| Residuals stall around 1e-3 | Mesh too coarse, or poor cells at the trailing edge | Refine sizing, add inflation layers |
| C_D an order of magnitude off | Wrong reference area | Re-read the surface area from the geometry |
| Solution diverges | Initial velocity too high for the mesh | Lower under-relaxation factors, use first-order upwind initially |
| Lift stays near zero at all AOA | Rotation did not regenerate | Confirm the Boolean was reapplied after the rotate |
