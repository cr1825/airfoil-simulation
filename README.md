# CFD Analysis of a NACA 4412 Airfoil — Angle of Attack Parametric Study

A two-dimensional computational fluid dynamics study of flow over a NACA 4412
airfoil, carried out in ANSYS Fluent. The project determines how the lift, drag
and pitching-moment coefficients vary with angle of attack, and identifies the
angle of best aerodynamic efficiency.

The repository contains the complete reproducible workflow: Python tools that
generate and format the airfoil geometry, a Fluent journal that fixes the solver
settings, documented meshing and setup procedures, and post-processing scripts
that turn the parametric results into report-ready plots.

!airfoil_naca4424.png

---

## Objectives

1. Build a validated 2D CFD model of an external airfoil flow in ANSYS Fluent.
2. Compute C_L, C_D and C_M across a sweep of angles of attack (0° to 10°).
3. Establish grid independence so the results do not depend on mesh density.
4. Compare the computed lift-curve slope against thin airfoil theory (2πα).
5. Identify the angle of attack giving the maximum lift-to-drag ratio.
6. Visualise the pressure field, velocity field and streamline pattern.

---

## Case setup

| Parameter | Value |
|---|---|
| Airfoil section | NACA 4412 |
| Chord length | 100 mm |
| Domain | 1500 × 1000 mm (15c × 10c) |
| Upstream distance | 500 mm (5c) |
| Inlet velocity | 1.5 m/s |
| Reynolds number | ≈ 1.03 × 10⁴ |
| Fluid | Air (ρ = 1.225 kg/m³, μ = 1.7894 × 10⁻⁵ Pa·s) |
| Turbulence model | Standard k-ω |
| Solver | Pressure-based, steady, 2D, double precision |
| Convergence criterion | 1 × 10⁻⁶ on all residuals |
| Inflation layers | 10 on the airfoil surface |
| Angles of attack | 0°, 2°, 4°, 6°, 8°, 10° |

The k-ω model was chosen over k-ε because it integrates through the viscous
sublayer to the wall rather than relying on wall functions, which makes it
substantially better at predicting boundary-layer separation — the physics that
governs drag and the shape of the lift curve near stall. The reasoning is set
out in full in [`docs/methodology.md`](docs/methodology.md).

---

## Repository layout

```
naca-airfoil-cfd-ansys/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
│
├── scripts/
│   ├── generate_airfoil.py      # NACA 4-digit coordinate generator
│   ├── format_for_ansys.py      # Converts coordinates to DesignModeler format
│   ├── postprocess.py           # Plots C_L, C_D, C_L/C_D, drag polar, C_M
│   └── mesh_independence.py     # Grid convergence check
│
├── fluent/
│   ├── setup.jou                # Fluent TUI journal, full solver setup
│   └── naca4412_ansys.txt       # Generated coordinate file for DesignModeler
│
├── data/
│   ├── raw/                     # Airfoil coordinates
│   └── results/
│       └── aoa_results.csv      # Parametric table exported from Workbench
│
├── docs/
│   ├── methodology.md           # Governing equations, turbulence model, theory
│   ├── ansys_workflow.md        # Full step-by-step reproduction guide
│   └── images/                  # Contours, mesh and geometry screenshots
│
└── results/
    └── plots/                   # Generated plots
```

---

## Quick start

```bash
git clone https://github.com/<your-username>/naca-airfoil-cfd-ansys.git
cd naca-airfoil-cfd-ansys
pip install -r requirements.txt

# 1. Generate the airfoil geometry
python scripts/generate_airfoil.py --naca 4412 --chord 100 --points 160

# 2. Convert it into an ANSYS DesignModeler coordinate file
python scripts/format_for_ansys.py data/raw/naca4412.csv --out fluent/naca4412_ansys.txt

# 3. Run the ANSYS workflow (see docs/ansys_workflow.md)

# 4. Export the design-point table into data/results/aoa_results.csv, then
python scripts/postprocess.py
```

Steps 1, 2 and 4 run on any machine with Python. Step 3 requires an ANSYS
licence (the free Student edition is sufficient for this mesh size).

---

## Geometry generation

The airfoil is built analytically from the NACA 4-digit definitions rather than
downloaded, which makes the geometry reproducible and version-controllable.

The thickness distribution is

```
yt = 5t(0.2969√x − 0.1260x − 0.3516x² + 0.2843x³ − 0.1015x⁴)
```

and the camber line is a two-part parabola meeting at the point of maximum
camber. Points are placed using cosine spacing so that the leading edge, where
curvature is highest, is far better resolved than uniform spacing would allow.
The trailing edge is explicitly closed, since the small gap left by the
analytical polynomial otherwise causes the Boolean subtract in DesignModeler to
fail.

