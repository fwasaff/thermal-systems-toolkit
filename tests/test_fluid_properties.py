"""
Verification tests for fluid_properties.py (CoolProp integration).

Same philosophy as test_verification.py: check the physics is right, not
just that CoolProp is callable.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thermal_toolkit.fluid_properties import water_properties
from thermal_toolkit.fluid_flow import pipe_design_summary, WATER_RHO, WATER_MU


def test_water_at_20C_matches_toolkit_constants():
    """The fixed WATER_RHO/WATER_MU constants elsewhere in the toolkit are
    documented as 'water at 20 degC' -- CoolProp should agree with them
    to within the precision those constants were given at (3-4 sig figs)."""
    props = water_properties(20.0)
    assert abs(props.rho - WATER_RHO) / WATER_RHO < 0.001
    assert abs(props.mu - WATER_MU) / WATER_MU < 0.001


def test_water_viscosity_decreases_with_temperature():
    """Physical sanity check: liquid water gets LESS viscous as it warms
    up (unlike gases, where viscosity increases with T) -- if this ever
    comes back false, something is wrong with the CoolProp call, not
    with physics."""
    mu_10 = water_properties(10.0).mu
    mu_95 = water_properties(95.0).mu
    assert mu_95 < mu_10
    # Not just "decreases" -- decreases by a LOT (this is the whole reason
    # a fixed-temperature toolkit gives the wrong answer for a real loop)
    assert mu_10 / mu_95 > 3.0


def test_water_density_decreases_with_temperature():
    """Same idea for density -- water expands as it warms (away from the
    4 degC anomaly, irrelevant for a hot industrial loop)."""
    rho_20 = water_properties(20.0).rho
    rho_90 = water_properties(90.0).rho
    assert rho_90 < rho_20


def test_pipe_design_matches_fixed_constants_when_temperature_omitted():
    """Backward compatibility: calling pipe_design_summary WITHOUT
    temperature_celsius must give exactly the same result as before this
    feature existed -- existing callers shouldn't see any change."""
    flow, length = 8.61, 10.0
    fittings = {'90_elbow': 3, 'gate_valve_open': 1}

    result = pipe_design_summary(flow, length, fittings)
    assert result['fluid_rho'] == WATER_RHO
    assert result['fluid_mu'] == WATER_MU
    assert result['fluid_T_celsius'] is None


def test_pipe_design_temperature_changes_the_answer():
    """The whole point of this feature: water at 85 degC (viscosity
    ~3x lower than at 20 degC) must give a MEASURABLY different pressure
    drop for the identical pipe and flow rate -- if it didn't, the
    temperature parameter would be decorative, not doing anything."""
    flow, length = 8.61, 10.0
    fittings = {'90_elbow': 3, 'gate_valve_open': 1}

    d20 = pipe_design_summary(flow, length, fittings, temperature_celsius=20.0)
    d85 = pipe_design_summary(flow, length, fittings, temperature_celsius=85.0)

    rel_diff = abs(d85['pressure_drop_total_kPa'] - d20['pressure_drop_total_kPa']) \
        / d20['pressure_drop_total_kPa']
    assert rel_diff > 0.05, (
        f"Expected >5% difference in pressure drop between 20 and 85 degC, "
        f"got {rel_diff:.1%} -- temperature_celsius may not be doing anything"
    )
