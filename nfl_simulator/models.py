"""Core data structures for the NFL simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class PlayerMetrics:
    """Collection of numeric metrics describing a player's performance.

    The simulator intentionally keeps this structure generic so that users can
    map the columns from their preferred data source (such as the provided
    Google Sheet export) to the expected metric names. Common metrics include
    ``completion_pct``, ``yards_per_attempt``, ``success_rate``, and
    ``epa_per_play``. Metrics can be accessed with :meth:`get`.
    """

    values: Dict[str, float] = field(default_factory=dict)

    def get(self, key: str, default: float = 0.0) -> float:
        """Return the metric identified by *key*.

        Parameters
        ----------
        key:
            Name of the metric to retrieve.
        default:
            Value returned when the metric is missing. Defaults to ``0.0``.
        """

        return float(self.values.get(key, default))


@dataclass(frozen=True)
class Player:
    """Represents an NFL player and the metrics relevant to the simulation."""

    name: str
    position: str
    metrics: PlayerMetrics = field(default_factory=PlayerMetrics)

    def metric(self, key: str, default: float = 0.0) -> float:
        """Convenience wrapper that delegates to :class:`PlayerMetrics`."""

        return self.metrics.get(key, default)


@dataclass
class Team:
    """Container for team-level information used during simulation.

    Attributes
    ----------
    name:
        Display name for the team.
    players:
        Iterable of :class:`Player` objects representing the active roster.
    pace_per_game:
        Estimated number of offensive drives per game. Defaults to ``11.5``
        which matches recent NFL averages.
    coaching_aggressiveness:
        Modifier in the ``[0.8, 1.2]`` range describing the propensity to make
        aggressive play calls on fourth down and in the red zone. Higher values
        slightly increase scoring chances and play tempo.
    home_field_advantage:
        Advantage applied when the team is playing at home. Values between ``0``
        and ``2`` map to roughly ``0`` to ``2`` additional points per game.
    injury_adjustment:
        Global modifier in ``[0.6, 1.1]`` that down-weights team strength when
        key players are unavailable.
    """

    name: str
    players: Iterable[Player]
    pace_per_game: float = 11.5
    coaching_aggressiveness: float = 1.0
    home_field_advantage: float = 0.0
    injury_adjustment: float = 1.0

    def __post_init__(self) -> None:
        self.players = list(self.players)

    def players_by_position(self, *positions: str) -> List[Player]:
        """Return the players whose ``position`` attribute matches ``positions``."""

        normalized = {pos.upper() for pos in positions}
        return [player for player in self.players if player.position.upper() in normalized]

    def offensive_players(self) -> List[Player]:
        """Return players considered offensive contributors."""

        return self.players_by_position("QB", "RB", "FB", "WR", "TE", "OL")

    def defensive_players(self) -> List[Player]:
        """Return players considered defensive contributors."""

        return self.players_by_position("DL", "DE", "DT", "LB", "CB", "S", "NB")

    def special_teams_players(self) -> List[Player]:
        """Return special teams contributors such as kickers and punters."""

        return self.players_by_position("K", "P", "KR", "PR", "LS")

    def metric_average(self, metric_name: str, *, positions: Optional[Iterable[str]] = None,
                       default: float = 0.0) -> float:
        """Return the average value for ``metric_name`` across selected players."""

        if positions:
            relevant = self.players_by_position(*positions)
        else:
            relevant = list(self.players)
        if not relevant:
            return default
        return sum(player.metric(metric_name, default) for player in relevant) / len(relevant)
