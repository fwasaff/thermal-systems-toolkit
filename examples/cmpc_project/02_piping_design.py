"""
CMPC Heat Recovery System - Piping Network Design
=================================================

This script designs the complete piping network for the heat recovery system,
including:
- Pipe diameter sizing for each section
- Pressure drop calculations
- Network configuration analysis (series vs parallel)
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

from thermal_toolkit import fluid_flow as ff
from thermal_toolkit import heat_transfer as ht


def load_project_data():
    """Load project specifications."""
    data_dir = Path(__file__).parent / 'data'
    
    with open(data_dir / 'compressor_specs.json', 'r') as f:
        compressor_data = json.load(f)
    
    with open(data_dir / 'operating_scenarios.json', 'r') as f:
        scenario_data = json.load(f)
    
    return compressor_data, scenario_data


def define_piping_network():
    """
    Define the piping network layout.
    
    Returns
    -------
    dict
        Network configuration with pipe sections
    
    Notes
    -----
    Network configuration:
    - Main header (collector): Collects from all compressors
    - Branch lines: From each compressor to main header
    - Supply line: From main header to accumulator
    - Return line: From accumulator back to compressors
    
    Based on layout drawing from Kaeser (CMPC_Puente_Alto_General_2__2_.pdf):
    - Piping height: 3.606 m from floor
    - Compressors arranged in two rows
    - Distances estimated from layout
    """
    
    # Piping network sections
    network = {
        # Branch lines from compressors to main header
        'branches': [
            {
                'id': 'branch_1',
                'from': 'Compressor_1',
                'to': 'Main_Header',
                'length_horizontal': 5.0,  # m (estimated from layout)
                'length_vertical': 1.2,    # m (from pump to header)
                'fittings': {
                    '90_elbow': 2,
                    'tee_branch': 1,
                    'gate_valve_open': 1
                }
            },
            {
                'id': 'branch_2',
                'from': 'Compressor_2',
                'to': 'Main_Header',
                'length_horizontal': 3.0,
                'length_vertical': 1.2,
                'fittings': {
                    '90_elbow': 2,
                    'tee_branch': 1,
                    'gate_valve_open': 1
                }
            },
            {
                'id': 'branch_3',
                'from': 'Compressor_3_BACKUP',
                'to': 'Main_Header',
                'length_horizontal': 5.0,
                'length_vertical': 1.2,
                'fittings': {
                    '90_elbow': 2,
                    'tee_branch': 1,
                    'gate_valve_open': 1
                }
            },
            {
                'id': 'branch_4',
                'from': 'Compressor_4',
                'to': 'Main_Header',
                'length_horizontal': 8.0,
                'length_vertical': 1.2,
                'fittings': {
                    '90_elbow': 2,
                    'tee_branch': 1,
                    'gate_valve_open': 1
                }
            },
            {
                'id': 'branch_5',
                'from': 'Compressor_5',
                'to': 'Main_Header',
                'length_horizontal': 10.0,
                'length_vertical': 1.2,
                'fittings': {
                    '90_elbow': 2,
                    'tee_branch': 1,
                    'gate_valve_open': 1
                }
            },
            {
                'id': 'branch_6',
                'from': 'Compressor_6',
                'to': 'Main_Header',
                'length_horizontal': 12.0,
                'length_vertical': 1.2,
                'fittings': {
                    '90_elbow': 2,
                    'tee_branch': 1,
                    'gate_valve_open': 1
                }
            }
        ],
        
        # Main header sections
        'headers': [
            {
                'id': 'header_section_1',
                'from': 'Junction_1',
                'to': 'Junction_2',
                'length': 3.0,
                'fittings': {'tee_line': 1}
            },
            {
                'id': 'header_section_2',
                'from': 'Junction_2',
                'to': 'Junction_3',
                'length': 3.0,
                'fittings': {'tee_line': 1}
            },
            {
                'id': 'header_section_3',
                'from': 'Junction_3',
                'to': 'Junction_4',
                'length': 4.0,
                'fittings': {'tee_line': 1}
            },
            {
                'id': 'header_section_4',
                'from': 'Junction_4',
                'to': 'Accumulator',
                'length': 4.0,
                'fittings': {'90_elbow': 1}
            }
        ],
        
        # Supply to accumulator
        'supply': {
            'id': 'supply_line',
            'from': 'Main_Header',
            'to': 'Accumulator',
            'length': 5.0,
            'fittings': {
                '90_elbow': 2,
                'gate_valve_open': 1
            }
        },
        
        # Return from accumulator
        'return': {
            'id': 'return_line',
            'from': 'Accumulator',
            'to': 'Compressor_Inlets',
            'length': 8.0,
            'fittings': {
                '90_elbow': 3,
                'gate_valve_open': 1
            }
        }
    }
    
    return network


def design_branch_pipes(compressor_data, network):
    """
    Design branch pipes from each compressor to main header.
    
    Parameters
    ----------
    compressor_data : dict
        Compressor specifications
    network : dict
        Network configuration
    
    Returns
    -------
    list
        List of pipe designs for each branch
    """
    
    print("\n" + "="*70)
    print("BRANCH PIPE DESIGN")
    print("="*70)
    print("\nDesigning individual branch lines from compressors to main header...")
    
    compressors = compressor_data['compressors']
    branches = network['branches']
    
    branch_designs = []
    
    for i, (comp, branch) in enumerate(zip(compressors, branches)):
        print(f"\n{'-'*70}")
        print(f"Branch {i+1}: {comp['model']} (Unit #{comp['id']})")
        
        if comp['status'] == 'backup':
            print("  Status: BACKUP UNIT (sized but normally closed)")
        
        # Flow rate for this compressor
        flow_rate = comp['water_flow_m3_per_h']
        
        # Total length (horizontal + vertical)
        length_total = branch['length_horizontal'] + branch['length_vertical']
        
        # Design pipe
        design = ff.pipe_design_summary(
            flow_rate_m3h=flow_rate,
            length=length_total,
            fittings=branch['fittings'],
            material='commercial_steel',
            v_target=2.0  # Target 2 m/s
        )
        
        # Add branch info
        design['branch_id'] = branch['id']
        design['compressor_id'] = comp['id']
        design['compressor_model'] = comp['model']
        design['is_backup'] = (comp['status'] == 'backup')
        
        branch_designs.append(design)
        
        # Print summary
        print(f"  Flow rate:       {design['flow_rate_m3h']:.2f} m³/h")
        print(f"  Selected DN:     DN{design['DN']}")
        print(f"  Internal dia:    {design['D_internal_mm']:.1f} mm")
        print(f"  Velocity:        {design['velocity_m_s']:.2f} m/s")
        print(f"  Reynolds:        {design['Reynolds']:.0f} ({design['flow_regime']})")
        print(f"  Friction factor: {design['friction_factor']:.4f}")
        print(f"  Length (equiv):  {design['length_total_m']:.2f} m")
        print(f"  Pressure drop:   {design['pressure_drop_total_kPa']:.2f} kPa ({design['pressure_drop_total_bar']:.3f} bar)")
    
    return branch_designs


def design_main_header(scenario_data, network):
    """
    Design main header (collector) that accumulates flow from all branches.
    
    The header must handle progressively increasing flow as branches join.
    
    Parameters
    ----------
    scenario_data : dict
        Operating scenarios
    network : dict
        Network configuration
    
    Returns
    -------
    list
        List of header section designs
    """
    
    print("\n" + "="*70)
    print("MAIN HEADER DESIGN")
    print("="*70)
    print("\nDesigning main collector header (progressive flow accumulation)...")
    
    # Design for maximum capacity scenario
    max_scenario = scenario_data['design_conditions']
    max_flow = max_scenario['maximum_water_flow_m3_per_h']
    
    # Design for normal operation scenario
    normal_flow = max_scenario['design_water_flow_m3_per_h']
    
    print(f"\nDesign criteria:")
    print(f"  Normal operation: {normal_flow} m³/h (80% probability)")
    print(f"  Maximum capacity: {max_flow} m³/h (peak demand)")
    
    # For simplicity, design header for maximum flow
    # In reality, you'd segment it as flow accumulates
    
    header_design = ff.pipe_design_summary(
        flow_rate_m3h=max_flow,
        length=15.0,  # Total header length
        fittings={
            'tee_line': 5,  # Multiple junctions
            '90_elbow': 2
        },
        material='commercial_steel',
        v_target=2.5  # Slightly higher for main header
    )
    
    print(f"\nMain Header Design:")
    print(f"  Design flow:     {header_design['flow_rate_m3h']:.2f} m³/h")
    print(f"  Selected DN:     DN{header_design['DN']}")
    print(f"  Internal dia:    {header_design['D_internal_mm']:.1f} mm")
    print(f"  Velocity:        {header_design['velocity_m_s']:.2f} m/s")
    print(f"  Pressure drop:   {header_design['pressure_drop_total_kPa']:.2f} kPa")
    
    return header_design


def calculate_system_pressure_drop(branch_designs, header_design):
    """
    Calculate total system pressure drop.
    
    Parameters
    ----------
    branch_designs : list
        Branch pipe designs
    header_design : dict
        Main header design
    
    Returns
    -------
    dict
        System pressure drop summary
    """
    
    print("\n" + "="*70)
    print("SYSTEM PRESSURE DROP ANALYSIS")
    print("="*70)
    
    # Worst case: longest branch path + header
    # (Typically compressor #6 is furthest)
    
    # Find branch with highest pressure drop
    active_branches = [b for b in branch_designs if not b['is_backup']]
    worst_branch = max(active_branches, key=lambda x: x['pressure_drop_total_Pa'])
    
    print(f"\nWorst case path analysis:")
    print(f"  Critical branch: {worst_branch['branch_id']}")
    print(f"  Compressor: {worst_branch['compressor_model']} (Unit #{worst_branch['compressor_id']})")
    print(f"  Branch ΔP: {worst_branch['pressure_drop_total_kPa']:.2f} kPa")
    print(f"  Header ΔP: {header_design['pressure_drop_total_kPa']:.2f} kPa")
    
    # Total system pressure drop
    dP_branch = worst_branch['pressure_drop_total_Pa']
    dP_header = header_design['pressure_drop_total_Pa']
    dP_total = dP_branch + dP_header
    
    # Add safety factor (typical 20% for design margin)
    safety_factor = 1.2
    dP_design = dP_total * safety_factor
    
    print(f"\nTotal pressure drop:")
    print(f"  Calculated: {dP_total/1000:.2f} kPa ({dP_total/100000:.3f} bar)")
    print(f"  With 20% safety: {dP_design/1000:.2f} kPa ({dP_design/100000:.3f} bar)")
    
    # Check against compressor heat exchanger limits
    print(f"\nCompressor heat exchanger limits:")
    for comp_design in branch_designs:
        if not comp_design['is_backup']:
            # Find corresponding compressor data
            comp_model = comp_design['compressor_model']
            if 'FSD' in comp_model:
                max_dP = 0.4  # bar
            elif 'DSDX' in comp_model:
                max_dP = 0.25  # bar
            elif 'ESD' in comp_model:
                max_dP = 0.4  # bar
            
            actual_dP = dP_design / 100000  # Convert to bar
            margin = (max_dP - actual_dP) / max_dP * 100
            
            status = "✓ OK" if actual_dP < max_dP else "⚠ EXCEEDS"
            
            print(f"  {comp_model}: {actual_dP:.3f} bar / {max_dP:.2f} bar max ({margin:.1f}% margin) {status}")
    
    return {
        'dP_branch_worst_Pa': dP_branch,
        'dP_branch_worst_kPa': dP_branch / 1000,
        'dP_header_Pa': dP_header,
        'dP_header_kPa': dP_header / 1000,
        'dP_total_Pa': dP_total,
        'dP_total_kPa': dP_total / 1000,
        'dP_total_bar': dP_total / 100000,
        'dP_design_Pa': dP_design,
        'dP_design_kPa': dP_design / 1000,
        'dP_design_bar': dP_design / 100000,
        'safety_factor': safety_factor,
        'worst_branch': worst_branch['branch_id']
    }


def plot_pipe_sizing_summary(branch_designs, header_design):
    """Create visualization of pipe sizing results."""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Extract data
    branch_ids = [f"Unit {d['compressor_id']}" for d in branch_designs]
    flows = [d['flow_rate_m3h'] for d in branch_designs]
    DNs = [d['DN'] for d in branch_designs]
    velocities = [d['velocity_m_s'] for d in branch_designs]
    pressures = [d['pressure_drop_total_kPa'] for d in branch_designs]
    is_backup = [d['is_backup'] for d in branch_designs]
    
    # Colors: blue for active, gray for backup
    colors = ['#95a5a6' if backup else '#3498db' for backup in is_backup]
    
    # Plot 1: Flow rates and DN selection
    ax1.bar(range(len(branch_ids)), flows, color=colors, alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Compressor Unit', fontsize=11)
    ax1.set_ylabel('Flow Rate [m³/h]', fontsize=11)
    ax1.set_title('Water Flow Rate by Branch', fontsize=12, fontweight='bold')
    ax1.set_xticks(range(len(branch_ids)))
    ax1.set_xticklabels(branch_ids, rotation=45)
    ax1.grid(True, axis='y', alpha=0.3)
    
    # Annotate DN on bars
    for i, (flow, dn) in enumerate(zip(flows, DNs)):
        ax1.text(i, flow + 0.2, f'DN{dn}', ha='center', fontsize=9, fontweight='bold')
    
    # Plot 2: Velocities
    ax2.bar(range(len(branch_ids)), velocities, color=colors, alpha=0.7, edgecolor='black')
    ax2.axhline(y=0.6, color='red', linestyle='--', linewidth=1.5, label='Min: 0.6 m/s')
    ax2.axhline(y=3.0, color='red', linestyle='--', linewidth=1.5, label='Max: 3.0 m/s')
    ax2.axhspan(1.5, 2.5, alpha=0.1, color='green', label='Optimal range')
    ax2.set_xlabel('Compressor Unit', fontsize=11)
    ax2.set_ylabel('Velocity [m/s]', fontsize=11)
    ax2.set_title('Flow Velocity in Branches', fontsize=12, fontweight='bold')
    ax2.set_xticks(range(len(branch_ids)))
    ax2.set_xticklabels(branch_ids, rotation=45)
    ax2.legend(fontsize=9)
    ax2.grid(True, axis='y', alpha=0.3)
    
    # Plot 3: Pressure drops
    ax3.bar(range(len(branch_ids)), pressures, color=colors, alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Compressor Unit', fontsize=11)
    ax3.set_ylabel('Pressure Drop [kPa]', fontsize=11)
    ax3.set_title('Pressure Drop by Branch', fontsize=12, fontweight='bold')
    ax3.set_xticks(range(len(branch_ids)))
    ax3.set_xticklabels(branch_ids, rotation=45)
    ax3.grid(True, axis='y', alpha=0.3)
    
    # Plot 4: Reynolds numbers (flow regime verification)
    reynolds = [d['Reynolds'] for d in branch_designs]
    ax4.bar(range(len(branch_ids)), reynolds, color=colors, alpha=0.7, edgecolor='black')
    ax4.axhline(y=4000, color='orange', linestyle='--', linewidth=2, label='Turbulent threshold')
    ax4.set_xlabel('Compressor Unit', fontsize=11)
    ax4.set_ylabel('Reynolds Number', fontsize=11)
    ax4.set_title('Flow Regime Analysis', fontsize=12, fontweight='bold')
    ax4.set_xticks(range(len(branch_ids)))
    ax4.set_xticklabels(branch_ids, rotation=45)
    ax4.legend(fontsize=9)
    ax4.grid(True, axis='y', alpha=0.3)
    ax4.set_yscale('log')
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'piping_design_summary.png', dpi=150, bbox_inches='tight')
    print(f"\n✓ Figure saved: {output_dir / 'piping_design_summary.png'}")
    
    return fig


def generate_piping_report(branch_designs, header_design, system_pressure):
    """Generate comprehensive piping design report."""
    
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / 'piping_design_report.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("CMPC HEAT RECOVERY SYSTEM - PIPING NETWORK DESIGN REPORT\n")
        f.write("="*70 + "\n\n")
        
        f.write("PROJECT INFORMATION\n")
        f.write("-"*70 + "\n")
        f.write("Client: Papeles Cordillera S.A. (CMPC Puente Alto)\n")
        f.write("System: Heat Recovery from Air Compressors\n")
        f.write("Design Standard: ASME B31.1 (Power Piping)\n")
        f.write("Fluid: Water (closed loop, glycol option for freeze protection)\n\n")
        
        f.write("="*70 + "\n")
        f.write("BRANCH PIPE DESIGN SUMMARY\n")
        f.write("="*70 + "\n\n")
        
        # Create table
        f.write(f"{'Unit':<8} {'Model':<12} {'DN':<6} {'Dia[mm]':<10} {'Vel[m/s]':<10} {'ΔP[kPa]':<10} {'Status':<10}\n")
        f.write("-"*70 + "\n")
        
        for design in branch_designs:
            status = "BACKUP" if design['is_backup'] else "ACTIVE"
            f.write(f"{design['compressor_id']:<8} "
                   f"{design['compressor_model']:<12} "
                   f"DN{design['DN']:<4} "
                   f"{design['D_internal_mm']:<10.1f} "
                   f"{design['velocity_m_s']:<10.2f} "
                   f"{design['pressure_drop_total_kPa']:<10.2f} "
                   f"{status:<10}\n")
        
        f.write("\n")
        f.write("="*70 + "\n")
        f.write("MAIN HEADER DESIGN\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Selected DN:         DN{header_design['DN']}\n")
        f.write(f"Internal diameter:   {header_design['D_internal_mm']:.1f} mm\n")
        f.write(f"Design flow:         {header_design['flow_rate_m3h']:.2f} m³/h\n")
        f.write(f"Velocity:            {header_design['velocity_m_s']:.2f} m/s\n")
        f.write(f"Pressure drop:       {header_design['pressure_drop_total_kPa']:.2f} kPa\n")
        f.write(f"Total length:        {header_design['length_total_m']:.2f} m\n\n")
        
        f.write("="*70 + "\n")
        f.write("SYSTEM PRESSURE DROP\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Critical path:       {system_pressure['worst_branch']}\n")
        f.write(f"Branch ΔP:           {system_pressure['dP_branch_worst_kPa']:.2f} kPa\n")
        f.write(f"Header ΔP:           {system_pressure['dP_header_kPa']:.2f} kPa\n")
        f.write(f"Total ΔP:            {system_pressure['dP_total_kPa']:.2f} kPa ({system_pressure['dP_total_bar']:.3f} bar)\n")
        f.write(f"Design ΔP (20% SF):  {system_pressure['dP_design_kPa']:.2f} kPa ({system_pressure['dP_design_bar']:.3f} bar)\n\n")
        
        f.write("="*70 + "\n")
        f.write("MATERIAL SPECIFICATION\n")
        f.write("="*70 + "\n\n")
        
        f.write("Recommended materials:\n")
        f.write("  Primary option:   ASTM A53 Grade B Carbon Steel (Schedule 40)\n")
        f.write("  Alternative:      ASTM A106 Grade B Seamless Carbon Steel\n")
        f.write("  Fittings:         ASME B16.9 Butt-Weld Fittings\n")
        f.write("  Flanges:          ASME B16.5 Class 150 RF\n")
        f.write("  Valves:           Gate valves ASME B16.34\n\n")
        
        f.write("Insulation:\n")
        f.write("  Type:             Mineral wool or fiberglass\n")
        f.write("  Thickness:        50 mm (for pipes up to DN100)\n")
        f.write("  Jacket:           Aluminum or PVC\n\n")
        
        f.write("="*70 + "\n")
        f.write("DESIGN RECOMMENDATIONS\n")
        f.write("="*70 + "\n\n")
        
        f.write("1. CONFIGURATION:\n")
        f.write("   → Use reverse return piping for balanced flow distribution\n")
        f.write("   → Install isolation valves on each branch for maintenance\n")
        f.write("   → Include drain/vent points at low/high locations\n\n")
        
        f.write("2. EXPANSION:\n")
        f.write("   → Install expansion loops or compensators for thermal expansion\n")
        f.write("   → Estimate: ΔL = α·L·ΔT ≈ 12 mm per 10m @ 50°C rise\n")
        f.write("   → Use guided supports at regular intervals\n\n")
        
        f.write("3. PROTECTION:\n")
        f.write("   → Consider glycol addition (10-15%) for freeze protection\n")
        f.write("   → Install air vents at high points to prevent air locks\n")
        f.write("   → Include strainers upstream of heat exchangers\n\n")
        
        f.write("4. TESTING:\n")
        f.write("   → Hydrostatic test: 1.5× design pressure (minimum 1 hour)\n")
        f.write("   → Leak test: Pressure hold for 24 hours\n")
        f.write("   → Flow balance: Verify flow rates match design\n\n")
        
        f.write("="*70 + "\n")
        f.write("BILL OF MATERIALS (ESTIMATED)\n")
        f.write("="*70 + "\n\n")
        
        # Calculate approximate material quantities
        total_pipe_length = sum(d['length_total_m'] for d in branch_designs) + header_design['length_total_m']
        
        f.write(f"Total pipe length:   ~{total_pipe_length:.0f} m\n\n")
        
        f.write("Pipe quantities (approximate):\n")
        dn_counts = {}
        for design in branch_designs:
            dn = design['DN']
            length = design['length_total_m']
            if dn in dn_counts:
                dn_counts[dn] += length
            else:
                dn_counts[dn] = length
        
        # Add header
        dn_counts[header_design['DN']] = dn_counts.get(header_design['DN'], 0) + header_design['length_total_m']
        
        for dn in sorted(dn_counts.keys()):
            f.write(f"  DN{dn} Schedule 40: {dn_counts[dn]:.1f} m\n")
        
        f.write("\nFittings (estimated):\n")
        f.write(f"  90° elbows:       ~{len(branch_designs) * 2 + 5} units\n")
        f.write(f"  Tees:             ~{len(branch_designs) + 3} units\n")
        f.write(f"  Gate valves:      ~{len(branch_designs) + 2} units\n")
        f.write(f"  Flanges:          ~{len(branch_designs) * 4} pairs\n\n")
        
        f.write("="*70 + "\n")
        f.write("NEXT STEPS\n")
        f.write("="*70 + "\n\n")
        
        f.write("[ ] Detailed isometric drawings with dimensions\n")
        f.write("[ ] Pump selection based on system curve\n")
        f.write("[ ] Thermal storage tank sizing\n")
        f.write("[ ] Intermediate heat exchanger design\n")
        f.write("[ ] Complete BOM with vendor quotes\n")
        f.write("[ ] Installation procedure and schedule\n\n")
        
        f.write("="*70 + "\n")
        f.write(f"Report generated by: Felipe Wasaff\n")
        f.write(f"Script: 02_piping_design.py\n")
        f.write("="*70 + "\n")
    
    print(f"\n✓ Report saved: {report_path}")


def main():
    """Main execution function."""
    
    print("\n" + "="*70)
    print("CMPC HEAT RECOVERY SYSTEM - PIPING NETWORK DESIGN")
    print("="*70)
    print("\nDesigning complete piping network for heat recovery system...")
    print("Analysis includes: pipe sizing, pressure drop, material selection\n")
    
    # Load data
    compressor_data, scenario_data = load_project_data()
    
    # Define network
    network = define_piping_network()
    
    # Design branch pipes
    branch_designs = design_branch_pipes(compressor_data, network)
    
    # Design main header
    header_design = design_main_header(scenario_data, network)
    
    # Calculate system pressure drop
    system_pressure = calculate_system_pressure_drop(branch_designs, header_design)
    
    # Generate visualizations
    plot_pipe_sizing_summary(branch_designs, header_design)
    
    # Generate report
    generate_piping_report(branch_designs, header_design, system_pressure)
    
    print("\n" + "="*70)
    print("PIPING DESIGN COMPLETE")
    print("="*70)
    print("\nKey Results:")
    print(f"  → System pressure drop: {system_pressure['dP_design_kPa']:.2f} kPa (with safety factor)")
    print(f"  → Critical path: {system_pressure['worst_branch']}")
    print(f"  → Main header: DN{header_design['DN']}")
    print("\nNext: Run 03_pump_selection.py to select circulation pump")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
