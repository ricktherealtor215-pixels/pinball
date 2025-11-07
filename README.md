# NFL Game Simulator

This repository provides a Monte Carlo simulator for NFL matchups. The engine
translates player-level metrics into team strengths and then simulates drives
and scoring events to project game outcomes.

## Features

- Flexible CSV ingestion that works with the shared Google Sheet export (use
  **File → Download → Comma Separated Values** to obtain a CSV).
- Heuristic model that converts player efficiency numbers into team-wide
  passing, rushing, defensive, and special teams ratings.
- Drive-by-drive simulation with touchdown, field goal, turnover, and overtime
  logic to approximate real game flow.
- Command line interface for running matchups, computing win probabilities,
  and evaluating spreads or totals.

## Getting Started

1. Export the roster and metric data for each team as CSV files. The loader
   expects at minimum the columns `name` and `position`. Additional numeric
   columns are interpreted as metrics (for example `completion_pct`,
   `yards_per_attempt`, `epa_per_play`, `pressure_rate`, etc.). Optional rows
   without a `position` value can store team-level metadata such as
   `pace_per_game` or `home_field_advantage`.
2. Run the simulator:

   ```bash
   python -m nfl_simulator path/to/home_team.csv path/to/away_team.csv \
       --iterations 10000 --spread -3.5 --total 47.5
   ```

   Add `--neutral-site` to remove built-in home field advantage, or use
   `--home-override coaching_aggressiveness=1.1` to tweak team attributes.

### Sample data

The `data/` directory contains two mock rosters, `springfield_atoms.csv` and
`shelbyville_sharks.csv`, that exercise the CSV ingestion pipeline without
requiring access to the shared spreadsheet. Run them against each other with:

```bash
python -m nfl_simulator data/springfield_atoms.csv data/shelbyville_sharks.csv \
    --iterations 2000 --spread -3.5 --total 47.5
```

## Module Overview

- `nfl_simulator.models`: Dataclasses for players and teams.
- `nfl_simulator.data_loader`: CSV ingestion helpers.
- `nfl_simulator.team_strength`: Converts metrics into normalized strengths.
- `nfl_simulator.simulation`: Drive-level Monte Carlo engine.
- `nfl_simulator.cli`: Command line parsing and program entry point.

## Development

The project uses only the Python standard library. Run the simulator's CLI as a
sanity check during development:

```bash
python -m nfl_simulator --help
```
