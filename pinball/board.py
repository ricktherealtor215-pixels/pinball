"""Board representation for the text pinball simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .ball import Ball

Position = Tuple[int, int]


@dataclass
class Bumper:
    """Description of a bumper on the play field."""

    symbol: str
    value: int
    cooldown_frames: int = 3
    cooldown: int = 0

    def hit(self) -> int:
        """Mark the bumper as hit and return its score value."""
        self.cooldown = self.cooldown_frames
        return self.value

    def tick(self) -> None:
        """Advance the cooldown animation."""
        if self.cooldown > 0:
            self.cooldown -= 1

    @property
    def display_symbol(self) -> str:
        """Return the character to display for the bumper."""
        if self.cooldown:
            return self.symbol.lower()
        return self.symbol


class Board:
    """Representation of the pinball board."""

    def __init__(self, width: int, height: int, bumpers: Iterable[Tuple[Position, Bumper]]):
        self.width = width
        self.height = height
        self.bumpers: Dict[Position, Bumper] = {pos: bumper for pos, bumper in bumpers}

    def is_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_bumper(self, position: Position) -> bool:
        return position in self.bumpers

    def register_hit(self, position: Position) -> int:
        return self.bumpers[position].hit()

    def tick(self) -> None:
        for bumper in self.bumpers.values():
            bumper.tick()

    def render(self, ball: "Ball", score: int, step: int, combo: int, message: str = "") -> str:
        grid = [["·" for _ in range(self.width)] for _ in range(self.height)]
        for (x, y), bumper in self.bumpers.items():
            grid[y][x] = bumper.display_symbol

        bx = max(0, min(self.width - 1, int(round(ball.x))))
        by = max(0, min(self.height - 1, int(round(ball.y))))
        grid[by][bx] = "●"

        lines = [
            f"Step {step + 1:02d} | Score: {score:05d} | Combo: x{combo}",
            "┌" + "─" * self.width + "┐",
        ]
        for row in grid:
            lines.append("│" + "".join(row) + "│")
        lines.append("└" + "─" * self.width + "┘")
        if message:
            lines.append(message)
        return "\n".join(lines)


__all__ = ["Bumper", "Board", "Position"]
