# Thermal Systems Toolkit

Python toolkit for the classical (non-CFD) fluid mechanics and heat transfer
calculations used to design industrial heat recovery systems: pipe sizing,
pump selection, heat exchanger sizing, and thermal storage tank design.

## What this is

Reusable engineering calculations built on standard, textbook fluid
mechanics and heat transfer — the same methods taught in undergraduate
Fluid Mechanics courses (continuity equation, Bernoulli/general energy
equation, Darcy-Weisbach head losses, ε-NTU heat exchanger sizing).
Reference: Robert L. Mott, *Applied Fluid Mechanics*.

This toolkit grew out of a real industrial heat-recovery consulting
engagement. Client-identifying details and financial figures from that
engagement are **not included here** — this repository contains only the
general-purpose calculation methods, which are reusable for any similar
project, not tied to any one client.

## Modules

| Module | What it does |
|---|---|
| `fluid_flow.py` | Reynolds number, friction factor (laminar exact, turbulent via Swamee-Jain or Colebrook-White), Darcy-Weisbach pressure drop, minor losses, standard pipe sizing (ASME B36.10M) |
| `heat_exchangers.py` | LMTD (counterflow), ε-NTU effectiveness method, plate and shell-and-tube sizing |
| `heat_transfer.py` | Heat duty, temperature-driven sizing for compressor heat recovery |
| `pumps.py` | Pump head requirement for closed-loop systems |
| `storage_tanks.py` | Thermal storage tank sizing |

## Range of application — what this IS and ISN'T for

This is **not** a CFD toolkit. It solves the classical, closed-form/1D
equations of fluid mechanics — it does not discretize a domain, solve
Navier-Stokes, or model turbulence beyond the empirical friction-factor
correlations above. Valid for:

- Single-phase, incompressible liquid flow (water/water-glycol) in pipes
- Steady-state operation (no transients, no water-hammer)
- Turbulent or laminar flow — the transitional regime (2300 < Re < 4000)
  is flagged with a warning and handled conservatively, not solved exactly
  (the friction factor is genuinely unstable in that range; this is a
  known limitation of the underlying correlations, not a bug)
- Bounded ranges of validity for the turbulent friction-factor
  correlations: 4000 < Re < 10⁸, 10⁻⁶ < relative roughness < 10⁻²

**Not appropriate for**: gas flow, multiphase flow, complex 3D geometries
(bends/manifolds beyond standard fitting loss coefficients), or anywhere
the flow field itself — not just the pressure drop — matters. That's what
the CFD/FEM work in the rest of my [portfolio](https://github.com/fwasaff)
is for.

## Verification

`tests/test_verification.py` checks the physics, not just that the code
runs — exact analytical limits (e.g. laminar `f = 64/Re`), agreement
between independent methods (Swamee-Jain vs. Colebrook-White), and
round-trip consistency (NTU → effectiveness → NTU). Running this suite
during a magíster course in numerical methods caught a real bug: the
NTU-from-effectiveness solver used a fixed-step update that assumed a
slope that was wrong near `C_ratio → 1`, silently returning NTU off by
~9%. Replaced with bisection (guaranteed convergence for a monotonic
function, at the cost of a few extra iterations) — see the git history
for the fix.

```bash
pip install -r requirements.txt
pip install pytest
pytest tests/ -v
```

## Installation

```bash
pip install -e .
```

## Author

Felipe Wasaff — felipe.wasaff@uchile.cl
