# Pinball

A lightweight, text-based pinball simulation that runs in the terminal. The
ball bounces around a compact board, lighting bumpers and building combos to
boost your score.

## Running the game

```bash
python main.py
```

The game prints each frame to the terminal. You can edit `main.py` or call
`pinball.run_game(display=False)` from a Python session if you only want the
numerical results.

## Tests

Run the deterministic simulation test with:

```bash
pytest
```
