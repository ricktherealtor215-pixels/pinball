"""Translate player metrics into team-level strength estimates."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .models import Player, Team


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _normalize_pct(value: float) -> float:
    if value is None:
        return 0.0
    if value > 1.5:
        return value / 100.0
    return value


def _average_metric(players: Iterable[Player], metric_name: str, default: float) -> float:
    players = list(players)
    if not players:
        return default
    total = 0.0
    for player in players:
        total += player.metric(metric_name, default)
    return total / len(players)


@dataclass(frozen=True)
class TeamStrength:
    """Summary of offensive, defensive, and special teams strength."""

    offensive: float
    passing_offense: float
    rushing_offense: float
    explosive_play: float
    defensive: float
    pass_defense: float
    rush_defense: float
    special_teams: float

    def adjust(self, multiplier: float) -> "TeamStrength":
        return TeamStrength(
            offensive=self.offensive * multiplier,
            passing_offense=self.passing_offense * multiplier,
            rushing_offense=self.rushing_offense * multiplier,
            explosive_play=self.explosive_play * multiplier,
            defensive=self.defensive * multiplier,
            pass_defense=self.pass_defense * multiplier,
            rush_defense=self.rush_defense * multiplier,
            special_teams=self.special_teams * multiplier,
        )


def estimate_team_strength(team: Team) -> TeamStrength:
    """Estimate team strengths from roster metrics.

    The heuristics in this function combine commonly available efficiency
    metrics and per-play numbers. They are intentionally conservative so that
    missing data keeps teams close to league average. All returned values are
    normalized to roughly ``0`` (poor) through ``1`` (elite) with ``0.5``
    representing league average.
    """

    qb = team.players_by_position("QB")
    running_backs = team.players_by_position("RB", "FB")
    receivers = team.players_by_position("WR", "TE")
    offensive_line = team.players_by_position("OL")
    front_seven = team.players_by_position("DL", "DE", "DT", "LB")
    secondary = team.players_by_position("CB", "S", "NB")
    specialists = team.players_by_position("K", "P", "KR", "PR")

    qb_completion = _normalize_pct(_average_metric(qb, "completion_pct", 0.64))
    qb_ypa = _average_metric(qb, "yards_per_attempt", 7.3)
    qb_td_rate = _normalize_pct(_average_metric(qb, "touchdown_rate", 0.045))
    qb_int_rate = _normalize_pct(_average_metric(qb, "interception_rate", 0.025))
    qb_epa = _average_metric(qb, "epa_per_play", 0.10)
    qb_success = _average_metric(qb, "success_rate", 0.47)

    wr_success = _average_metric(receivers, "success_rate", 0.50)
    wr_yprr = _average_metric(receivers, "yards_per_route_run", 1.75)
    wr_explosive = _average_metric(receivers, "explosive_rate", 0.14)

    rb_ypr = _average_metric(running_backs, "yards_per_attempt", 4.3)
    rb_success = _average_metric(running_backs, "success_rate", 0.43)
    rb_explosive = _average_metric(running_backs, "explosive_rate", 0.11)

    ol_pass_block = _normalize_pct(_average_metric(offensive_line, "pass_block_win_rate", 0.56))
    ol_run_block = _normalize_pct(_average_metric(offensive_line, "run_block_win_rate", 0.72))

    pass_rating = _logistic(
        3.2 * (qb_completion - 0.64) / 0.05
        + 2.4 * (qb_ypa - 7.3) / 0.7
        + 2.3 * (qb_td_rate - 0.045) / 0.015
        - 2.0 * (qb_int_rate - 0.025) / 0.01
        + 1.6 * (qb_epa - 0.10) / 0.07
        + 1.3 * (wr_success - 0.50) / 0.05
        + 1.1 * (wr_yprr - 1.75) / 0.35
        + 0.9 * (wr_explosive - 0.14) / 0.04
        + 1.0 * (ol_pass_block - 0.56) / 0.05
    )

    rush_rating = _logistic(
        2.4 * (rb_ypr - 4.3) / 0.4
        + 1.7 * (rb_success - 0.43) / 0.05
        + 1.1 * (rb_explosive - 0.11) / 0.03
        + 1.0 * (ol_run_block - 0.72) / 0.05
        + 0.6 * (qb_success - 0.47) / 0.05
    )

    explosive_rating = _logistic(
        1.5 * (wr_explosive - 0.14) / 0.04
        + 1.1 * (rb_explosive - 0.11) / 0.03
        + 0.9 * (qb_ypa - 7.3) / 0.7
    )

    offensive_rating = 0.62 * pass_rating + 0.38 * rush_rating

    pressure_rate = _normalize_pct(_average_metric(front_seven, "pressure_rate", 0.23))
    pass_rush_win = _normalize_pct(_average_metric(front_seven, "pass_rush_win_rate", 0.45))
    run_stop_win = _normalize_pct(_average_metric(front_seven, "run_stop_win_rate", 0.32))

    coverage_success = 1 - _normalize_pct(
        _average_metric(secondary, "success_rate_allowed", 0.47)
    )
    coverage_grade = _average_metric(secondary, "coverage_grade", 65.0)
    interceptions = _average_metric(secondary, "interception_rate", 0.028)
    pass_epa_allowed = -_average_metric(secondary, "epa_per_play_allowed", -0.04)

    rush_epa_allowed = -_average_metric(front_seven, "rush_epa_allowed", -0.01)
    yards_per_carry_allowed = 4.3 - _average_metric(front_seven, "yards_per_carry_allowed", 4.3)
    rush_success_allowed = 1 - _normalize_pct(
        _average_metric(front_seven, "rush_success_allowed", 0.43)
    )

    pass_defense_rating = _logistic(
        2.0 * (coverage_success - 0.53) / 0.05
        + 1.4 * (pressure_rate - 0.23) / 0.05
        + 1.1 * (pass_rush_win - 0.45) / 0.05
        + 1.0 * (coverage_grade - 65.0) / 5.0
        + 1.2 * (interceptions - 0.028) / 0.01
        + 1.6 * (pass_epa_allowed - 0.04) / 0.05
    )

    rush_defense_rating = _logistic(
        1.5 * (run_stop_win - 0.32) / 0.05
        + 1.2 * (rush_epa_allowed - 0.01) / 0.03
        + 1.1 * (yards_per_carry_allowed - 0.0) / 0.3
        + 1.0 * (rush_success_allowed - 0.57) / 0.05
    )

    defensive_rating = 0.6 * pass_defense_rating + 0.4 * rush_defense_rating

    fg_pct = _normalize_pct(_average_metric(specialists, "field_goal_pct", 0.86))
    punt_epa = _average_metric(specialists, "punt_epa", 0.0)
    kick_return = _average_metric(specialists, "kick_return_epa", 0.0)

    special_teams_rating = _logistic(
        1.6 * (fg_pct - 0.86) / 0.05
        + 0.9 * (punt_epa - 0.0) / 0.1
        + 0.8 * (kick_return - 0.0) / 0.08
    )

    injury_multiplier = max(0.6, min(1.1, team.injury_adjustment))

    return TeamStrength(
        offensive=offensive_rating * injury_multiplier,
        passing_offense=pass_rating * injury_multiplier,
        rushing_offense=rush_rating * injury_multiplier,
        explosive_play=explosive_rating * injury_multiplier,
        defensive=defensive_rating * injury_multiplier,
        pass_defense=pass_defense_rating * injury_multiplier,
        rush_defense=rush_defense_rating * injury_multiplier,
        special_teams=special_teams_rating * injury_multiplier,
    )
