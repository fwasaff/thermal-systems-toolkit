"""
Heat Exchangers Module
=====================

Heat exchanger design and analysis for thermal systems.

This module implements:
- LMTD (Log Mean Temperature Difference) method
- ε-NTU (Effectiveness-Number of Transfer Units) method
- Heat exchanger sizing and selection
- Pressure drop calculations
- Type comparison (plate, shell-tube, etc.)
- Performance rating

Author: Felipe Wasaff
Email: felipe.wasaff@uchile.cl
Project: CMPC Heat Recovery System
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
import warnings

# Constants
WATER_RHO = 998.0  # kg/m³ at 20°C
WATER_CP = 4186  # J/(kg·K)
WATER_MU = 1.002e-3  # Pa·s


@dataclass
class HeatExchangerSpecification:
    """Data class for heat exchanger specifications."""
    type: str
    manufacturer: str
    model: str
    heat_duty_kW: float
    area_m2: float
    U_coefficient: float
    effectiveness: float
    pressure_drop_hot_kPa: float
    pressure_drop_cold_kPa: float
    num_plates: Optional[int] = None
    num_passes: Optional[int] = None
    material: str = "Stainless Steel 316"


def lmtd_counterflow(T_hot_in: float, T_hot_out: float, T_cold_in: float, T_cold_out: float) -> float:
    """
    Calculate Log Mean Temperature Difference for counterflow.
    
    Parameters
    ----------
    T_hot_in : float
        Hot fluid inlet temperature [°C]
    T_hot_out : float
        Hot fluid outlet temperature [°C]
    T_cold_in : float
        Cold fluid inlet temperature [°C]
    T_cold_out : float
        Cold fluid outlet temperature [°C]
    
    Returns
    -------
    float
        LMTD [K]
    
    Notes
    -----
    LMTD = (ΔT₁ - ΔT₂) / ln(ΔT₁/ΔT₂)
    
    where:
    ΔT₁ = T_hot_in - T_cold_out
    ΔT₂ = T_hot_out - T_cold_in
    """
    dT1 = T_hot_in - T_cold_out
    dT2 = T_hot_out - T_cold_in
    
    if dT1 <= 0 or dT2 <= 0:
        raise ValueError("Invalid temperatures: LMTD requires proper temperature arrangement")
    
    if abs(dT1 - dT2) < 0.01:
        return dT1
    
    LMTD = (dT1 - dT2) / np.log(dT1 / dT2)
    return LMTD


def required_area_lmtd(Q: float, U: float, LMTD: float, F: float = 1.0) -> float:
    """
    Calculate required heat transfer area using LMTD method.
    
    Parameters
    ----------
    Q : float
        Heat transfer rate [W]
    U : float
        Overall heat transfer coefficient [W/(m²·K)]
    LMTD : float
        Log mean temperature difference [K]
    F : float, optional
        Correction factor (1.0 for counterflow)
    
    Returns
    -------
    float
        Required area [m²]
    
    Notes
    -----
    From Q = U·A·LMTD·F:
    A = Q / (U·LMTD·F)
    """
    A = Q / (U * LMTD * F)
    return A


def effectiveness_ntu_counterflow(NTU: float, C_ratio: float) -> float:
    """
    Calculate effectiveness using ε-NTU method for counterflow.
    
    Parameters
    ----------
    NTU : float
        Number of Transfer Units (NTU = UA/C_min)
    C_ratio : float
        Heat capacity ratio (C_min/C_max)
    
    Returns
    -------
    float
        Effectiveness ε
    
    Notes
    -----
    For counterflow:
    ε = (1 - exp[-NTU(1-C_r)]) / (1 - C_r·exp[-NTU(1-C_r)])
    
    Special case C_r = 1:
    ε = NTU / (1 + NTU)
    """
    if not 0 <= C_ratio <= 1:
        raise ValueError("C_ratio must be between 0 and 1")
    
    if abs(C_ratio - 1.0) < 1e-6:
        # Special case: equal heat capacities
        return NTU / (1 + NTU)
    
    exp_term = np.exp(-NTU * (1 - C_ratio))
    epsilon = (1 - exp_term) / (1 - C_ratio * exp_term)
    
    return epsilon


def ntu_from_effectiveness_counterflow(epsilon: float, C_ratio: float) -> float:
    """
    Calculate NTU from effectiveness (inverse problem).
    
    Parameters
    ----------
    epsilon : float
        Effectiveness
    C_ratio : float
        Heat capacity ratio
    
    Returns
    -------
    float
        NTU
    
    Notes
    -----
    For counterflow, solve numerically or use approximation.
    """
    if abs(C_ratio - 1.0) < 1e-6:
        return epsilon / (1 - epsilon)
    
    # Numerical solution using iterative approach
    NTU = 0.1
    for _ in range(50):
        eps_calc = effectiveness_ntu_counterflow(NTU, C_ratio)
        error = eps_calc - epsilon
        
        if abs(error) < 1e-6:
            break
        
        # Simple Newton-like step
        NTU = NTU - error * 0.5
        NTU = max(0.01, NTU)  # Keep positive
    
    return NTU


def heat_capacity_rate(mass_flow: float, cp: float = WATER_CP) -> float:
    """
    Calculate heat capacity rate.
    
    Parameters
    ----------
    mass_flow : float
        Mass flow rate [kg/s]
    cp : float, optional
        Specific heat [J/(kg·K)]
    
    Returns
    -------
    float
        Heat capacity rate C [W/K]
    
    Notes
    -----
    C = ṁ·cp
    """
    return mass_flow * cp


def overall_heat_transfer_coefficient(h_hot: float, h_cold: float, fouling_hot: float = 0.0001, fouling_cold: float = 0.0001, wall_thickness: float = 0.001, wall_k: float = 16.0) -> float:
    """
    Calculate overall heat transfer coefficient.
    
    Parameters
    ----------
    h_hot : float
        Hot side convection coefficient [W/(m²·K)]
    h_cold : float
        Cold side convection coefficient [W/(m²·K)]
    fouling_hot : float, optional
        Hot side fouling resistance [m²·K/W]
    fouling_cold : float, optional
        Cold side fouling resistance [m²·K/W]
    wall_thickness : float, optional
        Wall thickness [m]
    wall_k : float, optional
        Wall thermal conductivity [W/(m·K)]
    
    Returns
    -------
    float
        Overall U coefficient [W/(m²·K)]
    
    Notes
    -----
    1/U = 1/h_hot + R_foul_hot + t_wall/k_wall + R_foul_cold + 1/h_cold
    """
    R_hot = 1 / h_hot
    R_cold = 1 / h_cold
    R_wall = wall_thickness / wall_k
    R_total = R_hot + fouling_hot + R_wall + fouling_cold + R_cold
    
    U = 1 / R_total
    return U


def plate_heat_exchanger_design(Q: float, m_hot: float, m_cold: float, T_hot_in: float, T_hot_out: float, T_cold_in: float, T_cold_out: float, U_estimated: float = 4000.0) -> Dict:
    """
    Design plate heat exchanger using LMTD method.
    
    Parameters
    ----------
    Q : float
        Heat duty [W]
    m_hot : float
        Hot side mass flow [kg/s]
    m_cold : float
        Cold side mass flow [kg/s]
    T_hot_in : float
        Hot inlet temperature [°C]
    T_hot_out : float
        Hot outlet temperature [°C]
    T_cold_in : float
        Cold inlet temperature [°C]
    T_cold_out : float
        Cold outlet temperature [°C]
    U_estimated : float, optional
        Estimated U coefficient [W/(m²·K)]
    
    Returns
    -------
    dict
        Design parameters
    """
    # Calculate LMTD
    LMTD = lmtd_counterflow(T_hot_in, T_hot_out, T_cold_in, T_cold_out)
    
    # Calculate required area
    A_required = required_area_lmtd(Q, U_estimated, LMTD)
    
    # Calculate heat capacity rates
    C_hot = heat_capacity_rate(m_hot)
    C_cold = heat_capacity_rate(m_cold)
    C_min = min(C_hot, C_cold)
    C_max = max(C_hot, C_cold)
    C_ratio = C_min / C_max
    
    # Calculate effectiveness
    Q_max = C_min * (T_hot_in - T_cold_in)
    effectiveness = Q / Q_max
    
    # Calculate NTU
    NTU = U_estimated * A_required / C_min
    
    # Estimate number of plates (typical plate area: 0.3-0.5 m² each)
    plate_area_typical = 0.4  # m²
    num_plates = int(np.ceil(A_required / plate_area_typical))
    
    # Ensure even number (plates work in pairs)
    if num_plates % 2 != 0:
        num_plates += 1
    
    return {
        'heat_duty_W': Q,
        'heat_duty_kW': Q / 1000,
        'LMTD': LMTD,
        'area_required_m2': A_required,
        'U_coefficient': U_estimated,
        'C_hot': C_hot,
        'C_cold': C_cold,
        'C_min': C_min,
        'C_max': C_max,
        'C_ratio': C_ratio,
        'effectiveness': effectiveness,
        'NTU': NTU,
        'num_plates_estimated': num_plates,
        'plate_area_typical_m2': plate_area_typical
    }


def shell_tube_heat_exchanger_design(Q: float, m_hot: float, m_cold: float, T_hot_in: float, T_hot_out: float, T_cold_in: float, T_cold_out: float, U_estimated: float = 1000.0) -> Dict:
    """
    Design shell-and-tube heat exchanger.
    
    Similar to plate design but with different U coefficient.
    """
    LMTD = lmtd_counterflow(T_hot_in, T_hot_out, T_cold_in, T_cold_out)
    A_required = required_area_lmtd(Q, U_estimated, LMTD)
    
    C_hot = heat_capacity_rate(m_hot)
    C_cold = heat_capacity_rate(m_cold)
    C_min = min(C_hot, C_cold)
    C_max = max(C_hot, C_cold)
    C_ratio = C_min / C_max
    
    Q_max = C_min * (T_hot_in - T_cold_in)
    effectiveness = Q / Q_max
    NTU = U_estimated * A_required / C_min
    
    # Estimate tube bundle
    # Typical: 25mm OD tubes, 1m length, ~0.08 m² per tube
    tube_area = 0.08  # m²
    num_tubes = int(np.ceil(A_required / tube_area))
    
    return {
        'heat_duty_W': Q,
        'heat_duty_kW': Q / 1000,
        'LMTD': LMTD,
        'area_required_m2': A_required,
        'U_coefficient': U_estimated,
        'C_hot': C_hot,
        'C_cold': C_cold,
        'C_min': C_min,
        'C_max': C_max,
        'C_ratio': C_ratio,
        'effectiveness': effectiveness,
        'NTU': NTU,
        'num_tubes_estimated': num_tubes
    }


def pressure_drop_plate_hx(flow_rate: float, num_plates: int, plate_spacing: float = 0.003, port_diameter: float = 0.15) -> float:
    """
    Estimate pressure drop in plate heat exchanger.
    
    Parameters
    ----------
    flow_rate : float
        Volumetric flow rate [m³/s]
    num_plates : int
        Number of plates
    plate_spacing : float, optional
        Gap between plates [m]
    port_diameter : float, optional
        Port diameter [m]
    
    Returns
    -------
    float
        Pressure drop [Pa]
    
    Notes
    -----
    Simplified correlation for water in plate HX.
    Typical: 20-100 kPa depending on size and flow.
    """
    # Velocity in channels
    channel_area = plate_spacing * 0.5  # Simplified
    velocity = flow_rate / (channel_area * num_plates / 4)
    
    # Friction factor (simplified)
    Re = WATER_RHO * velocity * (2 * plate_spacing) / WATER_MU
    
    if Re < 2000:
        f = 64 / Re
    else:
        f = 0.316 / (Re ** 0.25)
    
    # Pressure drop
    L_effective = 1.0  # m (typical plate length)
    dP = f * (L_effective / (2 * plate_spacing)) * (WATER_RHO * velocity**2 / 2)
    
    # Add port losses
    port_velocity = flow_rate / (np.pi * port_diameter**2 / 4)
    dP_ports = 0.5 * WATER_RHO * port_velocity**2
    
    dP_total = dP + 2 * dP_ports  # Inlet and outlet
    
    return dP_total


def compare_heat_exchanger_types(Q: float, m_hot: float, m_cold: float, T_hot_in: float, T_hot_out: float, T_cold_in: float, T_cold_out: float) -> Dict:
    """
    Compare different heat exchanger types.
    
    Returns
    -------
    dict
        Comparison of plate vs shell-tube
    """
    # Plate HX
    plate_design = plate_heat_exchanger_design(Q, m_hot, m_cold, T_hot_in, T_hot_out, T_cold_in, T_cold_out, U_estimated=4000)
    
    # Shell-tube HX
    tube_design = shell_tube_heat_exchanger_design(Q, m_hot, m_cold, T_hot_in, T_hot_out, T_cold_in, T_cold_out, U_estimated=1000)
    
    return {
        'plate': plate_design,
        'shell_tube': tube_design,
        'area_ratio': tube_design['area_required_m2'] / plate_design['area_required_m2']
    }


# Typical commercial specifications
COMMERCIAL_PLATE_HX = {
    'Alfa_Laval_CB60': {
        'manufacturer': 'Alfa Laval',
        'model': 'CB60',
        'max_heat_duty_kW': 1000,
        'plate_area_m2': 0.6,
        'max_plates': 100,
        'U_typical': 4500,
        'max_pressure_bar': 25,
        'max_temperature_C': 180,
        'material': 'SS316'
    },
    'Alfa_Laval_CB30': {
        'manufacturer': 'Alfa Laval',
        'model': 'CB30',
        'max_heat_duty_kW': 500,
        'plate_area_m2': 0.3,
        'max_plates': 80,
        'U_typical': 4200,
        'max_pressure_bar': 25,
        'max_temperature_C': 180,
        'material': 'SS316'
    },
    'APV_R55': {
        'manufacturer': 'APV',
        'model': 'R55',
        'max_heat_duty_kW': 800,
        'plate_area_m2': 0.55,
        'max_plates': 90,
        'U_typical': 4300,
        'max_pressure_bar': 20,
        'max_temperature_C': 150,
        'material': 'SS316'
    }
}


def select_commercial_plate_hx(area_required: float, heat_duty_kW: float) -> Dict:
    """
    Select commercial plate heat exchanger.
    
    Parameters
    ----------
    area_required : float
        Required heat transfer area [m²]
    heat_duty_kW : float
        Heat duty [kW]
    
    Returns
    -------
    dict
        Selected unit specification
    """
    for model_name, specs in COMMERCIAL_PLATE_HX.items():
        num_plates = int(np.ceil(area_required / specs['plate_area_m2']))
        
        if num_plates % 2 != 0:
            num_plates += 1
        
        if num_plates <= specs['max_plates'] and heat_duty_kW <= specs['max_heat_duty_kW']:
            return {
                'model': model_name,
                'specs': specs,
                'num_plates': num_plates,
                'total_area_m2': num_plates * specs['plate_area_m2'],
                'oversizing_factor': (num_plates * specs['plate_area_m2']) / area_required
            }
    
    return None
