"""
CMPC Heat Recovery System - Thermal Storage Design
==================================================

This script designs the thermal storage accumulator tank for the heat
recovery system, including:
- Volume calculation based on system dynamics
- Optimal tank dimensions for stratification
- Wall thickness and pressure vessel design
- Insulation specification and heat loss analysis
- Connection sizing and placement
- Material selection and cost estimation

Author: Felipe Wasaff
Date: December 2024
Project: CMPC Puente Alto Heat Recovery System
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from thermal_toolkit import storage_tanks as st
from thermal_toolkit import fluid_flow as ff
from thermal_toolkit import pumps as pm
from thermal_toolkit import heat_transfer as ht


def load_project_data():
    """Load project specifications."""
    data_dir = Path(__file__).parent / 'data'
    
    with open(data_dir / 'compressor_specs.json', 'r') as f:
        compressor_data = json.load(f)
    
    with open(data_dir / 'operating_scenarios.json', 'r') as f:
        scenario_data = json.load(f)
    
    return compressor_data, scenario_data


def determine_storage_requirements(scenario_data):
    """
    Determine thermal storage requirements.
    
    Parameters
    ----------
    scenario_data : dict
        Operating scenarios data
    
    Returns
    -------
    dict
        Storage requirements
    """
    
    print("\n" + "="*70)
    print("THERMAL STORAGE REQUIREMENTS ANALYSIS")
    print("="*70)
    
    design = scenario_data['design_conditions']
    
    # System parameters
    design_power = design['design_thermal_power_kW'] * 1000  # Convert to W
    max_power = design['maximum_thermal_power_kW'] * 1000
    design_flow = design['design_water_flow_m3_per_h']
    
    print(f"\nSystem thermal power:")
    print(f"  Design (80%):     {design_power/1000:.0f} kW")
    print(f"  Maximum (2%):     {max_power/1000:.0f} kW")
    
    # Operating temperature range
    T_supply = 65  # °C (hot water from compressors)
    T_return = 40  # °C (return water)
    delta_T = T_supply - T_return
    
    print(f"\nOperating temperatures:")
    print(f"  Supply (hot):     {T_supply}°C")
    print(f"  Return (cold):    {T_return}°C")
    print(f"  Delta T:          {delta_T} K")
    
    # Storage time analysis
    print(f"\n" + "-"*70)
    print("STORAGE TIME SCENARIOS")
    print("-"*70)
    
    storage_scenarios = [
        {'name': '5 minutes', 'hours': 5/60, 'purpose': 'Minimal buffer'},
        {'name': '15 minutes', 'hours': 15/60, 'purpose': 'Recommended'},
        {'name': '30 minutes', 'hours': 30/60, 'purpose': 'Extended buffer'},
        {'name': '1 hour', 'hours': 1.0, 'purpose': 'Peak shaving'}
    ]
    
    print(f"\n{'Time':<15} {'Volume [m³]':<12} {'Purpose':<20} {'Cost Factor'}")
    print("-"*70)
    
    for scenario in storage_scenarios:
        volume = st.required_volume(
            design_power,
            scenario['hours'],
            delta_T
        )
        cost_factor = volume / st.required_volume(design_power, 15/60, delta_T)
        
        print(f"{scenario['name']:<15} {volume:<12.2f} {scenario['purpose']:<20} {cost_factor:.2f}×")
    
    # RECOMMENDATION
    print(f"\n" + "="*70)
    print("RECOMMENDED STORAGE TIME: 15 minutes")
    print("="*70)
    
    storage_time_recommended = 15 / 60  # hours
    volume_recommended = st.required_volume(design_power, storage_time_recommended, delta_T)
    
    print(f"\nRationale:")
    print(f"  ✓ Absorbs transient load variations")
    print(f"  ✓ Allows compressor start/stop without immediate demand")
    print(f"  ✓ Smooths flow to industrial water heat exchanger")
    print(f"  ✓ Provides operational buffer for maintenance")
    print(f"  ✓ Reasonable cost vs. benefit")
    
    print(f"\nRequired volume: {volume_recommended:.2f} m³")
    
    # Add safety factor
    safety_factor = 1.15  # 15% safety margin
    volume_design = volume_recommended * safety_factor
    
    print(f"With 15% safety:  {volume_design:.2f} m³")
    
    # Verify energy storage
    energy_stored = st.storage_capacity(volume_design, delta_T)
    
    print(f"\nEnergy storage capacity:")
    print(f"  Total energy:     {energy_stored/1e6:.2f} MJ")
    print(f"  Total energy:     {energy_stored/3.6e6:.2f} kWh")
    print(f"  At {design_power/1000:.0f} kW:      {energy_stored/design_power/60:.1f} minutes")
    
    return {
        'design_power_W': design_power,
        'max_power_W': max_power,
        'design_flow_m3h': design_flow,
        'T_supply': T_supply,
        'T_return': T_return,
        'delta_T': delta_T,
        'storage_time_hours': storage_time_recommended,
        'volume_required_m3': volume_recommended,
        'safety_factor': safety_factor,
        'volume_design_m3': volume_design,
        'energy_stored_MJ': energy_stored / 1e6
    }


def design_tank_geometry(volume: float):
    """
    Design tank physical geometry.
    
    Parameters
    ----------
    volume : float
        Required volume [m³]
    
    Returns
    -------
    dict
        Tank geometry specifications
    """
    
    print("\n" + "="*70)
    print("TANK GEOMETRY DESIGN")
    print("="*70)
    
    print(f"\nDesign criteria:")
    print(f"  Target volume:     {volume:.3f} m³")
    print(f"  Orientation:       Vertical cylinder")
    print(f"  Goal:              Maximize thermal stratification")
    
    # Analyze different H/D ratios
    print(f"\n" + "-"*70)
    print("HEIGHT-TO-DIAMETER RATIO ANALYSIS")
    print("-"*70)
    
    ratios = [1.5, 2.0, 2.5, 3.0, 3.5]
    
    print(f"\n{'H/D':<6} {'Diameter [m]':<14} {'Height [m]':<12} {'Assessment'}")
    print("-"*70)
    
    geometries = []
    for ratio in ratios:
        D, H = st.optimal_tank_dimensions(volume, ratio)
        
        if ratio < 2.0:
            assessment = "Compact, poor stratification"
        elif ratio < 2.5:
            assessment = "Good balance"
        elif ratio < 3.5:
            assessment = "Excellent stratification"
        else:
            assessment = "Very tall, difficult install"
        
        geometries.append({
            'ratio': ratio,
            'diameter': D,
            'height': H,
            'assessment': assessment
        })
        
        print(f"{ratio:<6.1f} {D:<14.3f} {H:<12.3f} {assessment}")
    
    # SELECTED DESIGN
    print(f"\n" + "="*70)
    print("SELECTED GEOMETRY: H/D = 2.5")
    print("="*70)
    
    selected_ratio = 2.5
    D_internal, H_internal = st.optimal_tank_dimensions(volume, selected_ratio)
    
    print(f"\nInternal dimensions:")
    print(f"  Diameter (D):      {D_internal:.3f} m = {D_internal*1000:.0f} mm")
    print(f"  Height (H):        {H_internal:.3f} m = {H_internal*1000:.0f} mm")
    print(f"  Volume:            {volume:.3f} m³")
    print(f"  H/D ratio:         {selected_ratio:.1f}")
    
    # Calculate surface areas
    areas = st.tank_surface_area(D_internal, H_internal)
    
    print(f"\nSurface areas:")
    print(f"  Cylindrical wall:  {areas['cylindrical']:.2f} m²")
    print(f"  Top head:          {areas['top']:.2f} m²")
    print(f"  Bottom head:       {areas['bottom']:.2f} m²")
    print(f"  Total:             {areas['total']:.2f} m²")
    
    return {
        'volume_m3': volume,
        'H_D_ratio': selected_ratio,
        'diameter_internal_m': D_internal,
        'height_internal_m': H_internal,
        'diameter_internal_mm': D_internal * 1000,
        'height_internal_mm': H_internal * 1000,
        'surface_areas': areas
    }


def design_pressure_vessel(geometry: dict):
    """
    Design pressure vessel (wall thickness).
    
    Parameters
    ----------
    geometry : dict
        Tank geometry
    
    Returns
    -------
    dict
        Pressure vessel design
    """
    
    print("\n" + "="*70)
    print("PRESSURE VESSEL DESIGN")
    print("="*70)
    
    # Design conditions
    design_pressure_bar = 2.5  # bar (above atmospheric)
    design_temperature = 85  # °C (above normal operating)
    
    print(f"\nDesign conditions:")
    print(f"  Design pressure:   {design_pressure_bar} bar (gauge)")
    print(f"  Design temperature: {design_temperature}°C")
    print(f"  Design code:       ASME Section VIII Div 1")
    
    # Material selection
    material = "Carbon Steel ASTM A36"
    allowable_stress = 140e6  # Pa at design temperature
    
    print(f"\nMaterial:")
    print(f"  Material:          {material}")
    print(f"  Allowable stress:  {allowable_stress/1e6:.0f} MPa")
    
    # Calculate wall thickness
    D_internal = geometry['diameter_internal_m']
    P_design = design_pressure_bar * 1e5  # Convert to Pa
    
    wall_thickness = st.wall_thickness_pressure_vessel(
        D_internal,
        P_design,
        allowable_stress=allowable_stress,
        corrosion_allowance=0.003,  # 3 mm
        weld_efficiency=0.85
    )
    
    # Round up to standard thickness
    standard_thicknesses = [5, 6, 8, 10, 12, 15, 20]  # mm
    wall_thickness_mm = wall_thickness * 1000
    wall_thickness_std = min([t for t in standard_thicknesses if t >= wall_thickness_mm])
    
    print(f"\nWall thickness:")
    print(f"  Calculated:        {wall_thickness_mm:.2f} mm")
    print(f"  Standard:          {wall_thickness_std} mm")
    print(f"  Corrosion allow:   3 mm (included)")
    
    # External dimensions
    D_external = D_internal + 2 * (wall_thickness_std / 1000)
    H_external = geometry['height_internal_m']  # Heads add minimal height
    
    print(f"\nExternal dimensions:")
    print(f"  Diameter:          {D_external:.3f} m = {D_external*1000:.0f} mm")
    print(f"  Height:            {H_external:.3f} m = {H_external*1000:.0f} mm")
    
    # Weight estimation
    volume_steel = (np.pi * D_external**2 * H_external / 4) - geometry['volume_m3']
    rho_steel = 7850  # kg/m³
    weight_empty = volume_steel * rho_steel
    weight_full = weight_empty + geometry['volume_m3'] * 998  # kg (water)
    
    print(f"\nWeight:")
    print(f"  Empty:             {weight_empty:.0f} kg")
    print(f"  Full (water):      {weight_full:.0f} kg")
    print(f"  Steel volume:      {volume_steel:.3f} m³")
    
    return {
        'design_pressure_bar': design_pressure_bar,
        'design_temperature_C': design_temperature,
        'material': material,
        'allowable_stress_MPa': allowable_stress / 1e6,
        'wall_thickness_mm': wall_thickness_std,
        'diameter_external_m': D_external,
        'height_external_m': H_external,
        'weight_empty_kg': weight_empty,
        'weight_full_kg': weight_full
    }


def design_insulation(geometry: dict, storage_req: dict):
    """
    Design thermal insulation.
    
    Parameters
    ----------
    geometry : dict
        Tank geometry
    storage_req : dict
        Storage requirements
    
    Returns
    -------
    dict
        Insulation design
    """
    
    print("\n" + "="*70)
    print("THERMAL INSULATION DESIGN")
    print("="*70)
    
    # Operating conditions
    T_avg_tank = (storage_req['T_supply'] + storage_req['T_return']) / 2
    T_ambient = 20  # °C (indoor installation)
    delta_T = T_avg_tank - T_ambient
    
    print(f"\nOperating conditions:")
    print(f"  Average tank temp: {T_avg_tank:.1f}°C")
    print(f"  Ambient temp:      {T_ambient}°C")
    print(f"  Delta T:           {delta_T:.1f} K")
    
    # Target heat loss: < 2% of stored energy per day
    target_loss_percentage = 2.0
    energy_stored = storage_req['energy_stored_MJ'] * 1e6  # J
    target_loss_daily = energy_stored * target_loss_percentage / 100
    target_loss_W = target_loss_daily / 86400  # Convert to W
    
    print(f"\nHeat loss targets:")
    print(f"  Target:            < {target_loss_percentage}% per day")
    print(f"  Max heat loss:     {target_loss_W:.1f} W")
    
    # Analyze insulation materials
    print(f"\n" + "-"*70)
    print("INSULATION MATERIAL COMPARISON")
    print("-"*70)
    
    materials = ['mineral_wool', 'fiberglass', 'polyurethane_foam']
    
    print(f"\n{'Material':<20} {'k [W/m·K]':<12} {'Thick [mm]':<12} {'U [W/m²·K]':<12}")
    print("-"*70)
    
    insulation_options = []
    for mat in materials:
        thickness = st.required_insulation_thickness(
            target_loss_W,
            geometry['surface_areas']['total'],
            delta_T,
            mat
        )
        
        U = st.heat_loss_coefficient(thickness, mat)
        k = st.INSULATION_MATERIALS[mat]
        
        insulation_options.append({
            'material': mat,
            'k': k,
            'thickness_m': thickness,
            'thickness_mm': thickness * 1000,
            'U': U
        })
        
        print(f"{mat:<20} {k:<12.3f} {thickness*1000:<12.0f} {U:<12.3f}")
    
    # SELECTED INSULATION
    print(f"\n" + "="*70)
    print("SELECTED INSULATION: Mineral Wool")
    print("="*70)
    
    selected = next(opt for opt in insulation_options if opt['material'] == 'mineral_wool')
    
    # Round up to practical thickness
    thickness_practical = 75  # mm (standard thickness)
    
    print(f"\nSpecification:")
    print(f"  Material:          Mineral wool (rock wool)")
    print(f"  Calculated thick:  {selected['thickness_mm']:.0f} mm")
    print(f"  Installed thick:   {thickness_practical} mm")
    print(f"  Density:           100-120 kg/m³")
    print(f"  Jacket:            Aluminum 0.5 mm")
    
    # Verify heat loss with installed thickness
    U_actual = st.heat_loss_coefficient(thickness_practical / 1000, 'mineral_wool')
    actual_losses = st.thermal_losses(
        geometry['surface_areas']['total'],
        T_avg_tank,
        T_ambient,
        U_actual
    )
    
    print(f"\nActual thermal performance:")
    print(f"  U coefficient:     {U_actual:.3f} W/(m²·K)")
    print(f"  Heat loss:         {actual_losses['heat_loss_W']:.1f} W")
    print(f"  Daily loss:        {actual_losses['heat_loss_daily_kWh']:.2f} kWh/day")
    print(f"  Percentage:        {(actual_losses['heat_loss_daily_kWh'] / (energy_stored/3.6e6)) * 100:.2f}% of stored energy")
    
    status = "✓ MEETS TARGET" if actual_losses['heat_loss_W'] < target_loss_W * 1.1 else "⚠ EXCEEDS TARGET"
    print(f"  Status:            {status}")
    
    # External dimensions with insulation
    D_with_insulation = geometry['diameter_internal_m'] + 2 * (thickness_practical / 1000)
    H_with_insulation = geometry['height_internal_m'] + 2 * (thickness_practical / 1000)
    
    print(f"\nFinal external dimensions (with insulation):")
    print(f"  Diameter:          {D_with_insulation:.3f} m = {D_with_insulation*1000:.0f} mm")
    print(f"  Height:            {H_with_insulation:.3f} m = {H_with_insulation*1000:.0f} mm")
    
    return {
        'material': 'mineral_wool',
        'thickness_mm': thickness_practical,
        'U_coefficient': U_actual,
        'heat_loss_W': actual_losses['heat_loss_W'],
        'heat_loss_daily_kWh': actual_losses['heat_loss_daily_kWh'],
        'diameter_with_insulation_m': D_with_insulation,
        'height_with_insulation_m': H_with_insulation,
        'jacket': 'Aluminum 0.5 mm'
    }


def design_connections(storage_req: dict, geometry: dict):
    """
    Design tank connections (inlets/outlets).
    
    Parameters
    ----------
    storage_req : dict
        Storage requirements
    geometry : dict
        Tank geometry
    
    Returns
    -------
    dict
        Connection specifications
    """
    
    print("\n" + "="*70)
    print("TANK CONNECTIONS DESIGN")
    print("="*70)
    
    print(f"\nConnection philosophy:")
    print(f"  Strategy:          Maintain thermal stratification")
    print(f"  Hot inlet:         Top of tank (from compressors)")
    print(f"  Cold outlet:       Bottom of tank (return to compressors)")
    print(f"  Secondary hot:     Top (to industrial water HX)")
    print(f"  Secondary cold:    Bottom (from industrial water HX)")
    
    # Primary circuit (compressor loop)
    flow_primary = storage_req['design_flow_m3h']
    
    print(f"\n" + "-"*70)
    print("PRIMARY CIRCUIT (Compressor Loop)")
    print("-"*70)
    
    primary_inlet = st.connection_sizing(flow_primary, target_velocity=1.5)
    
    print(f"\nHot inlet (top):")
    print(f"  Flow rate:         {primary_inlet['flow_rate_m3h']:.2f} m³/h")
    print(f"  Selected size:     DN{primary_inlet['selected_DN']}")
    print(f"  Velocity:          {primary_inlet['actual_velocity_ms']:.2f} m/s")
    print(f"  Type:              Radial diffuser (reduce velocity)")
    
    primary_outlet = st.connection_sizing(flow_primary, target_velocity=1.5)
    
    print(f"\nCold outlet (bottom):")
    print(f"  Flow rate:         {primary_outlet['flow_rate_m3h']:.2f} m³/h")
    print(f"  Selected size:     DN{primary_outlet['selected_DN']}")
    print(f"  Velocity:          {primary_outlet['actual_velocity_ms']:.2f} m/s")
    print(f"  Type:              Direct connection")
    
    # Secondary circuit (to industrial water)
    # Assume similar flow for heat exchange
    flow_secondary = flow_primary  # Can be different in practice
    
    print(f"\n" + "-"*70)
    print("SECONDARY CIRCUIT (Industrial Water)")
    print("-"*70)
    
    secondary_outlet = st.connection_sizing(flow_secondary, target_velocity=1.5)
    
    print(f"\nHot outlet (top):")
    print(f"  Flow rate:         {secondary_outlet['flow_rate_m3h']:.2f} m³/h")
    print(f"  Selected size:     DN{secondary_outlet['selected_DN']}")
    print(f"  Velocity:          {secondary_outlet['actual_velocity_ms']:.2f} m/s")
    
    secondary_inlet = st.connection_sizing(flow_secondary, target_velocity=1.5)
    
    print(f"\nCold return (bottom):")
    print(f"  Flow rate:         {secondary_inlet['flow_rate_m3h']:.2f} m³/h")
    print(f"  Selected size:     DN{secondary_inlet['selected_DN']}")
    print(f"  Velocity:          {secondary_inlet['actual_velocity_ms']:.2f} m/s")
    
    # Verify stratification with Richardson number
    print(f"\n" + "-"*70)
    print("STRATIFICATION ANALYSIS")
    print("-"*70)
    
    # Use inlet velocity and tank height
    v_inlet = primary_inlet['actual_velocity_ms']
    H_tank = geometry['height_internal_m']
    delta_T_strat = storage_req['delta_T']
    
    Ri = st.richardson_number(delta_T_strat, H_tank, v_inlet)
    quality = st.stratification_quality(Ri)
    
    print(f"\nRichardson number analysis:")
    print(f"  Inlet velocity:    {v_inlet:.2f} m/s")
    print(f"  Tank height:       {H_tank:.2f} m")
    print(f"  Delta T:           {delta_T_strat} K")
    print(f"  Richardson (Ri):   {Ri:.1f}")
    print(f"  Assessment:        {quality}")
    
    if Ri < 5:
        print(f"\n  ⚠ WARNING: Low Ri indicates potential mixing")
        print(f"  → Recommendation: Add flow diffusers at inlets")
        print(f"  → Recommendation: Consider perforated distribution pipes")
    
    # Additional connections
    print(f"\n" + "-"*70)
    print("AUXILIARY CONNECTIONS")
    print("-"*70)
    
    print(f"\nRequired auxiliary connections:")
    print(f"  □ Drain (bottom):       DN25 with full-port ball valve")
    print(f"  □ Vent (top):           DN15 automatic air vent")
    print(f"  □ Pressure relief:      DN25, set at 3.0 bar")
    print(f"  □ Pressure gauge (top): 0-4 bar, glycerin-filled")
    print(f"  □ Thermometer (top):    0-100°C")
    print(f"  □ Thermometer (mid):    0-100°C")
    print(f"  □ Thermometer (bottom): 0-100°C")
    print(f"  □ Level indicator:      Sight glass or float type")
    print(f"  □ Manway (optional):    DN450 for inspection/cleaning")
    
    return {
        'primary_circuit': {
            'hot_inlet': primary_inlet,
            'cold_outlet': primary_outlet
        },
        'secondary_circuit': {
            'hot_outlet': secondary_outlet,
            'cold_inlet': secondary_inlet
        },
        'stratification': {
            'richardson_number': Ri,
            'quality': quality
        }
    }


def estimate_costs(geometry: dict, pressure_vessel: dict, insulation: dict):
    """
    Estimate tank costs.
    
    Parameters
    ----------
    geometry : dict
        Tank geometry
    pressure_vessel : dict
        Pressure vessel design
    insulation : dict
        Insulation design
    
    Returns
    -------
    dict
        Cost breakdown
    """
    
    print("\n" + "="*70)
    print("COST ESTIMATION")
    print("="*70)
    
    print(f"\nNote: Costs are rough estimates for budgeting purposes.")
    print(f"Obtain formal quotations from tank manufacturers.\n")
    
    # Tank fabrication cost (CLP)
    # Rough estimate: 1,200,000 CLP/m³ for custom fabricated tanks
    volume = geometry['volume_m3']
    cost_tank = volume * 1_200_000
    
    # Insulation cost (CLP)
    # Rough estimate: 35,000 CLP/m² for 75mm mineral wool + aluminum jacket
    area_external = geometry['surface_areas']['total'] * 1.2  # Account for external diameter
    cost_insulation = area_external * 35_000
    
    # Connections and accessories (CLP)
    cost_connections = 800_000  # Flanges, nozzles, etc.
    
    # Painting and surface preparation
    cost_painting = 150_000
    
    # Stand/supports
    cost_support = 400_000
    
    # Installation (approximate)
    cost_installation = (cost_tank + cost_insulation) * 0.25  # 25% of material
    
    # Total
    cost_total = (cost_tank + cost_insulation + cost_connections + 
                  cost_painting + cost_support + cost_installation)
    
    print(f"{'Item':<30} {'Cost [CLP]':>15}")
    print("-"*70)
    print(f"{'Tank fabrication':<30} ${cost_tank:>14,.0f}")
    print(f"{'Insulation + jacket':<30} ${cost_insulation:>14,.0f}")
    print(f"{'Connections & accessories':<30} ${cost_connections:>14,.0f}")
    print(f"{'Painting & coating':<30} ${cost_painting:>14,.0f}")
    print(f"{'Support structure':<30} ${cost_support:>14,.0f}")
    print(f"{'Installation & testing':<30} ${cost_installation:>14,.0f}")
    print("-"*70)
    print(f"{'TOTAL ESTIMATED COST':<30} ${cost_total:>14,.0f}")
    print("="*70)
    
    print(f"\nExcludes:")
    print(f"  - Engineering and design services")
    print(f"  - Freight and handling")
    print(f"  - Site preparation (foundation, etc.)")
    print(f"  - Piping connections to/from tank")
    print(f"  - Control instrumentation")
    
    return {
        'tank_fabrication': cost_tank,
        'insulation': cost_insulation,
        'connections': cost_connections,
        'painting': cost_painting,
        'support': cost_support,
        'installation': cost_installation,
        'total': cost_total
    }


def plot_tank_design(geometry: dict, storage_req: dict, connections: dict):
    """Create visualization of tank design."""
    
    fig = plt.figure(figsize=(14, 10))
    
    # Create 2x2 subplot layout
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Plot 1: Tank schematic
    D = geometry['diameter_internal_m']
    H = geometry['height_internal_m']
    
    # Draw tank
    rect = plt.Rectangle((-D/2, 0), D, H, fill=False, edgecolor='black', linewidth=2)
    ax1.add_patch(rect)
    
    # Draw stratification layers
    num_layers = 5
    layer_height = H / num_layers
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, num_layers))
    
    for i in range(num_layers):
        y = i * layer_height
        layer = plt.Rectangle((-D/2, y), D, layer_height, 
                             facecolor=colors[i], alpha=0.6, edgecolor='gray', linewidth=0.5)
        ax1.add_patch(layer)
    
    # Mark connections
    ax1.plot(-D/2-0.1, H-0.1, 'r>', markersize=15, label='Hot inlet (top)')
    ax1.plot(D/2+0.1, 0.1, 'b<', markersize=15, label='Cold outlet (bottom)')
    
    # Annotations
    ax1.annotate(f'D = {D:.2f} m', xy=(0, -0.15), ha='center', fontsize=10, fontweight='bold')
    ax1.annotate(f'H = {H:.2f} m', xy=(D/2+0.3, H/2), rotation=90, va='center', 
                fontsize=10, fontweight='bold')
    ax1.annotate(f'V = {geometry["volume_m3"]:.2f} m³', xy=(0, H+0.2), ha='center',
                fontsize=11, fontweight='bold', bbox=dict(boxstyle='round', facecolor='wheat'))
    
    ax1.set_xlim(-D/2-0.5, D/2+0.5)
    ax1.set_ylim(-0.3, H+0.4)
    ax1.set_aspect('equal')
    ax1.set_xlabel('Diameter [m]', fontsize=10)
    ax1.set_ylabel('Height [m]', fontsize=10)
    ax1.set_title('Tank Schematic with Thermal Stratification', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9, loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Temperature profile
    heights = np.linspace(0, H, 100)
    # Simplified stratification profile
    T_bottom = storage_req['T_return']
    T_top = storage_req['T_supply']
    # Exponential-like profile for realistic stratification
    temps = T_bottom + (T_top - T_bottom) * (heights / H)**1.5
    
    ax2.plot(temps, heights, 'r-', linewidth=2.5)
    ax2.axhline(H, color='red', linestyle='--', alpha=0.5, label=f'Hot layer: {T_top}°C')
    ax2.axhline(0, color='blue', linestyle='--', alpha=0.5, label=f'Cold layer: {T_bottom}°C')
    ax2.fill_betweenx(heights, T_bottom, temps, alpha=0.3, color='orange')
    
    ax2.set_xlabel('Temperature [°C]', fontsize=10)
    ax2.set_ylabel('Height [m]', fontsize=10)
    ax2.set_title('Vertical Temperature Profile (Stratified)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(T_bottom-5, T_top+5)
    
    # Plot 3: Energy storage vs time
    times = np.array([5, 10, 15, 20, 30, 45, 60])  # minutes
    volumes = []
    for t in times:
        V = st.required_volume(storage_req['design_power_W'], t/60, storage_req['delta_T'])
        volumes.append(V)
    
    ax3.plot(times, volumes, 'go-', linewidth=2, markersize=8)
    ax3.axvline(15, color='red', linestyle='--', linewidth=2, label='Recommended (15 min)')
    ax3.axhline(geometry['volume_m3'], color='blue', linestyle='--', linewidth=2, 
               label=f'Selected: {geometry["volume_m3"]:.2f} m³')
    
    ax3.set_xlabel('Storage Time [minutes]', fontsize=10)
    ax3.set_ylabel('Required Volume [m³]', fontsize=10)
    ax3.set_title('Volume vs Storage Time', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Stratification quality (Richardson number)
    velocities = np.linspace(0.2, 3.0, 50)
    Ri_values = []
    for v in velocities:
        Ri = st.richardson_number(storage_req['delta_T'], H, v)
        Ri_values.append(Ri)
    
    ax4.plot(velocities, Ri_values, 'b-', linewidth=2.5)
    ax4.axhline(10, color='green', linestyle='--', linewidth=2, label='Excellent (Ri > 10)')
    ax4.axhline(1, color='orange', linestyle='--', linewidth=2, label='Minimum (Ri > 1)')
    
    # Mark design point
    v_design = connections['primary_circuit']['hot_inlet']['actual_velocity_ms']
    Ri_design = connections['stratification']['richardson_number']
    ax4.plot(v_design, Ri_design, 'ro', markersize=12, label=f'Design: Ri = {Ri_design:.1f}')
    
    ax4.set_xlabel('Inlet Velocity [m/s]', fontsize=10)
    ax4.set_ylabel('Richardson Number', fontsize=10)
    ax4.set_title('Stratification Quality vs Inlet Velocity', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.set_yscale('log')
    ax4.set_ylim(0.1, 100)
    
    # Save figure
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'storage_tank_design.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {output_dir / 'storage_tank_design.png'}")
    
    return fig


def generate_storage_report(storage_req, geometry, pressure_vessel, 
                           insulation, connections, costs):
    """Generate comprehensive storage tank design report."""
    
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / 'storage_tank_report.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("CMPC HEAT RECOVERY SYSTEM - THERMAL STORAGE TANK DESIGN\n")
        f.write("="*70 + "\n\n")
        
        f.write("PROJECT INFORMATION\n")
        f.write("-"*70 + "\n")
        f.write("Client: Papeles Cordillera S.A. (CMPC Puente Alto)\n")
        f.write("System: Heat Recovery Thermal Storage Accumulator\n")
        f.write("Design Code: ASME Section VIII Division 1\n\n")
        
        f.write("="*70 + "\n")
        f.write("STORAGE REQUIREMENTS\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Thermal power:        {storage_req['design_power_W']/1000:.0f} kW\n")
        f.write(f"Storage time:         {storage_req['storage_time_hours']*60:.0f} minutes\n")
        f.write(f"Operating temps:      {storage_req['T_return']}°C - {storage_req['T_supply']}°C\n")
        f.write(f"Delta T:              {storage_req['delta_T']} K\n")
        f.write(f"Energy capacity:      {storage_req['energy_stored_MJ']:.2f} MJ\n\n")
        
        f.write("="*70 + "\n")
        f.write("TANK DIMENSIONS\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Volume:               {geometry['volume_m3']:.3f} m³ ({geometry['volume_m3']*1000:.0f} liters)\n")
        f.write(f"Internal diameter:    {geometry['diameter_internal_mm']:.0f} mm\n")
        f.write(f"Internal height:      {geometry['height_internal_mm']:.0f} mm\n")
        f.write(f"H/D ratio:            {geometry['H_D_ratio']:.1f}\n")
        f.write(f"Surface area:         {geometry['surface_areas']['total']:.2f} m²\n\n")
        
        f.write("="*70 + "\n")
        f.write("PRESSURE VESSEL DESIGN\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Design pressure:      {pressure_vessel['design_pressure_bar']} bar (gauge)\n")
        f.write(f"Design temperature:   {pressure_vessel['design_temperature_C']}°C\n")
        f.write(f"Material:             {pressure_vessel['material']}\n")
        f.write(f"Wall thickness:       {pressure_vessel['wall_thickness_mm']} mm\n")
        f.write(f"External diameter:    {pressure_vessel['diameter_external_m']*1000:.0f} mm\n")
        f.write(f"Weight (empty):       {pressure_vessel['weight_empty_kg']:.0f} kg\n")
        f.write(f"Weight (full):        {pressure_vessel['weight_full_kg']:.0f} kg\n\n")
        
        f.write("="*70 + "\n")
        f.write("THERMAL INSULATION\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Material:             {insulation['material'].replace('_', ' ').title()}\n")
        f.write(f"Thickness:            {insulation['thickness_mm']} mm\n")
        f.write(f"Jacket:               {insulation['jacket']}\n")
        f.write(f"Heat loss:            {insulation['heat_loss_W']:.1f} W\n")
        f.write(f"Daily loss:           {insulation['heat_loss_daily_kWh']:.2f} kWh\n")
        f.write(f"U coefficient:        {insulation['U_coefficient']:.3f} W/(m²·K)\n")
        f.write(f"Final dimensions:     {insulation['diameter_with_insulation_m']*1000:.0f} mm × ")
        f.write(f"{insulation['height_with_insulation_m']*1000:.0f} mm\n\n")
        
        f.write("="*70 + "\n")
        f.write("CONNECTIONS\n")
        f.write("="*70 + "\n\n")
        
        f.write("Primary circuit (compressor loop):\n")
        f.write(f"  Hot inlet (top):      DN{connections['primary_circuit']['hot_inlet']['selected_DN']} ")
        f.write(f"@ {connections['primary_circuit']['hot_inlet']['actual_velocity_ms']:.2f} m/s\n")
        f.write(f"  Cold outlet (bottom): DN{connections['primary_circuit']['cold_outlet']['selected_DN']} ")
        f.write(f"@ {connections['primary_circuit']['cold_outlet']['actual_velocity_ms']:.2f} m/s\n\n")
        
        f.write("Secondary circuit (industrial water):\n")
        f.write(f"  Hot outlet (top):     DN{connections['secondary_circuit']['hot_outlet']['selected_DN']} ")
        f.write(f"@ {connections['secondary_circuit']['hot_outlet']['actual_velocity_ms']:.2f} m/s\n")
        f.write(f"  Cold inlet (bottom):  DN{connections['secondary_circuit']['cold_inlet']['selected_DN']} ")
        f.write(f"@ {connections['secondary_circuit']['cold_inlet']['actual_velocity_ms']:.2f} m/s\n\n")
        
        f.write("Stratification quality:\n")
        f.write(f"  Richardson number:    {connections['stratification']['richardson_number']:.1f}\n")
        f.write(f"  Assessment:           {connections['stratification']['quality']}\n\n")
        
        f.write("="*70 + "\n")
        f.write("COST ESTIMATE\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Tank fabrication:     ${costs['tank_fabrication']:,.0f} CLP\n")
        f.write(f"Insulation:           ${costs['insulation']:,.0f} CLP\n")
        f.write(f"Connections:          ${costs['connections']:,.0f} CLP\n")
        f.write(f"Painting:             ${costs['painting']:,.0f} CLP\n")
        f.write(f"Support:              ${costs['support']:,.0f} CLP\n")
        f.write(f"Installation:         ${costs['installation']:,.0f} CLP\n")
        f.write(f"{'-'*70}\n")
        f.write(f"TOTAL:                ${costs['total']:,.0f} CLP\n\n")
        
        f.write("="*70 + "\n")
        f.write("FABRICATION NOTES\n")
        f.write("="*70 + "\n\n")
        
        f.write("1. MATERIALS:\n")
        f.write("   - Shell: Carbon steel ASTM A36\n")
        f.write("   - Heads: ASME F&D or elliptical\n")
        f.write("   - Nozzles: ASTM A105 forgings\n")
        f.write("   - Flanges: ASME B16.5 Class 150 RF\n\n")
        
        f.write("2. FABRICATION:\n")
        f.write("   - Welding: SMAW or GMAW per ASME Section IX\n")
        f.write("   - Radiography: Spot RT per ASME Section VIII\n")
        f.write("   - Hydrostatic test: 1.5× design pressure\n")
        f.write("   - Painting: Shop primer + epoxy finish\n\n")
        
        f.write("3. INSTALLATION:\n")
        f.write("   - Foundation: Reinforced concrete pad\n")
        f.write("   - Supports: Four legs with anchor bolts\n")
        f.write("   - Access: Provide clearance for maintenance\n")
        f.write("   - Insulation: Install after pressure test\n\n")
        
        f.write("4. ACCESSORIES:\n")
        f.write("   - Pressure relief valve: Set at 3.0 bar\n")
        f.write("   - Automatic air vent (top)\n")
        f.write("   - Drain valve (bottom)\n")
        f.write("   - Pressure gauge (0-4 bar)\n")
        f.write("   - Temperature sensors (3 points)\n")
        f.write("   - Level indicator\n\n")
        
        f.write("="*70 + "\n")
        f.write("NEXT STEPS\n")
        f.write("="*70 + "\n\n")
        
        f.write("[ ] Obtain quotations from tank fabricators\n")
        f.write("[ ] Finalize P&ID with connections\n")
        f.write("[ ] Design intermediate heat exchanger (05_heat_exchanger.py)\n")
        f.write("[ ] Prepare foundation design\n")
        f.write("[ ] Develop commissioning procedure\n\n")
        
        f.write("="*70 + "\n")
        f.write(f"Report generated by: Felipe Wasaff\n")
        f.write(f"Script: 04_storage_design.py\n")
        f.write("="*70 + "\n")
    
    print(f"\n✓ Report saved: {report_path}")


def main():
    """Main execution function."""
    
    print("\n" + "="*70)
    print("CMPC HEAT RECOVERY SYSTEM - THERMAL STORAGE TANK DESIGN")
    print("="*70)
    print("\nDesigning thermal accumulator tank...")
    print("Includes: volume, geometry, insulation, connections, stratification\n")
    
    # Load data
    compressor_data, scenario_data = load_project_data()
    
    # Determine storage requirements
    storage_req = determine_storage_requirements(scenario_data)
    
    # Design tank geometry
    geometry = design_tank_geometry(storage_req['volume_design_m3'])
    
    # Design pressure vessel
    pressure_vessel = design_pressure_vessel(geometry)
    
    # Design insulation
    insulation = design_insulation(geometry, storage_req)
    
    # Design connections
    connections = design_connections(storage_req, geometry)
    
    # Estimate costs
    costs = estimate_costs(geometry, pressure_vessel, insulation)
    
    # Generate visualizations
    plot_tank_design(geometry, storage_req, connections)
    
    # Generate report
    generate_storage_report(storage_req, geometry, pressure_vessel, 
                          insulation, connections, costs)
    
    print("\n" + "="*70)
    print("STORAGE TANK DESIGN COMPLETE")
    print("="*70)
    print("\nKey Results:")
    print(f"  → Volume: {geometry['volume_m3']:.2f} m³ (15 min storage)")
    print(f"  → Dimensions: {geometry['diameter_internal_mm']:.0f}mm × {geometry['height_internal_mm']:.0f}mm (H/D = 2.5)")
    print(f"  → Insulation: 75mm mineral wool")
    print(f"  → Stratification: Ri = {connections['stratification']['richardson_number']:.1f} ({connections['stratification']['quality']})")
    print(f"  → Estimated cost: ${costs['total']:,.0f} CLP")
    print("\nNext: Run 05_heat_exchanger.py to design intermediate heat exchanger")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
