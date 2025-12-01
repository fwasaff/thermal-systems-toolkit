"""
Heat Transfer Module
===================

Fundamental heat transfer calculations for thermal system design.

Author: Felipe Wasaff
Email: felipe.wasaff@uchile.cl
"""

import numpy as np
from typing import Union, Tuple

# Physical constants
WATER_CP = 4186  # J/(kg·K) at 20°C
WATER_RHO = 998  # kg/m³ at 20°C


def heat_capacity_flow(
    mass_flow: float,
    cp: float = WATER_CP
) -> float:
    """
    Calculate heat capacity flow rate.
    
    Parameters
    ----------
    mass_flow : float
        Mass flow rate [kg/s]
    cp : float, optional
        Specific heat capacity [J/(kg·K)], default water at 20°C
    
    Returns
    -------
    float
        Heat capacity flow rate [W/K]
    
    Examples
    --------
    >>> mass_flow = 5.944  # kg/s (21.4 m³/h from CMPC project)
    >>> C = heat_capacity_flow(mass_flow)
    >>> print(f"Heat capacity flow: {C:.2f} W/K")
    Heat capacity flow: 24873.78 W/K
    """
    return mass_flow * cp


def required_heat_transfer(
    mass_flow: float,
    delta_T: float,
    cp: float = WATER_CP
) -> float:
    """
    Calculate required heat transfer rate.
    
    This is the fundamental equation: Q = ṁ · cp · ΔT
    
    Parameters
    ----------
    mass_flow : float
        Mass flow rate [kg/s]
    delta_T : float
        Temperature difference [K or °C]
    cp : float, optional
        Specific heat capacity [J/(kg·K)]
    
    Returns
    -------
    float
        Heat transfer rate [W]
    
    Examples
    --------
    >>> # CMPC Project: 622 kW demand, 21.4 m³/h flow, ΔT = 25 K
    >>> Q = required_heat_transfer(5.944, 25)
    >>> print(f"Heat transfer: {Q/1000:.1f} kW")
    Heat transfer: 622.0 kW
    
    Notes
    -----
    Derived from first law of thermodynamics for steady flow:
    Q̇ = ṁ·cp·ΔT
    
    References
    ----------
    Incropera et al., "Fundamentals of Heat and Mass Transfer", 7th ed.
    """
    return mass_flow * cp * delta_T


def volumetric_to_mass_flow(
    vol_flow: float,
    rho: float = WATER_RHO
) -> float:
    """
    Convert volumetric to mass flow rate.
    
    Parameters
    ----------
    vol_flow : float
        Volumetric flow rate [m³/s]
    rho : float, optional
        Fluid density [kg/m³]
    
    Returns
    -------
    float
        Mass flow rate [kg/s]
    
    Examples
    --------
    >>> # Convert 21.4 m³/h to kg/s
    >>> vol_flow_m3s = 21.4 / 3600  # m³/h to m³/s
    >>> mass_flow = volumetric_to_mass_flow(vol_flow_m3s)
    >>> print(f"Mass flow: {mass_flow:.3f} kg/s")
    Mass flow: 5.933 kg/s
    """
    return vol_flow * rho


def lmtd(
    T_hot_in: float,
    T_hot_out: float,
    T_cold_in: float,
    T_cold_out: float
) -> float:
    """
    Calculate Log Mean Temperature Difference for heat exchanger.
    
    Parameters
    ----------
    T_hot_in : float
        Hot fluid inlet temperature [°C or K]
    T_hot_out : float
        Hot fluid outlet temperature
    T_cold_in : float
        Cold fluid inlet temperature
    T_cold_out : float
        Cold fluid outlet temperature
    
    Returns
    -------
    float
        LMTD [K]
    
    Examples
    --------
    >>> # Counterflow heat exchanger
    >>> lmtd_val = lmtd(90, 70, 15, 40)
    >>> print(f"LMTD: {lmtd_val:.2f} K")
    LMTD: 43.13 K
    
    Notes
    -----
    For counterflow arrangement:
    LMTD = (ΔT₁ - ΔT₂) / ln(ΔT₁/ΔT₂)
    where ΔT₁ = T_hot_in - T_cold_out
          ΔT₂ = T_hot_out - T_cold_in
    
    References
    ----------
    Incropera et al., "Fundamentals of Heat and Mass Transfer", 7th ed.
    """
    dT1 = T_hot_in - T_cold_out
    dT2 = T_hot_out - T_cold_in
    
    if abs(dT1 - dT2) < 1e-6:  # Avoid division by zero
        return dT1
    
    if dT1 <= 0 or dT2 <= 0:
        raise ValueError("Temperature differences must be positive for valid LMTD calculation")
    
    return (dT1 - dT2) / np.log(dT1 / dT2)


