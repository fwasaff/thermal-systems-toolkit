"""
Fluid Properties Module
========================

Temperature-dependent fluid properties via CoolProp, for use anywhere
the rest of the toolkit currently assumes fixed properties at a single
reference temperature (20°C water).

Why this matters
-----------------
A heat recovery system, by definition, moves fluid across a real
temperature range (e.g. 25°C at the pump inlet to 85°C leaving the
compressor jacket). Water's dynamic viscosity drops by more than 4x
between 10°C and 95°C — since Reynolds number and friction factor both
depend on viscosity, using a single 20°C value everywhere introduces a
real error, not just a rounding one, for any point in the system that
isn't actually near 20°C.

This module is additive, not a breaking change: every function elsewhere
in the toolkit that takes `rho`/`mu` keyword arguments still defaults to
the fixed WATER_RHO/WATER_MU constants in fluid_flow.py. Pass
`water_properties(T_celsius)` explicitly when the temperature at that
point in the system matters.

Author: Felipe Wasaff
Email: felipe.wasaff@uchile.cl
"""
from typing import NamedTuple

try:
    import CoolProp.CoolProp as CP
    _HAS_COOLPROP = True
except ImportError:
    _HAS_COOLPROP = False


ATM_PRESSURE_PA = 101_325.0


class FluidProperties(NamedTuple):
    """Properties at one (fluid, T, P) state, in SI base units."""
    rho: float   # density [kg/m^3]
    mu: float    # dynamic viscosity [Pa.s]
    cp: float    # specific heat at constant pressure [J/(kg.K)]
    k: float     # thermal conductivity [W/(m.K)]
    T: float     # temperature this was evaluated at [K]


def _require_coolprop():
    if not _HAS_COOLPROP:
        raise ImportError(
            "CoolProp is not installed. It's an optional dependency, needed "
            "only for temperature-dependent properties: pip install CoolProp. "
            "Without it, use the fixed WATER_RHO/WATER_MU constants in "
            "fluid_flow.py (valid near 20 degC)."
        )


def fluid_properties(fluid: str, T_celsius: float,
                      P_pa: float = ATM_PRESSURE_PA) -> FluidProperties:
    """
    Get density, viscosity, specific heat and thermal conductivity for a
    CoolProp-supported fluid at a given temperature and pressure.

    Parameters
    ----------
    fluid : str
        CoolProp fluid name, e.g. 'Water', or a binary mixture like
        'INCOMP::MEG-30%' for 30% ethylene glycol / water (see CoolProp's
        incompressible-mixtures docs for the exact mixture string format).
    T_celsius : float
        Temperature [degC].
    P_pa : float, optional
        Pressure [Pa]. Default: atmospheric. Matters little for a liquid
        far from its critical point, but CoolProp needs a second state
        variable regardless.

    Returns
    -------
    FluidProperties
        rho [kg/m^3], mu [Pa.s], cp [J/(kg.K)], k [W/(m.K)], T [K]

    Examples
    --------
    >>> props = fluid_properties('Water', 20.0)
    >>> print(f"rho={props.rho:.2f} kg/m3, mu={props.mu:.4e} Pa.s")
    rho=998.21 kg/m3, mu=1.0016e-03 Pa.s
    """
    _require_coolprop()
    T_K = T_celsius + 273.15
    rho = CP.PropsSI('D', 'T', T_K, 'P', P_pa, fluid)
    mu = CP.PropsSI('V', 'T', T_K, 'P', P_pa, fluid)
    cp = CP.PropsSI('C', 'T', T_K, 'P', P_pa, fluid)
    k = CP.PropsSI('L', 'T', T_K, 'P', P_pa, fluid)
    return FluidProperties(rho=rho, mu=mu, cp=cp, k=k, T=T_K)


def water_properties(T_celsius: float, P_pa: float = ATM_PRESSURE_PA) -> FluidProperties:
    """Shorthand for fluid_properties('Water', T_celsius, P_pa) -- the
    common case for this toolkit's default fluid."""
    return fluid_properties('Water', T_celsius, P_pa)
