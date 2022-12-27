from setuptools import setup

setup(
    name="netlistSimulator",
    version="1.0",
    packages=["netlistSimulator", "netlistSimulator.netlist2C"],
    install_requires=[
        "Lark",
    ],
    entry_points={
        "console_scripts": [
            "nl-transpile = netlistSimulator:main",
        ]
    },
)
