"""
Setup script for the tripit-mcp package.
"""

from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "tripit-mcp=tripit_mcp.__main__:main",
        ],
    },
)
