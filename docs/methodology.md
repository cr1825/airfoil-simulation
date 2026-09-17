# Methodology and Governing Theory

## 1. Problem definition

A two-dimensional NACA 4412 airfoil is placed in a steady, incompressible,
viscous air stream. The objective is to determine how the lift, drag and
pitching-moment coefficients vary with angle of attack, and to identify the
angle giving the best aerodynamic efficiency.

| Parameter | Value |
|---|---|
| Airfoil | NACA 4412 |
| Chord, c | 100 mm |
| Freestream velocity, U | 1.5 m/s |
| Density, ρ | 1.225 kg/m³ |
| Dynamic viscosity, μ | 1.7894 × 10⁻⁵ Pa·s |
| Reynolds number, Re = ρUc/μ | ≈ 1.03 × 10⁴ |
| Mach number | ≈ 0.004 (incompressible) |
| Angles of attack | 0°, 2°, 4°, 6°, 8°, 10° |

Because the Mach number is far below 0.3, density is treated as constant and
the energy equation is not solved.

---

## 2. Governing equations

The solver works with the steady, incompressible Reynolds-Averaged
Navier-Stokes (RANS) equations.

**Continuity**

    ∂(ρ u_i)/∂x_i = 0

**Momentum**

    ∂(ρ u_i u_j)/∂x_j = −∂p/∂x_i + ∂/∂x_j [ μ (∂u_i/∂x_j + ∂u_j/∂x_i) − ρ u'_i u'_j ]

The final term, the Reynolds stress tensor, arises from averaging the turbulent
fluctuations and introduces more unknowns than equations. Closing that system is
the job of the turbulence model.

---

## 3. Turbulence model: standard k-ω

The Wilcox k-ω model solves two extra transport equations, for turbulent kinetic
energy k and specific dissipation rate ω:

    ∂(ρ k u_i)/∂x_i  = ∂/∂x_j [ Γ_k ∂k/∂x_j ] + G_k − Y_k
    ∂(ρ ω u_i)/∂x_i  = ∂/∂x_j [ Γ_ω ∂ω/∂x_j ] + G_ω − Y_ω

The eddy viscosity then follows as μ_t = ρ k / ω.

**Why k-ω rather than k-ε here.** The k-ε model relies on wall functions and
assumes a fully turbulent boundary layer, which makes it poor at predicting
separation. k-ω integrates directly to the wall, so it resolves the viscous
sublayer and captures adverse pressure gradients and the onset of separation
near stall — exactly the physics that determines drag and the shape of the lift
curve near its peak. The price is that the mesh must be fine near the surface,
which is why the inflation layer is mandatory.

---

## 4. Force coefficients

Non-dimensional coefficients let results be compared across different sizes and
speeds:

    C_L = L / (½ ρ U² A)
    C_D = D / (½ ρ U² A)
    C_M = M / (½ ρ U² A c)

where A is the reference area and c the chord. In 2D, A is taken per unit span.
Getting the reference area right in Fluent is essential — the solver computes
the raw force correctly and then divides by whatever number you supplied.

---

## 5. What thin airfoil theory predicts

For a thin airfoil in inviscid flow at small angles, classical theory gives a
lift-curve slope of

    dC_L/dα = 2π per radian ≈ 0.11 per degree

The CFD result is expected to fall slightly **below** this line, because the
theory neglects viscosity and finite thickness. Two checks worth making in the
report:

1. **Slope comparison.** In the linear region (roughly 0° to 6°) the CFD slope
   should be within about 10–15 % of 2π.
2. **Zero-lift angle.** NACA 4412 is cambered, so it produces positive lift at
   α = 0° and its zero-lift angle is negative, around −4°. A symmetric section
   such as NACA 0012 would pass through the origin instead. If your cambered
   airfoil gives C_L ≈ 0 at α = 0°, something is wrong with the setup.

Note that at Re ≈ 10⁴ the flow is in the low-Reynolds-number regime where
laminar separation bubbles are common and fully turbulent RANS models are known
to be less accurate. Mention this as a limitation rather than claiming
quantitative agreement with published high-Re wind tunnel data.

---

## 6. Verification and validation

| Check | What it demonstrates |
|---|---|
| Residuals below 1 × 10⁻⁶ | Iterative convergence |
| C_L and C_D flat over the last iterations | The solution has genuinely settled, not just the residuals |
| Mesh independence study | The answer does not depend on cell size |
| Domain size sensitivity | Outer boundaries are far enough away |
| Comparison with 2π slope | Physical plausibility |

Residual convergence alone is not proof of a correct answer. A converged
solution on a bad mesh is a converged wrong answer, which is why the mesh study
in `scripts/mesh_independence.py` is included.

---

## 7. Limitations

- Two-dimensional: no wingtip vortices, no induced drag, no three-dimensional
  separation.
- Steady RANS: cannot capture vortex shedding or unsteady post-stall behaviour.
- Fully turbulent assumption: transition is not modelled, which matters at this
  Reynolds number.
- Smooth surface, no roughness or freestream turbulence effects.
- Single-element airfoil, no flaps or slats.
