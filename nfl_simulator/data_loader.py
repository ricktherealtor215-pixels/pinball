"""Utility functions for ingesting roster and metric data."""

from __future__ import annotations

import csv
import os
from typing import Dict, Mapping, MutableMapping, Optional

from .models import Player, PlayerMetrics, Team

TEAM_FIELD_ALIASES: Mapping[str, str] = {
    "team": "name",
    "team_name": "name",
    "pace": "pace_per_game",
    "pace_per_game": "pace_per_game",
    "aggressiveness": "coaching_aggressiveness",
    "coaching_aggressiveness": "coaching_aggressiveness",
    "home_field_advantage": "home_field_advantage",
    "home_field": "home_field_advantage",
    "injury_adjustment": "injury_adjustment",
    "injuries": "injury_adjustment",
}


class TeamLoaderError(RuntimeError):
    """Raised when roster data cannot be converted into a :class:`Team`."""


def _parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _derive_team_name(path: str) -> str:
    base = os.path.basename(path)
    name, *_ = os.path.splitext(base)
    return name.replace("_", " ").title()


def load_team_from_csv(
    path: str,
    *,
    name: Optional[str] = None,
    overrides: Optional[Mapping[str, float]] = None,
) -> Team:
    """Load team and player data from a CSV export.

    Parameters
    ----------
    path:
        Location of the CSV file containing roster and metric data. The file is
        expected to contain at least the columns ``name`` and ``position``.
        Additional numeric columns are interpreted as player metrics and made
        available to the simulation engine.
    name:
        Optional override for the team name. When omitted, the loader first
        looks for a ``team`` or ``team_name`` column in metadata rows (rows
        without a ``position`` value). If still undefined it falls back to the
        file name.
    overrides:
        Mapping used to override the resulting :class:`Team` attributes (for
        example ``{"home_field_advantage": 1.2}``). Keys follow the attribute
        names defined on :class:`Team`.
    """

    with open(path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        players = []
        team_kwargs: MutableMapping[str, float] = {}
        discovered_name: Optional[str] = None

        for row in reader:
            position = (row.get("position") or "").strip()
            if not position:
                # Interpret as metadata row.
                label = (row.get("name") or "").strip()
                if label and not discovered_name:
                    discovered_name = label
                for key, value in row.items():
                    alias = TEAM_FIELD_ALIASES.get(key.lower()) if key else None
                    if not alias or value in (None, ""):
                        continue
                    parsed = _parse_float(value)
                    if parsed is not None:
                        team_kwargs[alias] = parsed
                continue

            player_name = (row.get("name") or "").strip()
            if not player_name:
                raise TeamLoaderError(
                    f"Encountered a player row without a name while reading {path}."
                )

            metrics: Dict[str, float] = {}
            for key, value in row.items():
                if key is None or key.lower() in {"name", "position"}:
                    continue
                if value in (None, ""):
                    continue
                parsed = _parse_float(value)
                if parsed is not None:
                    metrics[key] = parsed

            players.append(Player(player_name, position.upper(), PlayerMetrics(metrics)))

    if not players:
        raise TeamLoaderError(f"No players were parsed from {path}.")

    team_name = name or discovered_name or team_kwargs.get("name") or _derive_team_name(path)
    team_kwargs.pop("name", None)

    if overrides:
        for key, value in overrides.items():
            if hasattr(Team, key):
                team_kwargs[key] = value

    return Team(team_name, players, **team_kwargs)
