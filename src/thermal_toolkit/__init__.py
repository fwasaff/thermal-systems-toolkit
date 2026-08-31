"""
Thermal Systems Toolkit
======================

A Python library for thermal system design and analysis.

Modules
-------
- heat_transfer: Heat transfer calculations
- fluid_flow: Fluid mechanics and pipe design
- pumps: Pump selection and sizing
- storage_tanks: Thermal storage tank design
- heat_exchangers: Heat exchanger design and analysis

Author: Felipe Wasaff
Email: felipe.wasaff@uchile.cl
"""

__version__ = '0.1.0'
__author__ = 'Felipe Wasaff'

# Import main modules
from . import heat_transfer
from . import fluid_flow
from . import pumps
from . import storage_tanks
from . import heat_exchangers

__all__ = ['heat_transfer', 'fluid_flow', 'pumps', 'storage_tanks', 'heat_exchangers']
