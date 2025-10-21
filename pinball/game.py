"""Entry points for running the pinball simulation."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

from .ball import Ball
from .board import Board, Bumper, Position
from .score import ScoreTracker


@dataclass
class GameResult:
    """Summary information for a completed simulation."""

    score: int
    total_hits: int
    max_combo: int
    steps: int
    frames: List[str]


def create_default_board() -> Board:
    """Create a board with a hand-authored bumper layout."""

    layout: Iterable[tuple[Position, Bumper]] = [
        ((3, 3), Bumper("A", 50)),
        ((9, 3), Bumper("A", 50)),
        ((6, 4), Bumper("B", 75)),
        ((2, 7), Bumper("C", 125)),
        ((5, 6), Bumper("B", 75)),
        ((7, 6), Bumper("B", 75)),
        ((9, 7), Bumper("C", 125)),
        ((3, 8), Bumper("C", 125)),
        ((6, 9), Bumper("D", 175)),
        ((5, 10), Bumper("D", 175)),
        ((7, 10), Bumper("D", 175)),
        ((4, 12), Bumper("E", 200)),
        ((8, 12), Bumper("E", 200)),
        ((6, 14), Bumper("F", 250)),
    ]
    return Board(width=13, height=16, bumpers=layout)


def run_game(
    steps: int = 80,
    *,
    seed: Optional[int] = None,
    display: bool = True,
    frame_delay: float = 0.0,
) -> GameResult:
    """Run the simulation and optionally render frames to stdout."""

    rng = random.Random(seed)
    board = create_default_board()
    ball = Ball(
        x=board.width / 2,
        y=1.0,
        vx=rng.choice([-1.05, -0.75, 0.75, 1.05]),
        vy=0.0,
    )

    tracker = ScoreTracker()
    frames: List[str] = []
    steps_since_hit = 0

    for step in range(steps):
        board.tick()
        base_value, bumper_position, touched_floor = ball.step(board, rng)

        message = ""
        if base_value:
            gained = tracker.apply_hit(base_value)
            steps_since_hit = 0
            message = f"Hit bumper at {bumper_position}! +{gained}"
        else:
            steps_since_hit += 1
            if touched_floor or steps_since_hit >= 6:
                if tracker.combo:
                    message = "Combo lost!"
                tracker.reset_combo()
                steps_since_hit = 0 if touched_floor else steps_since_hit

        frame = board.render(ball, tracker.score, step, tracker.combo, message)
        frames.append(frame)
        if display:
            print(frame)
            if frame_delay:
                time.sleep(frame_delay)

    return GameResult(
        score=tracker.score,
        total_hits=tracker.hits,
        max_combo=tracker.max_combo,
        steps=len(frames),
        frames=frames,
    )


__all__ = ["GameResult", "create_default_board", "run_game"]
