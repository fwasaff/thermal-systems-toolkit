"""
CMPC Heat Recovery System - Heat Exchanger Design
=================================================

This script designs the intermediate heat exchanger that separates the
compressor heat recovery loop from the industrial water system.

Design includes:
- Heat duty and temperature profile analysis
- LMTD and ε-NTU calculations
- Technology comparison (plate vs shell-tube)
- Commercial unit selection
- Pressure drop verification
- Material specification

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

from thermal_toolkit import heat_exchangers as hx
from thermal_toolkit import heat_transfer as ht
from thermal_toolkit import fluid_flow as ff
from thermal_toolkit import pumps as pm


def load_project_data():
    """Load project specifications."""
    data_dir = Path(__file__).parent / 'data'
    
    with open(data_dir / 'compressor_specs.json', 'r') as f:
        compressor_data = json.load(f)
    
    with open(data_dir / 'operating_scenarios.json', 'r') as f:
        scenario_data = json.load(f)
    
    return compressor_data, scenario_data


def define_heat_exchanger_requirements(scenario_data):
    """
    Define heat exchanger requirements.
    
    Returns
    -------
    dict
        Heat exchanger requirements
    """
    
    print("\n" + "="*70)
    print("HEAT EXCHANGER REQUIREMENTS")
    print("="*70)
    
    design = scenario_data['design_conditions']
    
    # Heat duty
    Q_design = design['design_thermal_power_kW'] * 1000  # W
    Q_max = design['maximum_thermal_power_kW'] * 1000  # W
    
    print(f"\nHeat duty:")
    print(f"  Design (80%):     {Q_design/1000:.0f} kW")
    print(f"  Maximum (2%):     {Q_max/1000:.0f} kW")
    
    # HOT SIDE (Compressor circuit - closed loop)
    print(f"\n" + "-"*70)
    print("HOT SIDE: Compressor Heat Recovery Circuit")
    print("-"*70)
    
    T_hot_in = 65   # °C (from compressor heat exchangers)
    T_hot_out = 45  # °C (return to compressors)
    delta_T_hot = T_hot_in - T_hot_out
    
    # Flow rate from heat balance: Q = m·cp·ΔT
    m_hot = Q_design / (ht.WATER_CP * delta_T_hot)
    flow_hot_m3h = (m_hot / ht.WATER_RHO) * 3600
    
    print(f"\nTemperatures:")
    print(f"  Inlet:            {T_hot_in}°C")
    print(f"  Outlet:           {T_hot_out}°C")
    print(f"  Delta T:          {delta_T_hot} K")
    
    print(f"\nFlow rate:")
    print(f"  Mass flow:        {m_hot:.2f} kg/s")
    print(f"  Volumetric flow:  {flow_hot_m3h:.2f} m³/h")
    
    # COLD SIDE (Industrial water - open loop)
    print(f"\n" + "-"*70)
    print("COLD SIDE: Industrial Water Supply")
    print("-"*70)
    
    # Industrial water specs from original requirements
    T_cold_in_min = 6   # °C (winter)
    T_cold_in_max = 16  # °C (summer)
    T_cold_in_design = 11  # °C (average for design)
    
    # Target outlet temperature (limit to avoid scaling/fouling)
    T_cold_out = 35  # °C (reasonable for industrial water)
    
    delta_T_cold = T_cold_out - T_cold_in_design
    
    # Required cold side flow from heat balance
    m_cold = Q_design / (ht.WATER_CP * delta_T_cold)
    flow_cold_m3h = (m_cold / ht.WATER_RHO) * 3600
    
    print(f"\nTemperatures:")
    print(f"  Inlet (winter):   {T_cold_in_min}°C")
    print(f"  Inlet (summer):   {T_cold_in_max}°C")
    print(f"  Inlet (design):   {T_cold_in_design}°C")
    print(f"  Outlet (target):  {T_cold_out}°C")
    print(f"  Delta T:          {delta_T_cold} K")
    
    print(f"\nFlow rate:")
    print(f"  Mass flow:        {m_cold:.2f} kg/s")
    print(f"  Volumetric flow:  {flow_cold_m3h:.2f} m³/h")
    
    # Operating conditions
    print(f"\n" + "-"*70)
    print("OPERATING CONDITIONS")
    print("-"*70)
    
    P_hot_design = 2.0  # bar (closed loop, pressurized)
    P_cold_available = 4.0  # bar (industrial water supply)
    
    print(f"\nPressure:")
    print(f"  Hot side:         {P_hot_design} bar")
    print(f"  Cold side avail:  {P_cold_available} bar")
    print(f"  Max ΔP allowed:   0.5 bar each side")
    
    # Temperature approach
    print(f"\n" + "-"*70)
    print("TEMPERATURE PROFILE ANALYSIS")
    print("-"*70)
    
    # Check temperature approach (pinch point)
    approach_hot_end = T_hot_out - T_cold_in_design
    approach_cold_end = T_hot_in - T_cold_out
    min_approach = min(approach_hot_end, approach_cold_end)
    
    print(f"\nTemperature approaches:")
    print(f"  Hot end:          {approach_hot_end:.1f} K ({T_hot_out}°C - {T_cold_in_design}°C)")
    print(f"  Cold end:         {approach_cold_end:.1f} K ({T_hot_in}°C - {T_cold_out}°C)")
    print(f"  Minimum approach: {min_approach:.1f} K")
    
    if min_approach < 5:
        print(f"  ⚠ WARNING: Approach < 5K may be uneconomical")
    else:
        print(f"  ✓ Good approach temperature")
    
    return {
        'Q_design_W': Q_design,
        'Q_design_kW': Q_design / 1000,
        'Q_max_W': Q_max,
        'Q_max_kW': Q_max / 1000,
        'hot_side': {
            'T_in': T_hot_in,
            'T_out': T_hot_out,
            'delta_T': delta_T_hot,
            'mass_flow_kg_s': m_hot,
            'volumetric_flow_m3h': flow_hot_m3h,
            'pressure_bar': P_hot_design
        },
        'cold_side': {
            'T_in_min': T_cold_in_min,
            'T_in_max': T_cold_in_max,
            'T_in_design': T_cold_in_design,
            'T_out': T_cold_out,
            'delta_T': delta_T_cold,
            'mass_flow_kg_s': m_cold,
            'volumetric_flow_m3h': flow_cold_m3h,
            'pressure_bar': P_cold_available
        },
        'approach_min_K': min_approach
    }


def calculate_lmtd_and_area(requirements: dict):
    """
    Calculate LMTD and required area.
    
    Parameters
    ----------
    requirements : dict
        Heat exchanger requirements
    
    Returns
    -------
    dict
        LMTD and area calculations
    """
    
    print("\n" + "="*70)
    print("LMTD AND AREA CALCULATION")
    print("="*70)
    
    # Extract temperatures
    T_hot_in = requirements['hot_side']['T_in']
    T_hot_out = requirements['hot_side']['T_out']
    T_cold_in = requirements['cold_side']['T_in_design']
    T_cold_out = requirements['cold_side']['T_out']
    Q = requirements['Q_design_W']
    
    # Calculate LMTD
    LMTD = hx.lmtd_counterflow(T_hot_in, T_hot_out, T_cold_in, T_cold_out)
    
    print(f"\nTemperature profile (counterflow):")
    print(f"  Hot in:           {T_hot_in}°C  ──→  {T_hot_out}°C")
    print(f"  Cold out:         {T_cold_out}°C ←──  {T_cold_in}°C")
    print(f"\n  ΔT₁ (hot in - cold out):  {T_hot_in - T_cold_out:.1f} K")
    print(f"  ΔT₂ (hot out - cold in):  {T_hot_out - T_cold_in:.1f} K")
    print(f"  LMTD:                     {LMTD:.2f} K")
    
    # Calculate required area for different U values
    print(f"\n" + "-"*70)
    print("AREA REQUIREMENTS vs U COEFFICIENT")
    print("-"*70)
    
    U_values = {
        'Plate HX (excellent)': 5000,
        'Plate HX (good)': 4000,
        'Plate HX (average)': 3000,
        'Shell-tube (good)': 1200,
        'Shell-tube (average)': 1000,
        'Shell-tube (poor)': 800
    }
    
    print(f"\n{'Type':<25} {'U [W/m²·K]':<15} {'Area [m²]':<12}")
    print("-"*70)
    
    area_results = {}
    for type_name, U in U_values.items():
        A = hx.required_area_lmtd(Q, U, LMTD)
        area_results[type_name] = {'U': U, 'A': A}
        print(f"{type_name:<25} {U:<15} {A:<12.2f}")
    
    return {
        'LMTD': LMTD,
        'Q_W': Q,
        'area_results': area_results
    }


def compare_technologies(requirements: dict):
    """
    Compare plate vs shell-tube heat exchangers.
    
    Parameters
    ----------
    requirements : dict
        Heat exchanger requirements
    
    Returns
    -------
    dict
        Technology comparison
    """
    
    print("\n" + "="*70)
    print("TECHNOLOGY COMPARISON")
    print("="*70)
    
    Q = requirements['Q_design_W']
    m_hot = requirements['hot_side']['mass_flow_kg_s']
    m_cold = requirements['cold_side']['mass_flow_kg_s']
    T_hot_in = requirements['hot_side']['T_in']
    T_hot_out = requirements['hot_side']['T_out']
    T_cold_in = requirements['cold_side']['T_in_design']
    T_cold_out = requirements['cold_side']['T_out']
    
    # Compare designs
    comparison = hx.compare_heat_exchanger_types(
        Q, m_hot, m_cold,
        T_hot_in, T_hot_out,
        T_cold_in, T_cold_out
    )
    
    # PLATE HEAT EXCHANGER
    print(f"\n" + "-"*70)
    print("OPTION A: PLATE HEAT EXCHANGER (Brazed or Gasketed)")
    print("-"*70)
    
    plate = comparison['plate']
    
    print(f"\nPerformance:")
    print(f"  Heat duty:        {plate['heat_duty_kW']:.1f} kW")
    print(f"  LMTD:             {plate['LMTD']:.2f} K")
    print(f"  U coefficient:    {plate['U_coefficient']:.0f} W/(m²·K)")
    print(f"  Area required:    {plate['area_required_m2']:.2f} m²")
    print(f"  Effectiveness:    {plate['effectiveness']:.3f} ({plate['effectiveness']*100:.1f}%)")
    print(f"  NTU:              {plate['NTU']:.2f}")
    
    print(f"\nConfiguration:")
    print(f"  Estimated plates: {plate['num_plates_estimated']}")
    print(f"  Plate area:       {plate['plate_area_typical_m2']:.2f} m² each")
    
    # Estimate pressure drop
    flow_m3s = requirements['hot_side']['volumetric_flow_m3h'] / 3600
    dP_plate = hx.pressure_drop_plate_hx(flow_m3s, plate['num_plates_estimated'])
    
    print(f"\nPressure drop (estimated):")
    print(f"  Hot side:         {dP_plate/1000:.1f} kPa")
    print(f"  Cold side:        {dP_plate/1000:.1f} kPa (similar)")
    
    print(f"\nAdvantages:")
    print(f"  ✓ Compact size (small footprint)")
    print(f"  ✓ High heat transfer efficiency (U = 4000-5000)")
    print(f"  ✓ Easy to clean (removable plates)")
    print(f"  ✓ Easy to expand (add plates)")
    print(f"  ✓ Lower cost for this duty")
    print(f"  ✓ True counterflow arrangement")
    
    print(f"\nDisadvantages:")
    print(f"  ✗ Gasket maintenance required (if gasketed)")
    print(f"  ✗ Limited to ~25 bar, 180°C (typically)")
    print(f"  ✗ Requires clean fluids (no particles)")
    
    # SHELL-AND-TUBE
    print(f"\n" + "-"*70)
    print("OPTION B: SHELL-AND-TUBE HEAT EXCHANGER")
    print("-"*70)
    
    tube = comparison['shell_tube']
    
    print(f"\nPerformance:")
    print(f"  Heat duty:        {tube['heat_duty_kW']:.1f} kW")
    print(f"  LMTD:             {tube['LMTD']:.2f} K")
    print(f"  U coefficient:    {tube['U_coefficient']:.0f} W/(m²·K)")
    print(f"  Area required:    {tube['area_required_m2']:.2f} m²")
    print(f"  Effectiveness:    {tube['effectiveness']:.3f} ({tube['effectiveness']*100:.1f}%)")
    print(f"  NTU:              {tube['NTU']:.2f}")
    
    print(f"\nConfiguration:")
    print(f"  Estimated tubes:  {tube['num_tubes_estimated']}")
    print(f"  Tube area:        ~0.08 m² each")
    
    print(f"\nAdvantages:")
    print(f"  ✓ Robust construction")
    print(f"  ✓ High pressure/temperature capability")
    print(f"  ✓ Can handle fouling fluids")
    print(f"  ✓ Long service life")
    print(f"  ✓ No gaskets (welded construction)")
    
    print(f"\nDisadvantages:")
    print(f"  ✗ Much larger size ({comparison['area_ratio']:.1f}× more area)")
    print(f"  ✗ Higher cost")
    print(f"  ✗ Difficult to clean (requires removal)")
    print(f"  ✗ Lower thermal efficiency")
    print(f"  ✗ Not true counterflow (unless multi-pass)")
    
    # RECOMMENDATION
    print(f"\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    print(f"\nFor CMPC system, recommend: PLATE HEAT EXCHANGER")
    print(f"\nRationale:")
    print(f"  1. Moderate duty ({plate['heat_duty_kW']:.0f} kW) well-suited for plates")
    print(f"  2. Clean fluids on both sides (closed loop + treated water)")
    print(f"  3. Moderate pressures/temperatures (within plate limits)")
    print(f"  4. Compact size important for existing facility")
    print(f"  5. Cost-effective: ~60% less than shell-tube")
    print(f"  6. Easy maintenance with removable plates")
    print(f"  7. Area advantage: {plate['area_required_m2']:.1f} m² vs {tube['area_required_m2']:.1f} m²")
    
    return {
        'comparison': comparison,
        'recommendation': 'plate',
        'dP_estimated_kPa': dP_plate / 1000
    }


def select_commercial_unit(requirements: dict, lmtd_calc: dict):
    """
    Select commercial plate heat exchanger.
    
    Parameters
    ----------
    requirements : dict
        Heat exchanger requirements
    lmtd_calc : dict
        LMTD calculations
    
    Returns
    -------
    dict
        Selected unit
    """
    
    print("\n" + "="*70)
    print("COMMERCIAL UNIT SELECTION")
    print("="*70)
    
    print(f"\nSearching manufacturer catalogs...")
    print(f"Manufacturers considered: Alfa Laval, APV, GEA, SWEP")
    
    # Use plate design with U=4000 (conservative)
    area_required = lmtd_calc['area_results']['Plate HX (good)']['A']
    heat_duty_kW = requirements['Q_design_kW']
    
    print(f"\nDesign requirements:")
    print(f"  Heat duty:        {heat_duty_kW:.1f} kW")
    print(f"  Area required:    {area_required:.2f} m²")
    print(f"  Hot side flow:    {requirements['hot_side']['volumetric_flow_m3h']:.1f} m³/h")
    print(f"  Cold side flow:   {requirements['cold_side']['volumetric_flow_m3h']:.1f} m³/h")
    
    # Select unit
    selected = hx.select_commercial_plate_hx(area_required, heat_duty_kW)
    
    if selected:
        print(f"\n" + "-"*70)
        print("SELECTED UNIT")
        print("-"*70)
        
        specs = selected['specs']
        
        print(f"\nManufacturer:     {specs['manufacturer']}")
        print(f"Model:            {specs['model']}")
        print(f"Number of plates: {selected['num_plates']}")
        print(f"Plate area:       {specs['plate_area_m2']:.2f} m² each")
        print(f"Total area:       {selected['total_area_m2']:.2f} m²")
        print(f"Oversizing:       {(selected['oversizing_factor']-1)*100:.1f}%")
        
        print(f"\nRatings:")
        print(f"  Max heat duty:    {specs['max_heat_duty_kW']} kW")
        print(f"  Max pressure:     {specs['max_pressure_bar']} bar")
        print(f"  Max temperature:  {specs['max_temperature_C']}°C")
        print(f"  U typical:        {specs['U_typical']} W/(m²·K)")
        print(f"  Material:         {specs['material']}")
        
        print(f"\nVerification:")
        actual_U = specs['U_typical']
        actual_A = selected['total_area_m2']
        LMTD = lmtd_calc['LMTD']
        Q_actual = actual_U * actual_A * LMTD
        
        print(f"  Calculated duty:  {Q_actual/1000:.1f} kW")
        print(f"  Required duty:    {heat_duty_kW:.1f} kW")
        print(f"  Margin:           {(Q_actual/1000 - heat_duty_kW)/heat_duty_kW*100:.1f}%")
        
        if Q_actual > requirements['Q_design_W']:
            print(f"  Status:           ✓ ADEQUATE")
        else:
            print(f"  Status:           ⚠ UNDERSIZED")
        
        # Cost estimate
        cost_estimate_usd = 15000 + (selected['num_plates'] * 200)  # Rough estimate
        cost_estimate_clp = cost_estimate_usd * 950  # USD to CLP
        
        print(f"\nCost estimate:")
        print(f"  Unit cost:        ${cost_estimate_usd:,.0f} USD")
        print(f"  Unit cost:        ${cost_estimate_clp:,.0f} CLP")
        print(f"  Note: Obtain formal quotation from distributor")
        
        return {
            'selected': True,
            'manufacturer': specs['manufacturer'],
            'model': specs['model'],
            'num_plates': selected['num_plates'],
            'total_area_m2': selected['total_area_m2'],
            'specs': specs,
            'Q_actual_kW': Q_actual / 1000,
            'margin_percent': (Q_actual/1000 - heat_duty_kW)/heat_duty_kW*100,
            'cost_estimate_clp': cost_estimate_clp
        }
    else:
        print(f"\n⚠ No suitable unit found in database")
        print(f"  Recommendation: Contact manufacturer for custom design")
        return {'selected': False}


def plot_heat_exchanger_analysis(requirements: dict, lmtd_calc: dict):
    """Create visualization of heat exchanger analysis."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Temperature profile
    positions = np.array([0, 1])
    T_hot = np.array([requirements['hot_side']['T_in'], requirements['hot_side']['T_out']])
    T_cold = np.array([requirements['cold_side']['T_in_design'], requirements['cold_side']['T_out']])
    
    ax1.plot(positions, T_hot, 'r-o', linewidth=2.5, markersize=10, label='Hot side (compressor loop)')
    ax1.plot(positions, T_cold, 'b-o', linewidth=2.5, markersize=10, label='Cold side (industrial water)')
    
    # Mark temperatures
    ax1.text(0, T_hot[0]+2, f'{T_hot[0]:.0f}°C', ha='center', fontsize=10, color='red', fontweight='bold')
    ax1.text(1, T_hot[1]+2, f'{T_hot[1]:.0f}°C', ha='center', fontsize=10, color='red', fontweight='bold')
    ax1.text(0, T_cold[0]-2, f'{T_cold[0]:.0f}°C', ha='center', fontsize=10, color='blue', fontweight='bold')
    ax1.text(1, T_cold[1]-2, f'{T_cold[1]:.0f}°C', ha='center', fontsize=10, color='blue', fontweight='bold')
    
    # Shade area between curves
    ax1.fill_between(positions, T_hot, T_cold, alpha=0.3, color='orange', label='ΔT driving force')
    
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(['Inlet', 'Outlet'])
    ax1.set_ylabel('Temperature [°C]', fontsize=11)
    ax1.set_title('Temperature Profile (Counterflow)', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 70)
    
    # Plot 2: Area vs U coefficient
    U_range = np.linspace(1000, 6000, 50)
    areas = []
    for U in U_range:
        A = hx.required_area_lmtd(requirements['Q_design_W'], U, lmtd_calc['LMTD'])
        areas.append(A)
    
    ax2.plot(U_range, areas, 'g-', linewidth=2.5)
    
    # Mark typical values
    ax2.axvspan(3000, 5000, alpha=0.2, color='green', label='Plate HX range')
    ax2.axvspan(800, 1200, alpha=0.2, color='orange', label='Shell-tube range')
    
    ax2.set_xlabel('U Coefficient [W/(m²·K)]', fontsize=11)
    ax2.set_ylabel('Required Area [m²]', fontsize=11)
    ax2.set_title('Heat Transfer Area vs U Coefficient', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Technology comparison (area and cost)
    technologies = ['Plate HX', 'Shell-Tube']
    areas_comp = [
        lmtd_calc['area_results']['Plate HX (good)']['A'],
        lmtd_calc['area_results']['Shell-tube (average)']['A']
    ]
    costs_relative = [1.0, 1.6]  # Relative costs
    
    x = np.arange(len(technologies))
    width = 0.35
    
    bars1 = ax3.bar(x - width/2, areas_comp, width, label='Area [m²]', color='steelblue', alpha=0.7)
    ax3_twin = ax3.twinx()
    bars2 = ax3_twin.bar(x + width/2, costs_relative, width, label='Relative cost', color='coral', alpha=0.7)
    
    ax3.set_xlabel('Technology', fontsize=11)
    ax3.set_ylabel('Required Area [m²]', fontsize=11, color='steelblue')
    ax3_twin.set_ylabel('Relative Cost', fontsize=11, color='coral')
    ax3.set_title('Technology Comparison', fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(technologies)
    ax3.tick_params(axis='y', labelcolor='steelblue')
    ax3_twin.tick_params(axis='y', labelcolor='coral')
    ax3.grid(True, axis='y', alpha=0.3)
    
    # Add values on bars
    for bar in bars1:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f} m²', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 4: Effectiveness vs NTU
    NTU_range = np.linspace(0.1, 5, 100)
    C_ratios = [0.5, 0.8, 1.0]
    colors = ['red', 'blue', 'green']
    
    for C_r, color in zip(C_ratios, colors):
        eff = []
        for NTU in NTU_range:
            epsilon = hx.effectiveness_ntu_counterflow(NTU, C_r)
            eff.append(epsilon)
        ax4.plot(NTU_range, eff, color=color, linewidth=2, label=f'C_ratio = {C_r}')
    
    # Mark design point
    plate = lmtd_calc['area_results']['Plate HX (good)']
    # Calculate design NTU (simplified)
    C_min = min(requirements['hot_side']['mass_flow_kg_s'] * ht.WATER_CP,
                requirements['cold_side']['mass_flow_kg_s'] * ht.WATER_CP)
    NTU_design = (plate['U'] * plate['A']) / C_min
    
    # Calculate effectiveness
    Q_max = C_min * (requirements['hot_side']['T_in'] - requirements['cold_side']['T_in_design'])
    eff_design = requirements['Q_design_W'] / Q_max
    
    ax4.plot(NTU_design, eff_design, 'ko', markersize=12, label='Design point', zorder=5)
    
    ax4.set_xlabel('NTU (Number of Transfer Units)', fontsize=11)
    ax4.set_ylabel('Effectiveness ε', fontsize=11)
    ax4.set_title('ε-NTU Curves (Counterflow)', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 5)
    ax4.set_ylim(0, 1)
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'heat_exchanger_design.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {output_dir / 'heat_exchanger_design.png'}")
    
    return fig


def generate_heat_exchanger_report(requirements, lmtd_calc, comparison, selection):
    """Generate comprehensive heat exchanger design report."""
    
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / 'heat_exchanger_report.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("CMPC HEAT RECOVERY SYSTEM - HEAT EXCHANGER DESIGN\n")
        f.write("="*70 + "\n\n")
        
        f.write("PROJECT INFORMATION\n")
        f.write("-"*70 + "\n")
        f.write("Client: Papeles Cordillera S.A. (CMPC Puente Alto)\n")
        f.write("Function: Intermediate heat exchanger\n")
        f.write("Purpose: Separate compressor loop from industrial water\n\n")
        
        f.write("="*70 + "\n")
        f.write("DESIGN CONDITIONS\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Heat duty:            {requirements['Q_design_kW']:.1f} kW\n")
        f.write(f"LMTD:                 {lmtd_calc['LMTD']:.2f} K\n\n")
        
        f.write("Hot side (compressor circuit):\n")
        f.write(f"  Inlet temperature:  {requirements['hot_side']['T_in']}°C\n")
        f.write(f"  Outlet temperature: {requirements['hot_side']['T_out']}°C\n")
        f.write(f"  Flow rate:          {requirements['hot_side']['volumetric_flow_m3h']:.1f} m³/h\n")
        f.write(f"  Pressure:           {requirements['hot_side']['pressure_bar']} bar\n\n")
        
        f.write("Cold side (industrial water):\n")
        f.write(f"  Inlet temperature:  {requirements['cold_side']['T_in_design']}°C\n")
        f.write(f"  Outlet temperature: {requirements['cold_side']['T_out']}°C\n")
        f.write(f"  Flow rate:          {requirements['cold_side']['volumetric_flow_m3h']:.1f} m³/h\n")
        f.write(f"  Pressure:           {requirements['cold_side']['pressure_bar']} bar\n\n")
        
        f.write("="*70 + "\n")
        f.write("SELECTED CONFIGURATION\n")
        f.write("="*70 + "\n\n")
        
        if selection['selected']:
            f.write(f"Type:                 Plate Heat Exchanger (Gasketed)\n")
            f.write(f"Manufacturer:         {selection['manufacturer']}\n")
            f.write(f"Model:                {selection['model']}\n")
            f.write(f"Number of plates:     {selection['num_plates']}\n")
            f.write(f"Heat transfer area:   {selection['total_area_m2']:.2f} m²\n")
            f.write(f"U coefficient:        {selection['specs']['U_typical']} W/(m²·K)\n")
            f.write(f"Material:             {selection['specs']['material']}\n\n")
            
            f.write("Performance:\n")
            f.write(f"  Actual duty:        {selection['Q_actual_kW']:.1f} kW\n")
            f.write(f"  Design margin:      {selection['margin_percent']:.1f}%\n\n")
        
        f.write("="*70 + "\n")
        f.write("INSTALLATION REQUIREMENTS\n")
        f.write("="*70 + "\n\n")
        
        f.write("Location:\n")
        f.write("  - Install between thermal storage tank and industrial water\n")
        f.write("  - Provide access for plate removal (gasketed type)\n")
        f.write("  - Mounting: Vertical with connections at bottom\n\n")
        
        f.write("Connections:\n")
        f.write("  - Hot inlet/outlet:  DN80 (from/to accumulator)\n")
        f.write("  - Cold inlet/outlet: DN80 (industrial water)\n")
        f.write("  - Isolation valves on all connections\n")
        f.write("  - Pressure gauges on all sides\n")
        f.write("  - Temperature sensors at inlets/outlets\n\n")
        
        f.write("="*70 + "\n")
        f.write("MAINTENANCE SCHEDULE\n")
        f.write("="*70 + "\n\n")
        
        f.write("Monthly:\n")
        f.write("  □ Check pressure drops (indicates fouling)\n")
        f.write("  □ Verify temperatures match design\n")
        f.write("  □ Inspect for external leaks\n\n")
        
        f.write("Annually:\n")
        f.write("  □ Open unit and inspect plates\n")
        f.write("  □ Clean plates (chemical or mechanical)\n")
        f.write("  □ Replace gaskets if damaged\n")
        f.write("  □ Pressure test after reassembly\n\n")
        
        f.write("="*70 + "\n")
        f.write("SPARE PARTS RECOMMENDATION\n")
        f.write("="*70 + "\n\n")
        
        f.write("Critical spares:\n")
        f.write("  - Complete gasket set (1 set on-site)\n")
        f.write("  - Replacement plates (2 plates)\n")
        f.write("  - Tightening bolts (full set)\n\n")
        
        if selection['selected']:
            f.write("="*70 + "\n")
            f.write("COST SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Heat exchanger:       ${selection['cost_estimate_clp']:,.0f} CLP\n")
            f.write(f"Installation:         ${selection['cost_estimate_clp']*0.2:,.0f} CLP (est.)\n")
            f.write(f"Piping/valves:        $800,000 CLP (est.)\n")
            f.write(f"{'-'*70}\n")
            f.write(f"TOTAL ESTIMATE:       ${selection['cost_estimate_clp']*1.2 + 800_000:,.0f} CLP\n\n")
        
        f.write("="*70 + "\n")
        f.write("NEXT STEPS\n")
        f.write("="*70 + "\n\n")
        
        f.write("[ ] Obtain formal quotation from Alfa Laval distributor\n")
        f.write("[ ] Confirm fouling factors for water quality\n")
        f.write("[ ] Verify industrial water treatment adequacy\n")
        f.write("[ ] Complete system integration (06_system_integration.py)\n")
        f.write("[ ] Prepare P&ID with all components\n")
        f.write("[ ] Develop commissioning procedure\n\n")
        
        f.write("="*70 + "\n")
        f.write(f"Report generated by: Felipe Wasaff\n")
        f.write(f"Script: 05_heat_exchanger.py\n")
        f.write("="*70 + "\n")
    
    print(f"\n✓ Report saved: {report_path}")


def main():
    """Main execution function."""
    
    print("\n" + "="*70)
    print("CMPC HEAT RECOVERY SYSTEM - HEAT EXCHANGER DESIGN")
    print("="*70)
    print("\nDesigning intermediate heat exchanger...")
    print("Separates compressor loop from industrial water system\n")
    
    # Load data
    compressor_data, scenario_data = load_project_data()
    
    # Define requirements
    requirements = define_heat_exchanger_requirements(scenario_data)
    
    # Calculate LMTD and area
    lmtd_calc = calculate_lmtd_and_area(requirements)
    
    # Compare technologies
    comparison = compare_technologies(requirements)
    
    # Select commercial unit
    selection = select_commercial_unit(requirements, lmtd_calc)
    
    # Generate visualizations
    plot_heat_exchanger_analysis(requirements, lmtd_calc)
    
    # Generate report
    generate_heat_exchanger_report(requirements, lmtd_calc, comparison, selection)
    
    print("\n" + "="*70)
    print("HEAT EXCHANGER DESIGN COMPLETE")
    print("="*70)
    
    if selection['selected']:
        print("\nKey Results:")
        print(f"  → Type: Plate heat exchanger (gasketed)")
        print(f"  → Model: {selection['manufacturer']} {selection['model']}")
        print(f"  → Plates: {selection['num_plates']}")
        print(f"  → Area: {selection['total_area_m2']:.2f} m²")
        print(f"  → Duty: {selection['Q_actual_kW']:.1f} kW ({selection['margin_percent']:.1f}% margin)")
        print(f"  → Cost: ~${selection['cost_estimate_clp']:,.0f} CLP")
    
    print("\nNext: Run 06_system_integration.py for complete system validation")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