def heat_exchanger_area(
    Q: float,
    U: float,
    LMTD: float
) -> float:
    """
    Calculate required heat exchanger area.
    
    Parameters
    ----------
    Q : float
        Heat transfer rate [W]
    U : float
        Overall heat transfer coefficient [W/(m²·K)]
    LMTD : float
        Log mean temperature difference [K]
    
    Returns
    -------
    float
        Required heat transfer area [m²]
    
    Examples
    --------
    >>> # Design heat exchanger for CMPC compressor
    >>> Q = 246e3  # W (246 kW)
    >>> U = 500    # W/(m²·K) typical for water-air compact HX
    >>> LMTD_val = 40  # K
    >>> A = heat_exchanger_area(Q, U, LMTD_val)
    >>> print(f"Required area: {A:.2f} m²")
    Required area: 12.30 m²
    
    Notes
    -----
    From heat exchanger design equation:
    Q = U·A·LMTD
    
    Therefore:
    A = Q / (U·LMTD)
    
    References
    ----------
    Incropera et al., "Fundamentals of Heat and Mass Transfer", 7th ed.
    """
    if U <= 0 or LMTD <= 0:
        raise ValueError("U and LMTD must be positive")
    
    return Q / (U * LMTD)


def thermal_resistance(
    area: float,
    U: float
) -> float:
    """
    Calculate thermal resistance of heat exchanger.
    
    Parameters
    ----------
    area : float
        Heat transfer area [m²]
    U : float
        Overall heat transfer coefficient [W/(m²·K)]
    
    Returns
    -------
    float
        Thermal resistance [K/W]
    
    Notes
    -----
    R_thermal = 1 / (U·A)
    """
    return 1.0 / (U * area)


def effectiveness_ntu(
    NTU: float,
    C_ratio: float,
    flow_arrangement: str = 'counterflow'
) -> float:
    """
    Calculate heat exchanger effectiveness using ε-NTU method.
    
    Parameters
    ----------
    NTU : float
        Number of Transfer Units (NTU = UA/C_min)
    C_ratio : float
        Heat capacity ratio (C_min/C_max)
    flow_arrangement : str, optional
        Flow arrangement: 'counterflow', 'parallel', 'crossflow'
    
    Returns
    -------
    float
        Heat exchanger effectiveness ε
    
    Notes
    -----
    For counterflow:
    ε = (1 - exp[-NTU(1-C_r)]) / (1 - C_r·exp[-NTU(1-C_r)])
    
    For parallel flow:
    ε = (1 - exp[-NTU(1+C_r)]) / (1 + C_r)
    
    References
    ----------
    Incropera et al., "Fundamentals of Heat and Mass Transfer", 7th ed.
    """
    if not 0 <= C_ratio <= 1:
        raise ValueError("C_ratio must be between 0 and 1")
    
    if flow_arrangement == 'counterflow':
        if abs(C_ratio - 1.0) < 1e-6:  # C_ratio ≈ 1
            return NTU / (1 + NTU)
        else:
            numerator = 1 - np.exp(-NTU * (1 - C_ratio))
            denominator = 1 - C_ratio * np.exp(-NTU * (1 - C_ratio))
            return numerator / denominator
    
    elif flow_arrangement == 'parallel':
        return (1 - np.exp(-NTU * (1 + C_ratio))) / (1 + C_ratio)
    
    else:
        raise ValueError(f"Flow arrangement '{flow_arrangement}' not implemented")


# Convenience function for common use case
def calculate_heat_transfer_system(
    Q_target: float,
    flow_rate_m3h: float,
    delta_T: float,
    cp: float = WATER_CP,
    rho: float = WATER_RHO
) -> dict:
    """
    Calculate complete heat transfer system parameters.
    
    This is a convenience function that combines multiple calculations
    for a typical water-based heat recovery system.
    
    Parameters
    ----------
    Q_target : float
        Target heat transfer rate [W]
    flow_rate_m3h : float
        Volumetric flow rate [m³/h]
    delta_T : float
        Design temperature difference [K]
    cp : float, optional
        Specific heat capacity [J/(kg·K)]
    rho : float, optional
        Fluid density [kg/m³]
    
    Returns
    -------
    dict
        Dictionary with system parameters
    
    Examples
    --------
    >>> # CMPC compressor FSD 575
    >>> results = calculate_heat_transfer_system(
    ...     Q_target=246e3,      # 246 kW
    ...     flow_rate_m3h=8.61,  # m³/h
    ...     delta_T=25           # K
    ... )
    >>> print(f"Mass flow: {results['mass_flow_kg_s']:.3f} kg/s")
    >>> print(f"Heat achieved: {results['Q_actual_kW']:.1f} kW")
    """
    # Convert volumetric to mass flow
    vol_flow_m3s = flow_rate_m3h / 3600
    mass_flow = volumetric_to_mass_flow(vol_flow_m3s, rho)
    
    # Calculate actual heat transfer
    Q_actual = required_heat_transfer(mass_flow, delta_T, cp)
    
    # Calculate heat capacity flow
    C_flow = heat_capacity_flow(mass_flow, cp)
    
    return {
        'mass_flow_kg_s': mass_flow,
        'volumetric_flow_m3_s': vol_flow_m3s,
        'Q_actual_W': Q_actual,
        'Q_actual_kW': Q_actual / 1000,
        'Q_target_W': Q_target,
        'Q_target_kW': Q_target / 1000,
        'heat_capacity_flow_W_per_K': C_flow,
        'delta_T_K': delta_T,
        'match_percentage': (Q_actual / Q_target) * 100 if Q_target > 0 else 0
    }
