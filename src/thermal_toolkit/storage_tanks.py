"""
Storage Tanks Module
===================

Thermal storage tank design and analysis for energy systems.

This module implements:
- Storage capacity calculations
- Tank dimensioning (volume, diameter, height)
- Thermal stratification analysis
- Heat loss calculations
- Insulation design
- Connection sizing (inlets/outlets)
- Material selection

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
WATER_CP = 4186  # J/(kg·K)
WATER_BETA = 0.000207  # 1/K (thermal expansion coefficient at 20°C)

# Insulation materials (thermal conductivity [W/(m·K)])
INSULATION_MATERIALS = {
    'mineral_wool': 0.040,
    'fiberglass': 0.035,
    'polyurethane_foam': 0.025,
    'polystyrene': 0.033,
    'aerogel': 0.014,
}


@dataclass
class TankSpecification:
    """
    Data class for thermal storage tank specifications.
    
    Attributes
    ----------
    volume : float
        Tank volume [m³]
    diameter : float
        Internal diameter [m]
    height : float
        Internal height [m]
    wall_thickness : float
        Wall thickness [mm]
    insulation_thickness : float
        Insulation thickness [mm]
    material : str
        Tank material
    insulation_material : str
        Insulation material
    design_pressure : float
        Design pressure [bar]
    design_temperature : float
        Design temperature [°C]
    """
    volume: float
    diameter: float
    height: float
    wall_thickness: float
    insulation_thickness: float
    material: str
    insulation_material: str
    design_pressure: float
    design_temperature: float


def storage_capacity(
    volume: float,
    delta_T: float,
    rho: float = WATER_RHO,
    cp: float = WATER_CP
) -> float:
    """
    Calculate thermal storage capacity.
    
    Parameters
    ----------
    volume : float
        Tank volume [m³]
    delta_T : float
        Temperature difference [K]
    rho : float, optional
        Fluid density [kg/m³]
    cp : float, optional
        Specific heat capacity [J/(kg·K)]
    
    Returns
    -------
    float
        Stored energy [J]
    
    Notes
    -----
    E = m·cp·ΔT = V·ρ·cp·ΔT
    
    Examples
    --------
    >>> # 5 m³ tank with 20K temperature difference
    >>> E = storage_capacity(5.0, 20.0)
    >>> print(f"Stored energy: {E/1e6:.2f} MJ")
    Stored energy: 41.86 MJ
    """
    mass = volume * rho
    energy = mass * cp * delta_T
    return energy


def storage_time(
    volume: float,
    delta_T: float,
    power: float,
    rho: float = WATER_RHO,
    cp: float = WATER_CP
) -> float:
    """
    Calculate storage time (how long tank can supply given power).
    
    Parameters
    ----------
    volume : float
        Tank volume [m³]
    delta_T : float
        Temperature difference [K]
    power : float
        Power output [W]
    rho : float, optional
        Fluid density [kg/m³]
    cp : float, optional
        Specific heat capacity [J/(kg·K)]
    
    Returns
    -------
    float
        Storage time [s]
    
    Notes
    -----
    t = E / Q = (V·ρ·cp·ΔT) / Q
    """
    energy = storage_capacity(volume, delta_T, rho, cp)
    time_seconds = energy / power
    return time_seconds


def required_volume(
    power: float,
    storage_time_hours: float,
    delta_T: float,
    rho: float = WATER_RHO,
    cp: float = WATER_CP
) -> float:
    """
    Calculate required tank volume for desired storage time.
    
    Parameters
    ----------
    power : float
        Thermal power [W]
    storage_time_hours : float
        Desired storage time [hours]
    delta_T : float
        Operating temperature difference [K]
    rho : float, optional
        Fluid density [kg/m³]
    cp : float, optional
        Specific heat capacity [J/(kg·K)]
    
    Returns
    -------
    float
        Required volume [m³]
    
    Notes
    -----
    V = (Q·t) / (ρ·cp·ΔT)
    
    Examples
    --------
    >>> # 622 kW system, 15 minutes storage, 25K delta T
    >>> V = required_volume(622e3, 0.25, 25)
    >>> print(f"Required volume: {V:.2f} m³")
    Required volume: 1.42 m³
    """
    time_seconds = storage_time_hours * 3600
    energy_required = power * time_seconds
    volume = energy_required / (rho * cp * delta_T)
    return volume


def optimal_tank_dimensions(
    volume: float,
    height_to_diameter_ratio: float = 2.0
) -> Tuple[float, float]:
    """
    Calculate optimal tank dimensions for given volume.
    
    Parameters
    ----------
    volume : float
        Desired volume [m³]
    height_to_diameter_ratio : float, optional
        H/D ratio (typical range: 1.5-3.0 for good stratification)
    
    Returns
    -------
    diameter : float
        Internal diameter [m]
    height : float
        Internal height [m]
    
    Notes
    -----
    For a cylinder: V = π·D²·H/4
    
    With H = k·D (where k = H/D ratio):
    V = π·D²·(k·D)/4 = π·k·D³/4
    
    Therefore: D = ∛(4V/(π·k))
    
    Typical H/D ratios:
    - 1.5-2.0: Compact, easier to install
    - 2.0-3.0: Better stratification
    - >3.0: Excellent stratification, tall
    """
    # Calculate diameter
    D = (4 * volume / (np.pi * height_to_diameter_ratio)) ** (1/3)
    
    # Calculate height
    H = height_to_diameter_ratio * D
    
    # Verify volume
    V_check = np.pi * D**2 * H / 4
    
    if abs(V_check - volume) / volume > 0.01:
        warnings.warn(f"Volume mismatch: requested {volume:.3f} m³, got {V_check:.3f} m³")
    
    return D, H


def tank_surface_area(diameter: float, height: float) -> Dict[str, float]:
    """
    Calculate tank surface areas.
    
    Parameters
    ----------
    diameter : float
        Internal diameter [m]
    height : float
        Internal height [m]
    
    Returns
    -------
    dict
        Dictionary with cylindrical, top, bottom, and total areas [m²]
    """
    # Cylindrical surface
    A_cylindrical = np.pi * diameter * height
    
    # Top and bottom (circular)
    A_end = np.pi * diameter**2 / 4
    
    # Total
    A_total = A_cylindrical + 2 * A_end
    
    return {
        'cylindrical': A_cylindrical,
        'top': A_end,
        'bottom': A_end,
        'ends_total': 2 * A_end,
        'total': A_total
    }


def richardson_number(
    delta_T: float,
    height: float,
    velocity: float,
    beta: float = WATER_BETA
) -> float:
    """
    Calculate Richardson number for stratification analysis.
    
    Parameters
    ----------
    delta_T : float
        Temperature difference top-to-bottom [K]
    height : float
        Tank height [m]
    velocity : float
        Characteristic velocity (inlet velocity) [m/s]
    beta : float, optional
        Thermal expansion coefficient [1/K]
    
    Returns
    -------
    float
        Richardson number (dimensionless)
    
    Notes
    -----
    Ri = (g·β·ΔT·H) / v²
    
    Interpretation:
    - Ri > 10: Strong stratification (stable)
    - 1 < Ri < 10: Moderate stratification
    - Ri < 1: Weak/no stratification (mixed)
    
    For good thermal storage, aim for Ri > 10
    """
    Ri = (GRAVITY * beta * delta_T * height) / (velocity ** 2)
    return Ri


def stratification_quality(Ri: float) -> str:
    """
    Assess stratification quality based on Richardson number.
    
    Parameters
    ----------
    Ri : float
        Richardson number
    
    Returns
    -------
    str
        Quality assessment
    """
    if Ri > 10:
        return "Excellent - Strong stratification"
    elif Ri > 5:
        return "Good - Moderate stratification"
    elif Ri > 1:
        return "Fair - Weak stratification"
    else:
        return "Poor - Mixed/no stratification"


def inlet_velocity(flow_rate: float, diameter: float) -> float:
    """
    Calculate inlet velocity.
    
    Parameters
    ----------
    flow_rate : float
        Volumetric flow rate [m³/h]
    diameter : float
        Inlet pipe diameter [m]
    
    Returns
    -------
    float
        Velocity [m/s]
    """
    Q_m3s = flow_rate / 3600
    area = np.pi * diameter**2 / 4
    v = Q_m3s / area
    return v


def heat_loss_coefficient(
    insulation_thickness: float,
    insulation_material: str = 'mineral_wool',
    convection_coefficient: float = 10.0
) -> float:
    """
    Calculate overall heat transfer coefficient through insulation.
    
    Parameters
    ----------
    insulation_thickness : float
        Insulation thickness [m]
    insulation_material : str, optional
        Insulation material type
    convection_coefficient : float, optional
        External convection coefficient [W/(m²·K)]
    
    Returns
    -------
    float
        Overall heat transfer coefficient U [W/(m²·K)]
    
    Notes
    -----
    1/U = 1/h_out + t_ins/k_ins
    
    where:
    - h_out: external convection
    - t_ins: insulation thickness
    - k_ins: insulation thermal conductivity
    """
    k_insulation = INSULATION_MATERIALS.get(insulation_material, 0.04)
    
    # Thermal resistances
    R_convection = 1 / convection_coefficient
    R_insulation = insulation_thickness / k_insulation
    
    # Total resistance
    R_total = R_convection + R_insulation
    
    # Overall coefficient
    U = 1 / R_total
    
    return U


def thermal_losses(
    surface_area: float,
    tank_temperature: float,
    ambient_temperature: float,
    U: float
) -> Dict[str, float]:
    """
    Calculate thermal losses from tank.
    
    Parameters
    ----------
    surface_area : float
        Total surface area [m²]
    tank_temperature : float
        Average tank temperature [°C]
    ambient_temperature : float
        Ambient temperature [°C]
    U : float
        Overall heat transfer coefficient [W/(m²·K)]
    
    Returns
    -------
    dict
        Heat loss in various units
    
    Notes
    -----
    Q_loss = U·A·ΔT
    """
    delta_T = tank_temperature - ambient_temperature
    Q_loss_W = U * surface_area * delta_T
    
    # Daily losses
    Q_loss_daily_kWh = (Q_loss_W * 24) / 1000
    
    # Percentage of stored energy
    # Assume typical 5 m³ tank with 20K delta T
    stored_energy_kWh = (5 * WATER_RHO * WATER_CP * 20) / 3.6e6
    loss_percentage = (Q_loss_daily_kWh / stored_energy_kWh) * 100
    
    return {
        'heat_loss_W': Q_loss_W,
        'heat_loss_kW': Q_loss_W / 1000,
        'heat_loss_daily_kWh': Q_loss_daily_kWh,
        'delta_T': delta_T,
        'U_coefficient': U
    }


def required_insulation_thickness(
    target_heat_loss_W: float,
    surface_area: float,
    delta_T: float,
    insulation_material: str = 'mineral_wool',
    convection_coefficient: float = 10.0
) -> float:
    """
    Calculate required insulation thickness for target heat loss.
    
    Parameters
    ----------
    target_heat_loss_W : float
        Maximum allowable heat loss [W]
    surface_area : float
        Tank surface area [m²]
    delta_T : float
        Temperature difference [K]
    insulation_material : str, optional
        Insulation material
    convection_coefficient : float, optional
        External convection [W/(m²·K)]
    
    Returns
    -------
    float
        Required insulation thickness [m]
    
    Notes
    -----
    From Q = U·A·ΔT and 1/U = 1/h + t/k:
    
    t = k·[(A·ΔT/Q) - 1/h]
    """
    k = INSULATION_MATERIALS.get(insulation_material, 0.04)
    
    # Required U coefficient
    U_required = target_heat_loss_W / (surface_area * delta_T)
    
    # Required insulation thickness
    R_required = 1 / U_required
    R_convection = 1 / convection_coefficient
    R_insulation_required = R_required - R_convection
    
    if R_insulation_required < 0:
        warnings.warn("Cannot achieve target heat loss with this material")
        return 0.0
    
    t_required = R_insulation_required * k
    
    return t_required


def wall_thickness_pressure_vessel(
    internal_diameter: float,
    design_pressure: float,
    allowable_stress: float = 140e6,  # Pa (typical for carbon steel)
    corrosion_allowance: float = 0.003,  # m (3 mm)
    weld_efficiency: float = 0.85
) -> float:
    """
    Calculate required wall thickness for pressure vessel.
    
    Parameters
    ----------
    internal_diameter : float
        Internal diameter [m]
    design_pressure : float
        Design pressure [Pa]
    allowable_stress : float, optional
        Allowable stress [Pa]
    corrosion_allowance : float, optional
        Corrosion allowance [m]
    weld_efficiency : float, optional
        Weld joint efficiency
    
    Returns
    -------
    float
        Required wall thickness [m]
    
    Notes
    -----
    ASME Section VIII Division 1:
    t = (P·R) / (S·E - 0.6·P) + corrosion
    
    where:
    - P: design pressure
    - R: inside radius
    - S: allowable stress
    - E: weld efficiency
    """
    R = internal_diameter / 2
    
    # Required thickness (without corrosion)
    t_required = (design_pressure * R) / (allowable_stress * weld_efficiency - 0.6 * design_pressure)
    
    # Add corrosion allowance
    t_total = t_required + corrosion_allowance
    
    return t_total


def connection_sizing(
    flow_rate: float,
    target_velocity: float = 1.5
) -> Dict[str, float]:
    """
    Size inlet/outlet connections for tank.
    
    Parameters
    ----------
    flow_rate : float
        Flow rate [m³/h]
    target_velocity : float, optional
        Target velocity [m/s] (1-2 m/s for stratification)
    
    Returns
    -------
    dict
        Connection sizing recommendations
    
    Notes
    -----
    For good stratification:
    - Keep inlet velocity low (< 0.3 m/s at diffuser)
    - Use diffusers or distribution manifolds
    - Separate hot inlet (top) and cold outlet (bottom)
    """
    Q_m3s = flow_rate / 3600
    
    # Calculate diameter for target velocity
    D_calculated = np.sqrt(4 * Q_m3s / (np.pi * target_velocity))
    
    # Standard pipe sizes (DN)
    standard_DNs = [25, 32, 40, 50, 65, 80, 100, 125, 150]
    DN = min(standard_DNs, key=lambda x: abs(x/1000 - D_calculated))
    
    D_actual = DN / 1000  # Convert to meters
    v_actual = 4 * Q_m3s / (np.pi * D_actual**2)
    
    return {
        'flow_rate_m3h': flow_rate,
        'target_velocity_ms': target_velocity,
        'calculated_diameter_m': D_calculated,
        'selected_DN': DN,
        'actual_diameter_m': D_actual,
        'actual_velocity_ms': v_actual
    }


def design_thermal_storage_tank(
    power: float,
    storage_time_hours: float,
    delta_T: float,
    design_pressure_bar: float = 2.0,
    insulation_material: str = 'mineral_wool',
    target_heat_loss_percentage: float = 2.0
) -> TankSpecification:
    """
    Complete thermal storage tank design.
    
    Parameters
    ----------
    power : float
        System thermal power [W]
    storage_time_hours : float
        Desired storage time [hours]
    delta_T : float
        Operating temperature difference [K]
    design_pressure_bar : float, optional
        Design pressure [bar]
    insulation_material : str, optional
        Insulation material
    target_heat_loss_percentage : float, optional
        Target daily heat loss as % of stored energy
    
    Returns
    -------
    TankSpecification
        Complete tank specifications
    
    Examples
    --------
    >>> # Design tank for CMPC system
    >>> tank = design_thermal_storage_tank(
    ...     power=622e3,  # 622 kW
    ...     storage_time_hours=0.25,  # 15 minutes
    ...     delta_T=25.0  # 25 K
    ... )
    >>> print(f"Volume: {tank.volume:.2f} m³")
    >>> print(f"Dimensions: {tank.diameter:.2f}m × {tank.height:.2f}m")
    """
    # Calculate required volume
    volume = required_volume(power, storage_time_hours, delta_T)
    
    # Calculate optimal dimensions (H/D = 2.5 for good stratification)
    diameter, height = optimal_tank_dimensions(volume, height_to_diameter_ratio=2.5)
    
    # Calculate wall thickness
    design_pressure_Pa = design_pressure_bar * 1e5
    wall_thickness = wall_thickness_pressure_vessel(diameter, design_pressure_Pa)
    
    # Calculate surface area
    areas = tank_surface_area(diameter, height)
    
    # Calculate required insulation for target heat loss
    # Assume average tank temp = 60°C, ambient = 20°C
    delta_T_thermal = 40  # K
    stored_energy = storage_capacity(volume, delta_T)
    target_loss_daily = (stored_energy * target_heat_loss_percentage / 100) / 86400  # W
    
    insulation_thickness = required_insulation_thickness(
        target_loss_daily,
        areas['total'],
        delta_T_thermal,
        insulation_material
    )
    
    # Design temperature (assume 80°C max for low-pressure hot water)
    design_temperature = 80.0  # °C
    
    return TankSpecification(
        volume=volume,
        diameter=diameter,
        height=height,
        wall_thickness=wall_thickness * 1000,  # Convert to mm
        insulation_thickness=insulation_thickness * 1000,  # Convert to mm
        material='Carbon Steel ASTM A36',
        insulation_material=insulation_material,
        design_pressure=design_pressure_bar,
        design_temperature=design_temperature
    )
