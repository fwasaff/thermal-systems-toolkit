"""
CMPC Heat Recovery System - System Analysis
===========================================

This script analyzes the different operating scenarios of the compressor
station and determines the thermal power available for heat recovery.

Author: Felipe Wasaff
Date: December 2024
Project: CMPC Puente Alto Heat Recovery System
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Add parent directory to path to import thermal_toolkit
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from thermal_toolkit import heat_transfer as ht


def load_project_data():
    """Load compressor specifications and operating scenarios from JSON files."""
    
    data_dir = Path(__file__).parent / 'data'
    
    with open(data_dir / 'compressor_specs.json', 'r') as f:
        compressor_data = json.load(f)
    
    with open(data_dir / 'operating_scenarios.json', 'r') as f:
        scenario_data = json.load(f)
    
    return compressor_data, scenario_data


def analyze_thermal_capacity(compressor_data):
    """
    Analyze maximum thermal recovery capacity of the system.
    
    Returns
    -------
    dict
        Summary of thermal capacities by compressor and total system
    """
    
    print("="*70)
    print("THERMAL CAPACITY ANALYSIS")
    print("="*70)
    
    compressors = compressor_data['compressors']
    
    total_thermal = 0
    total_flow = 0
    
    print("\nIndividual Compressor Capacities:")
    print("-" * 70)
    
    for comp in compressors:
        if comp['status'] == 'backup':
            print(f"\nCompressor #{comp['id']} ({comp['model']}) - BACKUP UNIT")
            print(f"  (Only operates if unit 1 or 2 fails)")
        else:
            print(f"\nCompressor #{comp['id']} ({comp['model']})")
        
        print(f"  Thermal Recovery: {comp['thermal_recovery_max_kW']:.0f} kW")
        print(f"  Water Flow:       {comp['water_flow_m3_per_h']:.2f} m³/h")
        print(f"  ΔT:               {comp['delta_T_K']} K")
        print(f"  Pressure Drop:    {comp['pressure_drop_bar']} bar")
        
        if comp['status'] != 'backup':
            total_thermal += comp['thermal_recovery_max_kW']
            total_flow += comp['water_flow_m3_per_h']
    
    print("\n" + "="*70)
    print(f"TOTAL SYSTEM CAPACITY (excluding backup):")
    print(f"  Total Thermal Power: {total_thermal:.0f} kW")
    print(f"  Total Water Flow:    {total_flow:.2f} m³/h")
    print("="*70)
    
    return {
        'total_thermal_kW': total_thermal,
        'total_flow_m3_per_h': total_flow,
        'num_active_units': len([c for c in compressors if c['status'] != 'backup'])
    }


def analyze_operating_scenarios(scenario_data, compressor_data):
    """
    Analyze all operating scenarios and their probabilities.
    
    Returns
    -------
    pandas.DataFrame
        Summary table of operating scenarios
    """
    
    print("\n" + "="*70)
    print("OPERATING SCENARIOS ANALYSIS")
    print("="*70)
    
    scenarios = scenario_data['operating_scenarios']
    
    # Create summary table
    summary_data = []
    
    for scenario in scenarios:
        scenario_num = scenario['scenario']
        air_demand = scenario['air_demand_m3_per_min']
        probability = scenario['probability_percent']
        active_units = scenario['compressors_active']
        thermal_power = scenario['thermal_power_kW']
        water_flow = scenario['water_flow_m3_per_h']
        
        is_normal = scenario.get('notes', '').find('NORMAL') >= 0
        is_max = scenario.get('notes', '').find('MAXIMUM') >= 0
        
        summary_data.append({
            'Scenario': scenario_num,
            'Air Demand [m³/min]': air_demand,
            'Probability [%]': probability,
            'Active Units': '-'.join(map(str, active_units)),
            'Thermal Power [kW]': thermal_power,
            'Water Flow [m³/h]': water_flow,
            'Normal Operation': '✓' if is_normal else '',
            'Max Capacity': '✓' if is_max else ''
        })
    
    df = pd.DataFrame(summary_data)
    
    print("\n" + df.to_string(index=False))
    
    # Highlight design condition
    normal_scenario = scenario_data['design_conditions']['normal_operation_scenario']
    design_power = scenario_data['design_conditions']['design_thermal_power_kW']
    design_flow = scenario_data['design_conditions']['design_water_flow_m3_per_h']
    
    print("\n" + "="*70)
    print(f"DESIGN CONDITIONS (Scenario {normal_scenario} - 80% probability):")
    print(f"  Design Thermal Power: {design_power} kW")
    print(f"  Design Water Flow:    {design_flow} m³/h")
    print("="*70)
    
    return df


def calculate_heat_recovery_verification(scenario_data):
    """
    Verify heat recovery calculations using fundamental equations.
    
    This validates that Q = ṁ·cp·ΔT for each scenario.
    """
    
    print("\n" + "="*70)
    print("HEAT RECOVERY VERIFICATION")
    print("="*70)
    print("\nVerifying Q = ṁ·cp·ΔT for each scenario...")
    
    scenarios = scenario_data['operating_scenarios']
    
    for scenario in scenarios:
        thermal_power_stated = scenario['thermal_power_kW']
        water_flow_m3h = scenario['water_flow_m3_per_h']
        delta_T = 25  # K (constant for all compressors)
        
        # Convert to SI units
        mass_flow = ht.volumetric_to_mass_flow(
            water_flow_m3h / 3600,  # m³/s
            ht.WATER_RHO
        )
        
        # Calculate thermal power
        Q_calculated = ht.required_heat_transfer(
            mass_flow,
            delta_T,
            ht.WATER_CP
        )
        
        Q_calculated_kW = Q_calculated / 1000
        
        error_percent = abs(Q_calculated_kW - thermal_power_stated) / thermal_power_stated * 100
        
        status = "✓" if error_percent < 1.0 else "⚠"
        
        print(f"\nScenario {scenario['scenario']}:")
        print(f"  Stated:     {thermal_power_stated:.1f} kW")
        print(f"  Calculated: {Q_calculated_kW:.1f} kW")
        print(f"  Error:      {error_percent:.2f}% {status}")


def plot_scenario_distribution(scenario_data):
    """Create visualizations of operating scenarios."""
    
    scenarios = scenario_data['operating_scenarios']
    
    # Extract data
    scenario_nums = [s['scenario'] for s in scenarios]
    probabilities = [s['probability_percent'] for s in scenarios]
    thermal_powers = [s['thermal_power_kW'] for s in scenarios]
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Probability distribution
    colors = ['#2ecc71' if s.get('notes', '').find('NORMAL') >= 0 else '#3498db' 
              for s in scenarios]
    
    bars1 = ax1.bar(scenario_nums, probabilities, color=colors, alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Scenario Number', fontsize=12)
    ax1.set_ylabel('Probability [%]', fontsize=12)
    ax1.set_title('Operating Scenario Distribution', fontsize=14, fontweight='bold')
    ax1.grid(True, axis='y', alpha=0.3)
    
    # Annotate normal operation
    normal_idx = next(i for i, s in enumerate(scenarios) 
                     if s.get('notes', '').find('NORMAL') >= 0)
    ax1.annotate('Normal Operation\n(80%)', 
                xy=(scenario_nums[normal_idx], probabilities[normal_idx]),
                xytext=(scenario_nums[normal_idx] + 0.5, probabilities[normal_idx] + 10),
                arrowprops=dict(arrowstyle='->', lw=2, color='green'),
                fontsize=11, fontweight='bold', color='green')
    
    # Plot 2: Thermal power vs probability
    ax2.scatter(thermal_powers, probabilities, s=200, c=colors, 
               alpha=0.7, edgecolors='black', linewidths=2)
    
    for i, (power, prob, num) in enumerate(zip(thermal_powers, probabilities, scenario_nums)):
        ax2.annotate(f'S{num}', (power, prob), 
                    textcoords="offset points", xytext=(0,10), 
                    ha='center', fontsize=10, fontweight='bold')
    
    ax2.set_xlabel('Thermal Power [kW]', fontsize=12)
    ax2.set_ylabel('Probability [%]', fontsize=12)
    ax2.set_title('Thermal Power vs. Operating Probability', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Add design condition line
    design_power = scenario_data['design_conditions']['design_thermal_power_kW']
    ax2.axvline(design_power, color='red', linestyle='--', linewidth=2, 
               label=f'Design: {design_power} kW')
    ax2.legend(fontsize=11)
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'scenario_analysis.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {output_dir / 'scenario_analysis.png'}")
    
    return fig


def generate_summary_report(compressor_data, scenario_data, capacity_summary, scenario_df):
    """Generate a summary report of the system analysis."""
    
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / 'system_analysis_report.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("CMPC HEAT RECOVERY SYSTEM - SYSTEM ANALYSIS REPORT\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Client: {compressor_data['project_info']['client']}\n")
        f.write(f"Location: {compressor_data['project_info']['location']}\n")
        f.write(f"Date: {compressor_data['project_info']['date']}\n")
        f.write(f"Consultant: {compressor_data['project_info']['consultant']}\n\n")
        
        f.write("="*70 + "\n")
        f.write("SYSTEM CAPACITY SUMMARY\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Total Thermal Capacity: {capacity_summary['total_thermal_kW']:.0f} kW\n")
        f.write(f"Total Water Flow:       {capacity_summary['total_flow_m3_per_h']:.2f} m³/h\n")
        f.write(f"Active Compressors:     {capacity_summary['num_active_units']}\n\n")
        
        f.write("="*70 + "\n")
        f.write("DESIGN CONDITIONS\n")
        f.write("="*70 + "\n\n")
        
        design = scenario_data['design_conditions']
        f.write(f"Design Thermal Power:   {design['design_thermal_power_kW']} kW\n")
        f.write(f"Design Water Flow:      {design['design_water_flow_m3_per_h']} m³/h\n")
        f.write(f"Operating Probability:  80%\n\n")
        
        f.write("="*70 + "\n")
        f.write("OPERATING SCENARIOS\n")
        f.write("="*70 + "\n\n")
        
        f.write(scenario_df.to_string(index=False))
        f.write("\n\n")
        
        f.write("="*70 + "\n")
        f.write("KEY FINDINGS\n")
        f.write("="*70 + "\n\n")
        
        f.write("1. The system operates at 622 kW thermal power 80% of the time\n")
        f.write("   (Scenario 3: Units 1, 2, and 4 active)\n\n")
        
        f.write("2. Maximum capacity is 948 kW with all units operating\n")
        f.write("   (only 2% probability)\n\n")
        
        f.write("3. System must be designed for 622 kW nominal capacity\n")
        f.write("   with ability to handle up to 948 kW peak\n\n")
        
        f.write("="*70 + "\n")
        f.write("NEXT STEPS\n")
        f.write("="*70 + "\n\n")
        
        f.write("[ ] Design piping network for 21.72 m³/h nominal flow\n")
        f.write("[ ] Select pump for required head and flow\n")
        f.write("[ ] Size thermal storage tank\n")
        f.write("[ ] Design intermediate heat exchanger\n")
        f.write("[ ] System integration and validation\n\n")
        
        f.write("="*70 + "\n")
        f.write(f"Report generated by: Felipe Wasaff\n")
        f.write(f"Script: 01_system_analysis.py\n")
        f.write("="*70 + "\n")
    
    print(f"\n✓ Report saved: {report_path}")


def main():
    """Main execution function."""
    
    print("\n" + "="*70)
    print("CMPC HEAT RECOVERY SYSTEM - SYSTEM ANALYSIS")
    print("="*70)
    print("\nAnalyzing compressor station operating scenarios...")
    print("This analysis will determine the design basis for the heat recovery system.\n")
    
    # Load data
    compressor_data, scenario_data = load_project_data()
    
    # Run analyses
    capacity_summary = analyze_thermal_capacity(compressor_data)
    scenario_df = analyze_operating_scenarios(scenario_data, compressor_data)
    calculate_heat_recovery_verification(scenario_data)
    
    # Generate visualizations
    plot_scenario_distribution(scenario_data)
    
    # Generate report
    generate_summary_report(compressor_data, scenario_data, capacity_summary, scenario_df)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print("\nKey Results:")
    print(f"  → Design condition: 622 kW (80% probability)")
    print(f"  → Maximum capacity: 948 kW (2% probability)")
    print(f"  → Design water flow: 21.72 m³/h")
    print("\nNext: Run 02_piping_design.py to design the piping network")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
