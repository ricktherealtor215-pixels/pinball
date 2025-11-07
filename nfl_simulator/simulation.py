"""Game simulation engine."""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .models import Team
from .team_strength import TeamStrength, estimate_team_strength


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if q <= 0:
        return sorted_values[0]
    if q >= 1:
        return sorted_values[-1]
    position = (len(sorted_values) - 1) * q
    lower_index = int(math.floor(position))
    upper_index = int(math.ceil(position))
    if lower_index == upper_index:
        return sorted_values[lower_index]
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    weight = position - lower_index
    return lower_value + (upper_value - lower_value) * weight


@dataclass(frozen=True)
class SimulationResult:
    """Outcome summary of a Monte Carlo simulation."""

    home_team: str
    away_team: str
    iterations: int
    home_win_prob: float
    away_win_prob: float
    tie_prob: float
    expected_home_score: float
    expected_away_score: float
    expected_total: float
    expected_margin: float
    score_quantiles: Dict[str, Dict[str, float]]
    spread_line: Optional[float]
    home_cover_prob: Optional[float]
    total_line: Optional[float]
    over_prob: Optional[float]

    def summary(self) -> str:
        lines = [
            f"Simulated {self.iterations} games between {self.home_team} (home) and {self.away_team}.",
            f"Win probabilities — {self.home_team}: {self.home_win_prob:.1%}, {self.away_team}: {self.away_win_prob:.1%}, tie: {self.tie_prob:.1%}.",
            f"Expected score: {self.away_team} {self.expected_away_score:.1f} @ {self.home_team} {self.expected_home_score:.1f}",
            f"Expected margin: {self.home_team} by {self.expected_margin:+.1f} (total {self.expected_total:.1f}).",
        ]
        if self.spread_line is not None and self.home_cover_prob is not None:
            lines.append(
                f"Home team cover probability vs spread {self.spread_line:+.1f}: {self.home_cover_prob:.1%}."
            )
        if self.total_line is not None and self.over_prob is not None:
            lines.append(
                f"Probability of total going over {self.total_line:.1f}: {self.over_prob:.1%}."
            )
        home_quantiles = ", ".join(
            f"{label}: {value:.1f}" for label, value in self.score_quantiles.get("home", {}).items()
        )
        away_quantiles = ", ".join(
            f"{label}: {value:.1f}" for label, value in self.score_quantiles.get("away", {}).items()
        )
        margin_quantiles = ", ".join(
            f"{label}: {value:+.1f}" for label, value in self.score_quantiles.get("margin", {}).items()
        )
        lines.append(f"Home score quantiles — {home_quantiles}")
        lines.append(f"Away score quantiles — {away_quantiles}")
        lines.append(f"Margin quantiles — {margin_quantiles}")
        return "\n".join(lines)


