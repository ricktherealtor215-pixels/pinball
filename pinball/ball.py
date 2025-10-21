"""Ball physics for the text pinball simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .board import Board, Position


@dataclass
class Ball:
    """Represents the moving ball on the play field."""

    x: float
    y: float
    vx: float
    vy: float
    gravity: float = 0.25
    max_speed: float = 3.5

    def step(self, board: Board, rng) -> Tuple[int, Optional[Position], bool]:
        """Advance the ball by a single frame.

        Returns a tuple ``(score, bumper_position, touched_floor)``.
        """

        self.vx += rng.uniform(-0.15, 0.15)
        self.vy += self.gravity
        self.vx = max(min(self.vx, self.max_speed), -self.max_speed)
        self.vy = max(min(self.vy, self.max_speed), -self.max_speed)

        next_x = self.x + self.vx
        next_y = self.y + self.vy

        touched_floor = False

        if next_x < 0:
            next_x = -next_x
            self.vx = abs(self.vx) * 0.85
        elif next_x > board.width - 1:
            next_x = 2 * (board.width - 1) - next_x
            self.vx = -abs(self.vx) * 0.85

        if next_y < 0:
            next_y = -next_y
            self.vy = abs(self.vy) * 0.85
        elif next_y > board.height - 1:
            next_y = board.height - 1
            self.vy = -abs(self.vy) * 0.6 - 0.4
            self.vx = (self.vx * 0.9) + rng.uniform(-0.7, 0.7)
            touched_floor = True

        tile = (int(round(next_x)), int(round(next_y)))
        if not board.is_bumper(tile):
            for candidate in board.bumpers:
                cx, cy = candidate
                if abs(next_x - cx) <= 0.45 and abs(next_y - cy) <= 0.45:
                    tile = candidate
                    break
        score = 0
        bumper_position: Optional[Position] = None
        if board.is_bumper(tile):
            score = board.register_hit(tile)
            bumper_position = tile
            if abs(self.vx) < 0.2:
                self.vx = rng.choice([-0.9, 0.9])
            else:
                self.vx = -self.vx * 0.8
            self.vx += rng.uniform(-0.3, 0.3)
            self.vy = -abs(self.vy) * 0.7 - 0.25
            next_x = self.x + self.vx * 0.5
            next_y = self.y + self.vy * 0.5

        self.x = max(0.0, min(board.width - 1, next_x))
        self.y = max(0.0, min(board.height - 1, next_y))
        return score, bumper_position, touched_floor


__all__ = ["Ball"]
