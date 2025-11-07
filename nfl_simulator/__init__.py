"""NFL game simulation package.

This package provides utilities for loading player data, estimating team
strength, and running Monte Carlo simulations of NFL games. The public API
exposes the :mod:`nfl_simulator.cli` entry point for command line usage and the
:class:`nfl_simulator.simulation.GameSimulator` class for programmatic access.
"""

from .models import Player, PlayerMetrics, Team
from .data_loader import load_team_from_csv
from .simulation import GameSimulator, SimulationResult

__all__ = [
    "Player",
    "PlayerMetrics",
    "Team",
    "load_team_from_csv",
    "GameSimulator",
    "SimulationResult",
]
