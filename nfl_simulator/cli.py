"""Command line interface for the NFL simulator."""

from __future__ import annotations

import argparse
from typing import Dict, Iterable, Optional

from .data_loader import TeamLoaderError, load_team_from_csv
from .simulation import GameSimulator


def _parse_overrides(items: Optional[Iterable[str]]) -> Dict[str, float]:
    overrides: Dict[str, float] = {}
    if not items:
        return overrides
    for item in items:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"Override '{item}' must be in key=value format, e.g. home_field_advantage=1.2"
            )
        key, value = item.split("=", 1)
        try:
            overrides[key] = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Override '{item}' contains a non-numeric value."
            ) from exc
    return overrides


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate NFL matchups using roster metrics.")
    parser.add_argument("home", help="CSV file containing the home team's roster and metrics.")
    parser.add_argument("away", help="CSV file containing the away team's roster and metrics.")
    parser.add_argument("--iterations", type=int, default=5000, help="Number of Monte Carlo iterations to run.")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed for reproducibility.")
    parser.add_argument("--home-name", dest="home_name", default=None, help="Override for the home team name.")
    parser.add_argument("--away-name", dest="away_name", default=None, help="Override for the away team name.")
    parser.add_argument(
        "--home-override",
        dest="home_overrides",
        action="append",
        default=None,
        help="Override home team attributes (key=value). Repeat for multiple overrides.",
    )
    parser.add_argument(
        "--away-override",
        dest="away_overrides",
        action="append",
        default=None,
        help="Override away team attributes (key=value). Repeat for multiple overrides.",
    )
    parser.add_argument("--neutral-site", action="store_true", help="Remove built-in home field advantage.")
    parser.add_argument(
        "--spread",
        dest="spread_line",
        type=float,
        default=None,
        help="Point spread from the home team's perspective (negative means favorite).",
    )
    parser.add_argument(
        "--total",
        dest="total_line",
        type=float,
        default=None,
        help="Game total/over-under to evaluate.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    home_overrides = _parse_overrides(args.home_overrides)
    away_overrides = _parse_overrides(args.away_overrides)

    try:
        home_team = load_team_from_csv(args.home, name=args.home_name, overrides=home_overrides)
        away_team = load_team_from_csv(args.away, name=args.away_name, overrides=away_overrides)
    except TeamLoaderError as exc:
        parser.error(str(exc))
        return 2

    simulator = GameSimulator(home_team, away_team, neutral_site=args.neutral_site)
    result = simulator.simulate(
        iterations=args.iterations,
        seed=args.seed,
        spread_line=args.spread_line,
        total_line=args.total_line,
    )

    print(result.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
