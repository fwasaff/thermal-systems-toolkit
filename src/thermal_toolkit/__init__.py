"""
Thermal Systems Toolkit
======================

A Python library for thermal system design and analysis.

Modules
-------
- heat_transfer: Heat transfer calculations
- fluid_flow: Fluid mechanics and pipe design (coming soon)
- heat_exchangers: Heat exchanger design (coming soon)
- pumps: Pump selection and sizing (coming soon)

Author: Felipe Wasaff
Email: felipe.wasaff@uchile.cl
"""

__version__ = '0.1.0'
__author__ = 'Felipe Wasaff'

# Import main modules
from . import heat_transfer

__all__ = ['heat_transfer']
