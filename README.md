# Pac-Man Like Game (Python)

A Pac-Man-inspired game built with **Python + Tkinter**, now with an AI-controlled Pac-Man that learns with **Q-Learning**.

## Run

```bash
python3 pacman_game.py
```

## What changed

- Pac-Man is controlled by a Q-learning agent (no manual movement controls).
- The agent uses epsilon-greedy exploration and updates its Q-table every game tick.
- Rewards are based on pellets, power pellets, eating ghosts, surviving, and avoiding death.
- The HUD shows learning stats (`ε` and training steps).

## Controls

- Press `R` to restart a run.

## Ghost AI

- **Blinky (red / chaser):** directly chases player
- **Pinky (pink / ambusher):** aims ahead of player movement
- **Inky (cyan / random):** mostly unpredictable
- **Clyde (orange / scatter):** tends toward lower-right area with occasional randomness
