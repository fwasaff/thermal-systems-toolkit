"""
Fluid Flow Module
================

Fluid mechanics calculations for pipe design and pressure drop analysis.

This module implements:
- Darcy-Weisbach equation for friction losses
- Reynolds number calculations
- Friction factor (Moody diagram, Colebrook-White, Swamee-Jain)
- Minor losses (fittings, valves, etc.)
- Pipe sizing based on velocity constraints

Author: Felipe Wasaff
Email: felipe.wasaff@uchile.cl
Project: CMPC Heat Recovery System
"""

import numpy as np
from typing import Union, Tuple, Dict
import warnings

# Physical constants for water at 20°C
WATER_RHO = 998.0  # kg/m³
WATER_MU = 1.002e-3  # Pa·s (dynamic viscosity)
WATER_NU = 1.004e-6  # m²/s (kinematic viscosity)

# Pipe roughness values [m]
PIPE_ROUGHNESS = {
    'commercial_steel': 0.000045,
    'pvc': 0.0000015,
    'copper': 0.0000015,
    'cast_iron': 0.00026,
    'galvanized_steel': 0.00015,
    'concrete': 0.0003,
}

# Standard pipe sizes (DN - Nominal Diameter) [mm]
STANDARD_DN = [15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300]


def reynolds_number(
    velocity: float,
    diameter: float,
    rho: float = WATER_RHO,
    mu: float = WATER_MU
) -> float:
    """
    Calculate Reynolds number.
    
    Parameters
    ----------
    velocity : float
        Fluid velocity [m/s]
    diameter : float
        Pipe internal diameter [m]
    rho : float, optional
        Fluid density [kg/m³]
    mu : float, optional
        Dynamic viscosity [Pa·s]
    
    Returns
    -------
    float
        Reynolds number (dimensionless)
    
    Notes
    -----
    Re = ρ·v·D / μ
    
    Flow regimes:
    - Re < 2300: Laminar
    - 2300 < Re < 4000: Transitional
    - Re > 4000: Turbulent
    """
    return rho * velocity * diameter / mu


def friction_factor_laminar(Re: float) -> float:
    """
    Calculate friction factor for laminar flow.
    
    Parameters
    ----------
    Re : float
        Reynolds number
    
    Returns
    -------
    float
        Friction factor
    
    Notes
    -----
    For laminar flow (Re < 2300):
    f = 64 / Re
    """
    return 64.0 / Re


def friction_factor_turbulent(
    Re: float,
    roughness: float,
    diameter: float,
    method: str = 'swamee-jain'
) -> float:
    """
    Calculate friction factor for turbulent flow.
    
    Parameters
    ----------
    Re : float
        Reynolds number
    roughness : float
        Absolute pipe roughness [m]
    diameter : float
        Pipe internal diameter [m]
    method : str, optional
        Calculation method: 'swamee-jain' (default) or 'colebrook-white'
    
    Returns
    -------
    float
        Friction factor
    
    Notes
    -----
    Swamee-Jain approximation (explicit):
    f = 0.25 / [log₁₀(ε/(3.7·D) + 5.74/Re^0.9)]²
    
    Valid for:
    - 4000 < Re < 10⁸
    - 10⁻⁶ < ε/D < 10⁻²
    """
    relative_roughness = roughness / diameter
    
    if method == 'swamee-jain':
        # Swamee-Jain equation (explicit, easier to compute)
        term1 = relative_roughness / 3.7
        term2 = 5.74 / (Re ** 0.9)
        f = 0.25 / (np.log10(term1 + term2) ** 2)
        
    elif method == 'colebrook-white':
        # Colebrook-White (implicit, solved iteratively)
        # 1/√f = -2·log₁₀(ε/(3.7·D) + 2.51/(Re·√f))
        
        # Initial guess using Swamee-Jain
        f = friction_factor_turbulent(Re, roughness, diameter, 'swamee-jain')
        
        # Iterate to converge
        for _ in range(10):
            f_new = 1.0 / (
                -2.0 * np.log10(
                    relative_roughness / 3.7 + 2.51 / (Re * np.sqrt(f))
                )
            ) ** 2
            
            if abs(f_new - f) < 1e-6:
                break
            f = f_new
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return f


