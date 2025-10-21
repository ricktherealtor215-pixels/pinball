from pinball import run_game


def test_run_game_deterministic():
    result = run_game(steps=60, seed=7, display=False)
    assert result.score == 1125
    assert result.total_hits == 4
    assert result.max_combo == 2
    assert result.steps == 60
    assert len(result.frames) == 60
