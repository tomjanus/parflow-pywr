#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='moea-tools',
    version='1.0',
    description='Tools for processing outputs from MOEA optimization runs',
    packages=find_packages(),
    package_data={},
    include_package_data=True,
    py_modules=['process_outputs', 'outputs_visualisation'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        moea-tools=cli:start_cli
    ''',
)