def friction_factor(
    Re: float,
    roughness: float,
    diameter: float,
    method: str = 'swamee-jain'
) -> float:
    """
    Calculate friction factor for any flow regime.
    
    Parameters
    ----------
    Re : float
        Reynolds number
    roughness : float
        Absolute pipe roughness [m]
    diameter : float
        Pipe internal diameter [m]
    method : str, optional
        Calculation method for turbulent flow
    
    Returns
    -------
    float
        Friction factor
    
    Notes
    -----
    Automatically selects appropriate equation based on Reynolds number:
    - Re < 2300: Laminar (f = 64/Re)
    - Re > 4000: Turbulent (Swamee-Jain or Colebrook-White)
    - 2300 < Re < 4000: Transitional (linear interpolation)
    """
    if Re < 2300:
        # Laminar flow
        return friction_factor_laminar(Re)
    
    elif Re > 4000:
        # Turbulent flow
        return friction_factor_turbulent(Re, roughness, diameter, method)
    
    else:
        # Transitional flow (linear interpolation)
        f_lam = friction_factor_laminar(2300)
        f_turb = friction_factor_turbulent(4000, roughness, diameter, method)
        
        # Linear interpolation
        f = f_lam + (f_turb - f_lam) * (Re - 2300) / (4000 - 2300)
        return f


def pressure_drop_darcy_weisbach(
    velocity: float,
    length: float,
    diameter: float,
    roughness: float,
    rho: float = WATER_RHO,
    mu: float = WATER_MU
) -> Tuple[float, Dict]:
    """
    Calculate pressure drop using Darcy-Weisbach equation.
    
    Parameters
    ----------
    velocity : float
        Fluid velocity [m/s]
    length : float
        Pipe length [m]
    diameter : float
        Pipe internal diameter [m]
    roughness : float
        Absolute pipe roughness [m]
    rho : float, optional
        Fluid density [kg/m³]
    mu : float, optional
        Dynamic viscosity [Pa·s]
    
    Returns
    -------
    pressure_drop : float
        Pressure drop [Pa]
    details : dict
        Dictionary with calculation details (Re, f, regime)
    
    Notes
    -----
    Darcy-Weisbach equation:
    ΔP = f · (L/D) · (ρ·v²/2)
    
    Examples
    --------
    >>> # Calculate pressure drop in 10m of DN50 pipe at 2 m/s
    >>> v = 2.0  # m/s
    >>> L = 10.0  # m
    >>> D = 0.050  # m (DN50)
    >>> roughness = PIPE_ROUGHNESS['commercial_steel']
    >>> dP, details = pressure_drop_darcy_weisbach(v, L, D, roughness)
    >>> print(f"Pressure drop: {dP/1000:.2f} kPa")
    >>> print(f"Reynolds: {details['Re']:.0f}, Regime: {details['regime']}")
    """
    # Calculate Reynolds number
    Re = reynolds_number(velocity, diameter, rho, mu)
    
    # Determine flow regime
    if Re < 2300:
        regime = 'laminar'
    elif Re > 4000:
        regime = 'turbulent'
    else:
        regime = 'transitional'
    
    # Calculate friction factor
    f = friction_factor(Re, roughness, diameter)
    
    # Calculate pressure drop (Darcy-Weisbach)
    dP = f * (length / diameter) * (rho * velocity**2 / 2)
    
    # Return results with details
    details = {
        'Re': Re,
        'f': f,
        'regime': regime,
        'velocity': velocity,
        'diameter': diameter,
        'length': length
    }
    
    return dP, details


def minor_loss_coefficient(fitting_type: str) -> float:
    """
    Get loss coefficient (K) for common pipe fittings.
    
    Parameters
    ----------
    fitting_type : str
        Type of fitting
    
    Returns
    -------
    float
        Loss coefficient K
    
    Notes
    -----
    Pressure drop for minor losses:
    ΔP = K · (ρ·v²/2)
    
    Available fittings:
    - '90_elbow': 90° elbow
    - '45_elbow': 45° elbow
    - 'tee_branch': Tee (flow through branch)
    - 'tee_line': Tee (flow through line)
    - 'gate_valve_open': Gate valve (fully open)
    - 'globe_valve_open': Globe valve (fully open)
    - 'check_valve': Check valve
    - 'entrance_sharp': Sharp entrance
    - 'entrance_rounded': Rounded entrance
    - 'exit': Pipe exit
    """
    K_values = {
        '90_elbow': 0.9,
        '45_elbow': 0.4,
        'tee_branch': 1.8,
        'tee_line': 0.9,
        'gate_valve_open': 0.2,
        'globe_valve_open': 10.0,
        'check_valve': 2.5,
        'entrance_sharp': 0.5,
        'entrance_rounded': 0.05,
        'exit': 1.0,
    }
    
    if fitting_type not in K_values:
        raise ValueError(f"Unknown fitting type: {fitting_type}")
    
    return K_values[fitting_type]


