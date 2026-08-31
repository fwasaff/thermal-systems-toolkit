"""
Verification tests for thermal_toolkit.

These are not "does it run" smoke tests — each one checks the physics
against something independently known to be true: an exact analytical
limit, agreement between two independent numerical methods, or a
round-trip consistency check (inverse function recovers the input).
This is the same style of verification used for numerical solvers in
general: when you don't have a certified reference value, you check
convergence, limiting behavior, and cross-method agreement instead.

Run with: pytest tests/test_verification.py -v
"""
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thermal_toolkit.fluid_flow import (
    reynolds_number, friction_factor_laminar, friction_factor_turbulent,
    optimal_pipe_diameter,
)
from thermal_toolkit.heat_exchangers import (
    effectiveness_ntu_counterflow, ntu_from_effectiveness_counterflow,
)


# ---------------------------------------------------------------------------
# fluid_flow.py
# ---------------------------------------------------------------------------

def test_laminar_friction_factor_exact():
    """f = 64/Re is an exact analytical result (Hagen-Poiseuille) — no
    approximation involved, so this must match to machine precision."""
    Re = 1500.0
    assert friction_factor_laminar(Re) == 64.0 / Re


def test_swamee_jain_vs_colebrook_white_agree():
    """Swamee-Jain is an explicit APPROXIMATION to the implicit
    Colebrook-White equation. They're independent formulations of the
    same physics — if they disagree by more than ~2%, something is
    wrong with one of them. This is cross-validation, not a comparison
    against a known 'right answer'."""
    Re = 50_000.0
    roughness = 0.000045  # commercial steel [m]
    D = 0.05  # m

    f_sj = friction_factor_turbulent(Re, roughness, D, method="swamee-jain")
    f_cw = friction_factor_turbulent(Re, roughness, D, method="colebrook-white")

    rel_error = abs(f_sj - f_cw) / f_cw
    assert rel_error < 0.02, (
        f"Swamee-Jain and Colebrook-White disagree by {rel_error:.1%} "
        f"(f_sj={f_sj:.5f}, f_cw={f_cw:.5f}) — expected agreement within 2%"
    )


def test_colebrook_white_converges():
    """The iterative solver should actually converge, not just run out
    of iterations. Check by verifying the fixed-point residual is small:
    plugging f back into the implicit equation should reproduce f."""
    Re = 80_000.0
    roughness = 0.00015  # galvanized steel
    D = 0.08
    relative_roughness = roughness / D

    f = friction_factor_turbulent(Re, roughness, D, method="colebrook-white")

    # Residual of the implicit Colebrook-White equation itself:
    # 1/sqrt(f) = -2*log10(eps/(3.7D) + 2.51/(Re*sqrt(f)))
    lhs = 1.0 / math.sqrt(f)
    rhs = -2.0 * math.log10(relative_roughness / 3.7 + 2.51 / (Re * math.sqrt(f)))
    assert abs(lhs - rhs) < 1e-4, "Colebrook-White solution does not satisfy its own equation"


def test_reynolds_number_scales_linearly_with_velocity():
    """Re = rho*v*D/mu — doubling velocity must exactly double Re. Basic
    but catches sign/unit errors that a single point-value test would not."""
    D = 0.05
    Re1 = reynolds_number(1.0, D)
    Re2 = reynolds_number(2.0, D)
    assert abs(Re2 - 2 * Re1) < 1e-9


def test_optimal_pipe_diameter_conserves_mass():
    """Continuity: Q = A*v = (pi*D^2/4)*v must hold EXACTLY for whatever
    diameter the sizing function returns — this is mass conservation,
    not a curve fit, so tolerance should be tight."""
    Q = 0.01  # m^3/s
    D, v = optimal_pipe_diameter(Q, v_target=2.0)
    Q_check = (math.pi * D**2 / 4) * v
    assert abs(Q_check - Q) / Q < 1e-9


# ---------------------------------------------------------------------------
# heat_exchangers.py
# ---------------------------------------------------------------------------

def test_ntu_effectiveness_limit_ntu_zero():
    """No transfer area (NTU=0) must give zero effectiveness, for any
    capacity ratio — this is a boundary condition, not a fitted result."""
    for Cr in [0.0, 0.3, 0.7, 1.0]:
        eps = effectiveness_ntu_counterflow(0.0, Cr)
        assert abs(eps) < 1e-9, f"NTU=0 should give effectiveness=0 (Cr={Cr})"


def test_ntu_effectiveness_limit_cr_zero_matches_known_closed_form():
    """When Cr=0 (one fluid changes phase, e.g. condensing steam), the
    counterflow effectiveness formula reduces to the well-known closed
    form eps = 1 - exp(-NTU), independent of the flow arrangement. This
    checks the general formula against that specific analytical case."""
    NTU = 2.5
    eps_general = effectiveness_ntu_counterflow(NTU, C_ratio=0.0)
    eps_known = 1 - math.exp(-NTU)
    assert abs(eps_general - eps_known) < 1e-9


def test_ntu_effectiveness_approaches_one_for_large_ntu():
    """As NTU -> infinity with Cr < 1, effectiveness must approach 1
    (the theoretical maximum) — an infinitely large exchanger cannot
    transfer more heat than the maximum possible."""
    eps = effectiveness_ntu_counterflow(NTU=50.0, C_ratio=0.5)
    assert eps > 0.999


def test_ntu_from_effectiveness_is_the_inverse_function():
    """Round-trip check: NTU -> effectiveness -> NTU should recover the
    original NTU. If the 'inverse' function doesn't actually invert the
    forward one, this is exactly the kind of bug that stays hidden until
    someone uses it for a real design."""
    for NTU_true, Cr in [(0.5, 0.3), (1.2, 0.6), (3.0, 0.9)]:
        eps = effectiveness_ntu_counterflow(NTU_true, Cr)
        NTU_recovered = ntu_from_effectiveness_counterflow(eps, Cr)
        rel_error = abs(NTU_recovered - NTU_true) / NTU_true
        assert rel_error < 1e-3, (
            f"Round-trip failed: NTU={NTU_true} -> eps={eps:.4f} -> "
            f"NTU_recovered={NTU_recovered:.4f} (Cr={Cr})"
        )
