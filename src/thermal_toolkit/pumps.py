"""
Pumps Module
===========

Pump selection, sizing, and performance analysis for fluid systems.

This module implements:
- Total Dynamic Head (TDH) calculations
- System curve generation
- Pump curve modeling
- Operating point determination
- NPSH calculations and cavitation analysis
- Power and efficiency calculations
- Multi-pump configurations (series/parallel)

Author: Felipe Wasaff
Email: felipe.wasaff@uchile.cl
Project: CMPC Heat Recovery System
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
import warnings

# Constants
GRAVITY = 9.81  # m/s²
WATER_RHO = 998.0  # kg/m³ at 20°C
WATER_VAPOR_PRESSURE = 2.34e3  # Pa at 20°C
ATM_PRESSURE = 101325  # Pa


@dataclass
class PumpSpecification:
    """
    Data class for pump specifications.
    
    Attributes
    ----------
    model : str
        Pump model name
    manufacturer : str
        Manufacturer name
    rated_flow : float
        Rated flow rate [m³/h]
    rated_head : float
        Rated head [m]
    rated_power : float
        Rated power [kW]
    rated_efficiency : float
        Efficiency at rated point [%]
    max_flow : float
        Maximum flow [m³/h]
    shutoff_head : float
        Head at zero flow [m]
    npsh_required : float
        NPSH required at rated flow [m]
    speed : float
        Rotational speed [rpm]
    impeller_diameter : float
        Impeller diameter [mm]
    """
    model: str
    manufacturer: str
    rated_flow: float
    rated_head: float
    rated_power: float
    rated_efficiency: float
    max_flow: float
    shutoff_head: float
    npsh_required: float
    speed: float = 1450  # Standard for 50 Hz
    impeller_diameter: float = None


def total_dynamic_head(
    static_head: float,
    friction_loss: float,
    minor_losses: float = 0.0,
    equipment_losses: float = 0.0,
    velocity_head: float = 0.0
) -> float:
    """
    Calculate Total Dynamic Head (TDH).
    
    Parameters
    ----------
    static_head : float
        Static elevation difference [m]
    friction_loss : float
        Friction losses in piping [m]
    minor_losses : float, optional
        Minor losses (fittings, valves) [m]
    equipment_losses : float, optional
        Losses in equipment (heat exchangers, etc.) [m]
    velocity_head : float, optional
        Velocity head difference [m]
    
    Returns
    -------
    float
        Total Dynamic Head [m]
    
    Notes
    -----
    TDH = H_static + H_friction + H_minor + H_equipment + H_velocity
    
    Examples
    --------
    >>> # CMPC system with 1.2m elevation, 5m friction, 2m equipment
    >>> TDH = total_dynamic_head(1.2, 5.0, 1.0, 2.0)
    >>> print(f"TDH: {TDH:.1f} m")
    TDH: 9.2 m
    """
    return static_head + friction_loss + minor_losses + equipment_losses + velocity_head


def pressure_to_head(pressure: float, rho: float = WATER_RHO) -> float:
    """
    Convert pressure to head.
    
    Parameters
    ----------
    pressure : float
        Pressure [Pa]
    rho : float, optional
        Fluid density [kg/m³]
    
    Returns
    -------
    float
        Head [m]
    
    Notes
    -----
    H = P / (ρ·g)
    """
    return pressure / (rho * GRAVITY)


def head_to_pressure(head: float, rho: float = WATER_RHO) -> float:
    """
    Convert head to pressure.
    
    Parameters
    ----------
    head : float
        Head [m]
    rho : float, optional
        Fluid density [kg/m³]
    
    Returns
    -------
    float
        Pressure [Pa]
    
    Notes
    -----
    P = H·ρ·g
    """
    return head * rho * GRAVITY


def system_curve(
    flow_rates: np.ndarray,
    static_head: float,
    K_system: float
) -> np.ndarray:
    """
    Generate system curve: H = H_static + K·Q²
    
    Parameters
    ----------
    flow_rates : array_like
        Array of flow rates [m³/h]
    static_head : float
        Static head [m]
    K_system : float
        System resistance coefficient [h²/m⁵]
    
    Returns
    -------
    array_like
        Required head at each flow rate [m]
    
    Notes
    -----
    System curve equation:
    H_system(Q) = H_static + K·Q²
    
    where K is derived from friction losses:
    K = (f·L/D + ΣK_minor) / (2·g·A²)
    """
    Q = np.array(flow_rates)
    return static_head + K_system * Q**2


def calculate_system_K(
    design_flow: float,
    design_head_loss: float,
    static_head: float
) -> float:
    """
    Calculate system resistance coefficient K.
    
    Parameters
    ----------
    design_flow : float
        Design flow rate [m³/h]
    design_head_loss : float
        Total head loss at design flow [m]
    static_head : float
        Static head [m]
    
    Returns
    -------
    float
        System resistance coefficient K [h²/m⁵]
    
    Notes
    -----
    From H_system = H_static + K·Q²:
    K = (H_design - H_static) / Q_design²
    """
    dynamic_loss = design_head_loss - static_head
    K = dynamic_loss / (design_flow ** 2)
    return K


def pump_curve_polynomial(
    flow_rates: np.ndarray,
    shutoff_head: float,
    rated_flow: float,
    rated_head: float
) -> np.ndarray:
    """
    Generate pump characteristic curve using quadratic model.
    
    Parameters
    ----------
    flow_rates : array_like
        Array of flow rates [m³/h]
    shutoff_head : float
        Head at zero flow [m]
    rated_flow : float
        Rated flow [m³/h]
    rated_head : float
        Head at rated flow [m]
    
    Returns
    -------
    array_like
        Pump head at each flow rate [m]
    
    Notes
    -----
    Pump curve approximation:
    H_pump(Q) = H₀ - a·Q²
    
    where:
    - H₀ = shutoff head
    - a = (H₀ - H_rated) / Q_rated²
    """
    Q = np.array(flow_rates)
    a = (shutoff_head - rated_head) / (rated_flow ** 2)
    return shutoff_head - a * Q**2


def find_operating_point(
    system_K: float,
    static_head: float,
    shutoff_head: float,
    rated_flow: float,
    rated_head: float
) -> Tuple[float, float]:
    """
    Find operating point (intersection of pump and system curves).
    
    Parameters
    ----------
    system_K : float
        System resistance coefficient
    static_head : float
        Static head [m]
    shutoff_head : float
        Pump shutoff head [m]
    rated_flow : float
        Pump rated flow [m³/h]
    rated_head : float
        Pump rated head [m]
    
    Returns
    -------
    Q_op : float
        Operating flow rate [m³/h]
    H_op : float
        Operating head [m]
    
    Notes
    -----
    Solve: H_pump(Q) = H_system(Q)
    
    H₀ - a·Q² = H_static + K·Q²
    Q² = (H₀ - H_static) / (a + K)
    """
    # Pump coefficient
    a = (shutoff_head - rated_head) / (rated_flow ** 2)
    
    # Solve for Q
    Q_squared = (shutoff_head - static_head) / (a + system_K)
    
    if Q_squared < 0:
        raise ValueError("No intersection: static head exceeds pump capacity")
    
    Q_op = np.sqrt(Q_squared)
    H_op = static_head + system_K * Q_op**2
    
    return Q_op, H_op


def pump_power(
    flow: float,
    head: float,
    efficiency: float,
    rho: float = WATER_RHO
) -> Dict[str, float]:
    """
    Calculate pump power requirements.
    
    Parameters
    ----------
    flow : float
        Flow rate [m³/h]
    head : float
        Head [m]
    efficiency : float
        Pump efficiency [%]
    rho : float, optional
        Fluid density [kg/m³]
    
    Returns
    -------
    dict
        Dictionary with hydraulic power, shaft power, and motor power
    
    Notes
    -----
    Hydraulic power: P_h = ρ·g·Q·H [W]
    Shaft power:     P_s = P_h / η_pump
    Motor power:     P_m = P_s / η_motor (typically η_motor ≈ 0.9)
    """
    # Convert flow to m³/s
    Q_m3s = flow / 3600
    
    # Hydraulic power [W]
    P_hydraulic = rho * GRAVITY * Q_m3s * head
    
    # Shaft power [W]
    eta_decimal = efficiency / 100
    P_shaft = P_hydraulic / eta_decimal
    
    # Motor power [W] (assume 90% motor efficiency)
    eta_motor = 0.90
    P_motor = P_shaft / eta_motor
    
    return {
        'hydraulic_power_W': P_hydraulic,
        'hydraulic_power_kW': P_hydraulic / 1000,
        'shaft_power_W': P_shaft,
        'shaft_power_kW': P_shaft / 1000,
        'motor_power_W': P_motor,
        'motor_power_kW': P_motor / 1000,
        'efficiency_pump': efficiency,
        'efficiency_motor': eta_motor * 100
    }


def npsh_available(
    atmospheric_pressure: float = ATM_PRESSURE,
    vapor_pressure: float = WATER_VAPOR_PRESSURE,
    static_suction_head: float = 0.0,
    suction_friction_loss: float = 0.0,
    rho: float = WATER_RHO
) -> float:
    """
    Calculate Net Positive Suction Head Available (NPSH_a).
    
    Parameters
    ----------
    atmospheric_pressure : float, optional
        Atmospheric pressure [Pa]
    vapor_pressure : float, optional
        Fluid vapor pressure [Pa]
    static_suction_head : float, optional
        Static height from fluid surface to pump centerline [m]
        Positive if pump is above fluid, negative if below
    suction_friction_loss : float, optional
        Friction loss in suction line [m]
    rho : float, optional
        Fluid density [kg/m³]
    
    Returns
    -------
    float
        NPSH available [m]
    
    Notes
    -----
    NPSH_a = (P_atm - P_vapor)/(ρ·g) + H_static - H_friction_suction
    
    For closed loop systems (like CMPC):
    NPSH_a is typically very high since system is pressurized
    """
    pressure_head = (atmospheric_pressure - vapor_pressure) / (rho * GRAVITY)
    npsh_a = pressure_head + static_suction_head - suction_friction_loss
    
    return npsh_a


def check_cavitation(
    npsh_available: float,
    npsh_required: float,
    safety_margin: float = 0.5
) -> Dict[str, any]:
    """
    Check if cavitation risk exists.
    
    Parameters
    ----------
    npsh_available : float
        NPSH available [m]
    npsh_required : float
        NPSH required by pump [m]
    safety_margin : float, optional
        Recommended safety margin [m]
    
    Returns
    -------
    dict
        Cavitation analysis results
    
    Notes
    -----
    Safe operation requires:
    NPSH_available > NPSH_required + safety_margin
    """
    margin = npsh_available - npsh_required
    is_safe = margin > safety_margin
    
    return {
        'npsh_available': npsh_available,
        'npsh_required': npsh_required,
        'margin': margin,
        'safety_margin_target': safety_margin,
        'is_safe': is_safe,
        'status': 'SAFE' if is_safe else 'CAVITATION RISK'
    }


def energy_cost_annual(
    power_kW: float,
    operating_hours_per_year: float,
    electricity_cost_per_kWh: float
) -> Dict[str, float]:
    """
    Calculate annual energy cost.
    
    Parameters
    ----------
    power_kW : float
        Power consumption [kW]
    operating_hours_per_year : float
        Operating hours per year [h/year]
    electricity_cost_per_kWh : float
        Electricity cost [$/kWh or CLP/kWh]
    
    Returns
    -------
    dict
        Energy consumption and cost analysis
    """
    annual_energy_kWh = power_kW * operating_hours_per_year
    annual_cost = annual_energy_kWh * electricity_cost_per_kWh
    
    return {
        'power_kW': power_kW,
        'operating_hours_per_year': operating_hours_per_year,
        'annual_energy_kWh': annual_energy_kWh,
        'annual_energy_MWh': annual_energy_kWh / 1000,
        'electricity_cost_per_kWh': electricity_cost_per_kWh,
        'annual_cost': annual_cost,
        'monthly_cost': annual_cost / 12
    }


def pumps_in_series(
    pumps: List[PumpSpecification],
    flow_rate: float
) -> Dict[str, float]:
    """
    Calculate performance of pumps in series.
    
    Parameters
    ----------
    pumps : list
        List of pump specifications
    flow_rate : float
        Operating flow rate [m³/h]
    
    Returns
    -------
    dict
        Combined performance
    
    Notes
    -----
    Series configuration:
    - Same flow through all pumps
    - Heads add up: H_total = H₁ + H₂ + ...
    """
    total_head = 0.0
    
    for pump in pumps:
        # Calculate head from each pump at given flow
        a = (pump.shutoff_head - pump.rated_head) / (pump.rated_flow ** 2)
        head = pump.shutoff_head - a * flow_rate**2
        total_head += head
    
    return {
        'configuration': 'series',
        'num_pumps': len(pumps),
        'flow_rate': flow_rate,
        'total_head': total_head
    }


def pumps_in_parallel(
    pumps: List[PumpSpecification],
    head: float
) -> Dict[str, float]:
    """
    Calculate performance of pumps in parallel.
    
    Parameters
    ----------
    pumps : list
        List of pump specifications (must be identical)
    head : float
        Operating head [m]
    
    Returns
    -------
    dict
        Combined performance
    
    Notes
    -----
    Parallel configuration:
    - Same head across all pumps
    - Flows add up: Q_total = Q₁ + Q₂ + ...
    """
    total_flow = 0.0
    
    for pump in pumps:
        # Calculate flow from each pump at given head
        # From H = H₀ - a·Q²: Q = √[(H₀ - H)/a]
        a = (pump.shutoff_head - pump.rated_head) / (pump.rated_flow ** 2)
        
        if head > pump.shutoff_head:
            warnings.warn(f"Head {head}m exceeds pump capacity {pump.shutoff_head}m")
            flow = 0.0
        else:
            flow = np.sqrt((pump.shutoff_head - head) / a)
        
        total_flow += flow
    
    return {
        'configuration': 'parallel',
        'num_pumps': len(pumps),
        'head': head,
        'total_flow': total_flow,
        'flow_per_pump': total_flow / len(pumps)
    }


# Library of common pumps (example database)
PUMP_LIBRARY = {
    'Grundfos_TPE3_D_40_120': PumpSpecification(
        model='TPE3 D 40-120/4',
        manufacturer='Grundfos',
        rated_flow=40.0,  # m³/h
        rated_head=12.0,  # m
        rated_power=1.5,  # kW
        rated_efficiency=70.0,  # %
        max_flow=55.0,
        shutoff_head=15.0,
        npsh_required=2.5,
        speed=1450,
        impeller_diameter=120
    ),
    'Grundfos_TPE3_D_25_80': PumpSpecification(
        model='TPE3 D 25-80/4',
        manufacturer='Grundfos',
        rated_flow=25.0,
        rated_head=8.0,
        rated_power=0.75,
        rated_efficiency=68.0,
        max_flow=35.0,
        shutoff_head=10.0,
        npsh_required=2.0,
        speed=1450,
        impeller_diameter=80
    ),
    'KSB_Etanorm_32_160': PumpSpecification(
        model='Etanorm 032-160',
        manufacturer='KSB',
        rated_flow=35.0,
        rated_head=14.0,
        rated_power=2.2,
        rated_efficiency=72.0,
        max_flow=50.0,
        shutoff_head=17.0,
        npsh_required=3.0,
        speed=1450,
        impeller_diameter=160
    ),
}