def pressure_drop_minor_losses(
    velocity: float,
    K_total: float,
    rho: float = WATER_RHO
) -> float:
    """
    Calculate pressure drop due to minor losses (fittings, valves).
    
    Parameters
    ----------
    velocity : float
        Fluid velocity [m/s]
    K_total : float
        Sum of all loss coefficients
    rho : float, optional
        Fluid density [kg/m³]
    
    Returns
    -------
    float
        Pressure drop [Pa]
    
    Notes
    -----
    ΔP = K · (ρ·v²/2)
    """
    return K_total * (rho * velocity**2 / 2)


def equivalent_length(
    fittings: Dict[str, int],
    diameter: float
) -> float:
    """
    Calculate equivalent length of fittings.
    
    Parameters
    ----------
    fittings : dict
        Dictionary with fitting types as keys and quantities as values
    diameter : float
        Pipe diameter [m]
    
    Returns
    -------
    float
        Equivalent length [m]
    
    Notes
    -----
    Uses L_eq = K · D / f method with f ≈ 0.02 (typical for turbulent flow)
    
    Examples
    --------
    >>> fittings = {'90_elbow': 4, 'gate_valve_open': 2}
    >>> L_eq = equivalent_length(fittings, 0.050)  # DN50
    >>> print(f"Equivalent length: {L_eq:.2f} m")
    """
    f_typical = 0.02  # Typical friction factor for turbulent flow
    L_eq = 0.0
    
    for fitting_type, quantity in fittings.items():
        K = minor_loss_coefficient(fitting_type)
        L_eq += quantity * K * diameter / f_typical
    
    return L_eq


def optimal_pipe_diameter(
    flow_rate: float,
    v_min: float = 0.6,
    v_max: float = 3.0,
    v_target: float = 2.0
) -> Tuple[float, float]:
    """
    Calculate optimal pipe diameter based on velocity constraints.
    
    Parameters
    ----------
    flow_rate : float
        Volumetric flow rate [m³/s]
    v_min : float, optional
        Minimum allowable velocity [m/s]
    v_max : float, optional
        Maximum allowable velocity [m/s]
    v_target : float, optional
        Target velocity [m/s]
    
    Returns
    -------
    diameter : float
        Optimal internal diameter [m]
    velocity : float
        Actual velocity at optimal diameter [m/s]
    
    Notes
    -----
    From continuity equation:
    Q = A·v = (π·D²/4)·v
    
    Therefore:
    D = √(4·Q / (π·v))
    """
    # Calculate diameter for target velocity
    D = np.sqrt(4 * flow_rate / (np.pi * v_target))
    
    # Check if velocity is within bounds
    v_actual = 4 * flow_rate / (np.pi * D**2)
    
    if v_actual < v_min:
        D = np.sqrt(4 * flow_rate / (np.pi * v_min))
        v_actual = v_min
        warnings.warn(f"Velocity below minimum. Adjusted to {v_min} m/s")
    
    elif v_actual > v_max:
        D = np.sqrt(4 * flow_rate / (np.pi * v_max))
        v_actual = v_max
        warnings.warn(f"Velocity above maximum. Adjusted to {v_max} m/s")
    
    return D, v_actual


