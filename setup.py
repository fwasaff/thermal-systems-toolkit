"""
Setup script for thermal-systems-toolkit
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / 'README.md'
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ''

setup(
    name='thermal-systems-toolkit',
    version='0.1.0',
    author='Felipe Wasaff',
    author_email='felipe.wasaff@uchile.cl',
    description='Python toolkit for thermal system design and analysis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fwasaff/thermal-systems-toolkit',
    
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    
    install_requires=[
        'numpy>=1.21.0',
        'scipy>=1.7.0',
        'matplotlib>=3.4.0',
        'pandas>=1.3.0',
    ],
    
    python_requires='>=3.8',
    
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