class GameSimulator:
    """Monte Carlo simulator for NFL games."""

    def __init__(self, home_team: Team, away_team: Team, *, neutral_site: bool = False) -> None:
        self.home_team = home_team
        self.away_team = away_team
        self.neutral_site = neutral_site
        self.home_strength = estimate_team_strength(home_team)
        self.away_strength = estimate_team_strength(away_team)
        base_home_edge = 0.18 if not neutral_site else 0.0
        base_home_edge += 0.04 * _clamp(home_team.home_field_advantage, 0.0, 2.5)
        self.home_drive_boost = base_home_edge

    def simulate(
        self,
        iterations: int = 5000,
        *,
        seed: Optional[int] = None,
        spread_line: Optional[float] = None,
        total_line: Optional[float] = None,
    ) -> SimulationResult:
        rng = random.Random(seed)
        home_scores: List[int] = []
        away_scores: List[int] = []
        margins: List[int] = []
        totals: List[int] = []
        home_wins = 0
        away_wins = 0
        ties = 0

        for _ in range(iterations):
            home, away = self._simulate_single_game(rng)
            home_scores.append(home)
            away_scores.append(away)
            margin = home - away
            total = home + away
            margins.append(margin)
            totals.append(total)
            if home > away:
                home_wins += 1
            elif away > home:
                away_wins += 1
            else:
                ties += 1

        home_scores_sorted = sorted(home_scores)
        away_scores_sorted = sorted(away_scores)
        margin_sorted = sorted(margins)

        score_quantiles = {
            "home": {
                "p10": _quantile(home_scores_sorted, 0.10),
                "p50": _quantile(home_scores_sorted, 0.50),
                "p90": _quantile(home_scores_sorted, 0.90),
            },
            "away": {
                "p10": _quantile(away_scores_sorted, 0.10),
                "p50": _quantile(away_scores_sorted, 0.50),
                "p90": _quantile(away_scores_sorted, 0.90),
            },
            "margin": {
                "p10": _quantile(margin_sorted, 0.10),
                "p50": _quantile(margin_sorted, 0.50),
                "p90": _quantile(margin_sorted, 0.90),
            },
        }

        home_cover_prob = None
        over_prob = None
        if spread_line is not None:
            home_cover_prob = sum(1 for margin in margins if margin > -spread_line) / iterations
        if total_line is not None:
            over_prob = sum(1 for total in totals if total > total_line) / iterations

        return SimulationResult(
            home_team=self.home_team.name,
            away_team=self.away_team.name,
            iterations=iterations,
            home_win_prob=home_wins / iterations,
            away_win_prob=away_wins / iterations,
            tie_prob=ties / iterations,
            expected_home_score=statistics.mean(home_scores),
            expected_away_score=statistics.mean(away_scores),
            expected_total=statistics.mean(totals),
            expected_margin=statistics.mean(margins),
            score_quantiles=score_quantiles,
            spread_line=spread_line,
            home_cover_prob=home_cover_prob,
            total_line=total_line,
            over_prob=over_prob,
        )

    def _estimate_drive_counts(self, rng: random.Random) -> Tuple[int, int]:
        combined_pace = self.home_team.pace_per_game + self.away_team.pace_per_game
        if combined_pace <= 0:
            combined_pace = 22.0
        combined_drives = int(round(rng.gauss(combined_pace, 2.2)))
        combined_drives = int(_clamp(combined_drives, 16, 28))
        home_share = self.home_team.pace_per_game / combined_pace
        home_drives = max(8, int(round(combined_drives * home_share)))
        away_drives = max(8, combined_drives - home_drives)
        return home_drives, away_drives

    def _simulate_single_game(self, rng: random.Random) -> Tuple[int, int]:
        home_drives, away_drives = self._estimate_drive_counts(rng)
        home_points = 0
        away_points = 0

        for drive_index in range(max(home_drives, away_drives)):
            if drive_index < home_drives:
                gained, conceded = self._simulate_drive(
                    self.home_strength,
                    self.away_strength,
                    rng,
                    is_home=True,
                )
                home_points += gained
                away_points += conceded
            if drive_index < away_drives:
                gained, conceded = self._simulate_drive(
                    self.away_strength,
                    self.home_strength,
                    rng,
                    is_home=False,
                )
                away_points += gained
                home_points += conceded

        # Simple overtime model: each team gets one more drive. If still tied, allow tie.
        if home_points == away_points:
            gained, conceded = self._simulate_drive(
                self.home_strength,
                self.away_strength,
                rng,
                is_home=True,
                overtime=True,
            )
            home_points += gained
            away_points += conceded
            if home_points == away_points:
                gained, conceded = self._simulate_drive(
                    self.away_strength,
                    self.home_strength,
                    rng,
                    is_home=False,
                    overtime=True,
                )
                away_points += gained
                home_points += conceded

        return int(round(home_points)), int(round(away_points))

    def _simulate_drive(
        self,
        offense: TeamStrength,
        defense: TeamStrength,
        rng: random.Random,
        *,
        is_home: bool,
        overtime: bool = False,
    ) -> Tuple[float, float]:
        advantage = offense.offensive - (defense.defensive)
        pass_diff = offense.passing_offense - (defense.pass_defense)
        rush_diff = offense.rushing_offense - (defense.rush_defense)
        explosive_diff = offense.explosive_play - (1.0 - defense.pass_defense)
        special_diff = offense.special_teams - defense.special_teams
        aggression = _clamp(offense.offensive + offense.explosive_play, 0.0, 2.0)
        coaching_boost = _clamp(aggression - 0.9, -0.3, 0.4)

        base_td = 0.22
        base_fg = 0.095
        base_turnover = 0.12
        if overtime:
            base_td -= 0.02
            base_fg += 0.01

        drive_variance = rng.gauss(0.0, 0.03)
        home_edge = self.home_drive_boost if is_home else 0.0

        touchdown_prob = _clamp(
            base_td
            + 0.22 * advantage
            + 0.18 * pass_diff
            + 0.10 * rush_diff
            + 0.12 * explosive_diff
            + 0.06 * coaching_boost
            + 0.04 * special_diff
            + home_edge
            + drive_variance,
            0.05,
            0.75,
        )
        field_goal_prob = _clamp(
            base_fg
            + 0.10 * advantage
            + 0.05 * rush_diff
            + 0.04 * special_diff
            + 0.02 * coaching_boost
            + drive_variance / 2,
            0.02,
            0.35,
        )
        turnover_prob = _clamp(
            base_turnover
            - 0.08 * advantage
            - 0.04 * rush_diff
            + 0.12 * (defense.defensive - 0.5)
            + 0.06 * (defense.pass_defense - 0.5)
            - 0.03 * special_diff,
            0.05,
            0.30,
        )
        safety_prob = _clamp(0.01 + 0.04 * (defense.defensive - 0.5) - 0.03 * rush_diff, 0.0, 0.03)

        cumulative = touchdown_prob
        roll = rng.random()
        team_points = 0.0
        opponent_points = 0.0
        if roll < cumulative:
            two_point_prob = _clamp(0.03 + 0.05 * (coaching_boost), 0.0, 0.25)
            go_for_two = rng.random() < two_point_prob
            if go_for_two:
                conversion_prob = _clamp(0.46 + 0.18 * (pass_diff + rush_diff) / 2, 0.30, 0.70)
                team_points += 6
                if rng.random() < conversion_prob:
                    team_points += 2
            else:
                xp_prob = _clamp(0.92 + 0.10 * special_diff, 0.88, 0.99)
                team_points += 6
                if rng.random() < xp_prob:
                    team_points += 1
        else:
            cumulative += field_goal_prob
            if roll < cumulative:
                fg_success = _clamp(0.85 + 0.10 * special_diff, 0.75, 0.99)
                if rng.random() < fg_success:
                    team_points += 3
            else:
                cumulative += turnover_prob
                if roll < cumulative:
                    # Turnover outcomes occasionally translate into defensive points.
                    def_td_prob = _clamp(
                        0.08 + 0.12 * (defense.pass_defense - 0.5) + 0.05 * (defense.explosive_play - 0.5),
                        0.02,
                        0.25,
                    )
                    if rng.random() < def_td_prob:
                        opponent_points += 7
                    else:
                        def_fg_prob = _clamp(
                            0.20 + 0.18 * (defense.defensive - 0.5) + 0.05 * (defense.special_teams - 0.5),
                            0.05,
                            0.45,
                        )
                        if rng.random() < def_fg_prob:
                            opponent_points += 3
                else:
                    if rng.random() < safety_prob:
                        opponent_points += 2

        return team_points, opponent_points