def select_standard_pipe(
    diameter_calculated: float,
    schedule: str = 'schedule_40'
) -> Tuple[int, float, float]:
    """
    Select nearest standard pipe size (DN) and get internal diameter.
    
    Parameters
    ----------
    diameter_calculated : float
        Calculated internal diameter [m]
    schedule : str, optional
        Pipe schedule (affects wall thickness)
    
    Returns
    -------
    DN : int
        Nominal diameter [mm]
    D_internal : float
        Actual internal diameter [m]
    D_external : float
        External diameter [m]
    
    Notes
    -----
    This is a simplified function. In practice, use ASME B36.10M tables.
    
    For Schedule 40 (most common):
    D_internal ≈ DN - 2·wall_thickness
    """
    # Convert to mm
    D_calc_mm = diameter_calculated * 1000
    
    # Find nearest standard DN
    DN = min(STANDARD_DN, key=lambda x: abs(x - D_calc_mm))
    
    # Approximate internal diameter for Schedule 40
    # (simplified - use actual tables for precision)
    if schedule == 'schedule_40':
        # Approximate formula: D_internal = DN - 2·wall_thickness
        # Wall thickness varies with DN (simplified approximation)
        if DN <= 50:
            wall_thickness = 3.0  # mm
        elif DN <= 100:
            wall_thickness = 4.0  # mm
        else:
            wall_thickness = 6.0  # mm
        
        D_internal = (DN - 2 * wall_thickness) / 1000  # Convert to m
        D_external = DN / 1000
    
    return DN, D_internal, D_external


def pipe_design_summary(
    flow_rate_m3h: float,
    length: float,
    fittings: Dict[str, int],
    material: str = 'commercial_steel',
    v_target: float = 2.0
) -> Dict:
    """
    Complete pipe design calculation.
    
    Parameters
    ----------
    flow_rate_m3h : float
        Volumetric flow rate [m³/h]
    length : float
        Straight pipe length [m]
    fittings : dict
        Dictionary of fittings and quantities
    material : str, optional
        Pipe material (for roughness)
    v_target : float, optional
        Target velocity [m/s]
    
    Returns
    -------
    dict
        Complete design summary
    
    Examples
    --------
    >>> # Design pipe for CMPC compressor FSD 575
    >>> flow = 8.61  # m³/h
    >>> length = 10.0  # m
    >>> fittings = {'90_elbow': 3, 'gate_valve_open': 1}
    >>> design = pipe_design_summary(flow, length, fittings)
    >>> print(f"DN: {design['DN']}")
    >>> print(f"Pressure drop: {design['pressure_drop_total_kPa']:.2f} kPa")
    """
    # Convert flow rate to m³/s
    Q = flow_rate_m3h / 3600
    
    # Calculate optimal diameter
    D_calc, v_calc = optimal_pipe_diameter(Q, v_target=v_target)
    
    # Select standard pipe
    DN, D_internal, D_external = select_standard_pipe(D_calc)
    
    # Recalculate velocity with actual pipe diameter
    v_actual = 4 * Q / (np.pi * D_internal**2)
    
    # Get pipe roughness
    roughness = PIPE_ROUGHNESS[material]
    
    # Calculate equivalent length of fittings
    L_eq = equivalent_length(fittings, D_internal)
    L_total = length + L_eq
    
    # Calculate pressure drop (friction)
    dP_friction, details = pressure_drop_darcy_weisbach(
        v_actual, L_total, D_internal, roughness
    )
    
    # Calculate minor losses (alternative method, for verification)
    K_total = sum(minor_loss_coefficient(f) * n for f, n in fittings.items())
    dP_minor = pressure_drop_minor_losses(v_actual, K_total)
    
    # Total pressure drop
    dP_total = dP_friction  # Already includes equivalent length
    
    return {
        'flow_rate_m3h': flow_rate_m3h,
        'flow_rate_m3s': Q,
        'DN': DN,
        'D_internal_mm': D_internal * 1000,
        'D_internal_m': D_internal,
        'velocity_m_s': v_actual,
        'length_straight_m': length,
        'length_equivalent_m': L_eq,
        'length_total_m': L_total,
        'Reynolds': details['Re'],
        'friction_factor': details['f'],
        'flow_regime': details['regime'],
        'pressure_drop_friction_Pa': dP_friction,
        'pressure_drop_friction_kPa': dP_friction / 1000,
        'pressure_drop_friction_bar': dP_friction / 100000,
        'pressure_drop_total_Pa': dP_total,
        'pressure_drop_total_kPa': dP_total / 1000,
        'pressure_drop_total_bar': dP_total / 100000,
        'material': material,
        'roughness_m': roughness
    }
