#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='parflow-pywr-moea',
    version='0.1',
    description='Coupled Parflow and Pywr modelling system.',
    packages=find_packages(),
    install_requires=[
        'click', 'pywr', 'numpy'
    ],
    entry_points='''
    [console_scripts]
    parflow-pywr=parflow_pywr_moea.cli:start_cli
    ''',
)
