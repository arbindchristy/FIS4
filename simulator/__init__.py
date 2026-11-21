"""Fictional, offline fleet-history generation; never wired into production APIs."""

from simulator.contracts import SimulationConfig, SyntheticHistory
from simulator.generator import generate

__all__ = ["SimulationConfig", "SyntheticHistory", "generate"]
