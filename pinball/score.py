"""Score tracking utilities."""

from dataclasses import dataclass


@dataclass
class ScoreTracker:
    """Maintain the score and combo state for the game."""

    score: int = 0
    hits: int = 0
    combo: int = 0
    max_combo: int = 0

    def apply_hit(self, base_value: int) -> int:
        self.hits += 1
        self.combo += 1
        if self.combo > self.max_combo:
            self.max_combo = self.combo
        gained = base_value * self.combo
        self.score += gained
        return gained

    def reset_combo(self) -> None:
        self.combo = 0


__all__ = ["ScoreTracker"]