`format_for_ansys.py` then writes the five-column tab-delimited file that
DesignModeler's **Concept → 3D Curve** importer expects, replacing the manual
Excel column-filling step and the errors that come with it.

---

## Method summary

1. **Geometry** — import the airfoil curve, sketch the rectangular far-field,
   create both surfaces and Boolean-subtract the airfoil from the domain.
2. **Mesh** — face sizing at 0.05 m with a 10-layer inflation on the airfoil
   surface; named selections for `inlet`, `outlet`, `walls`, `airfoil`.
3. **Setup** — k-ω turbulence, 1.5 m/s velocity inlet, zero-gauge pressure
   outlet, no-slip airfoil wall, force report definitions for C_L, C_D and C_M.
4. **Solve** — hybrid initialisation, 500 iterations, residuals to 1 × 10⁻⁶.
5. **Parameterise** — promote the airfoil rotation angle to the input parameter
   AOA, promote the three coefficients to output parameters, then solve all
   design points from the Workbench Parameter Set.
6. **Post-process** — contours and streamlines in CFD-Post, coefficient plots
   from `scripts/postprocess.py`.

Full detail, including the dimensions and every menu path, is in
[`docs/ansys_workflow.md`](docs/ansys_workflow.md).

---

## Results

> Replace the placeholder table and images below with your own output once the
> design points have solved.

| AOA (°) | C_L | C_D | C_L/C_D | C_M |
|---|---|---|---|---|
| 0 | — | — | — | — |
| 2 | — | — | — | — |
| 4 | — | — | — | — |
| 6 | — | — | — | — |
| 8 | — | — | — | — |
| 10 | — | — | — | — |

| Lift coefficient | Drag coefficient |
|---|---|
| ![CL vs AOA](results/plots/cl_vs_aoa.png) | ![CD vs AOA](results/plots/cd_vs_aoa.png) |

| Efficiency | Drag polar |
|---|---|
| ![L/D](results/plots/ld_vs_aoa.png) | ![Drag polar](results/plots/drag_polar.png) |

### Flow visualisation

| Pressure contour | Velocity contour | Streamlines |
|---|---|---|
| ![Pressure](docs/images/pressure_contour.png) | ![Velocity](docs/images/velocity_contour.png) | ![Streamlines](docs/images/streamlines.png) |

---

## Verification

A converged solution on a poor mesh is still a wrong answer, so the following
checks are part of the study:

- **Iterative convergence** — all residuals below 1 × 10⁻⁶, and the force
  coefficients flat over the final iterations.
- **Grid independence** — the case is repeated at successively finer element
  sizes until C_L and C_D change by less than 1 %; recorded in
  `scripts/mesh_independence.py`.
- **Theoretical comparison** — the computed lift-curve slope is compared against
  the thin-airfoil value of 2π per radian, which the viscous CFD result is
  expected to fall slightly below.

---

## Limitations

The model is two-dimensional, so there are no wingtip vortices and no induced
drag. Steady RANS cannot represent unsteady post-stall behaviour such as vortex
shedding. The flow is assumed fully turbulent, with no transition model, which
is a real limitation at Re ≈ 10⁴ where laminar separation bubbles are common —
so the results should be read as a qualitative trend study rather than as
quantitative agreement with high-Reynolds-number wind tunnel data.

---

## Tools used

- ANSYS Workbench — project management and parametric design points
- ANSYS DesignModeler — geometry creation and Boolean operations
- ANSYS Meshing — mesh generation, inflation layers, named selections
- ANSYS Fluent — pressure-based RANS solver
- ANSYS CFD-Post — contours and streamlines
- Python 3.8+ with matplotlib — geometry generation and post-processing

---

## References

1. Anderson, J.D., *Fundamentals of Aerodynamics*, 6th ed., McGraw-Hill.
2. Abbott, I.H. and von Doenhoff, A.E., *Theory of Wing Sections*, Dover.
3. Wilcox, D.C., *Turbulence Modeling for CFD*, 3rd ed., DCW Industries.
4. Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational Fluid
   Dynamics: The Finite Volume Method*, 2nd ed., Pearson.
5. ANSYS Inc., *ANSYS Fluent Theory Guide*.
6. Airfoil Tools — http://airfoiltools.com

---



## Author

**<Your Name>**
<Your Department>, <Your College>
GitHub: [@cr1825](https://github.com/cr1825) · Email: pchaitanya74@gmail.com.com
