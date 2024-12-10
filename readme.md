
# Flappy Bird Command Line Edition

This is a minimalist **console-based adaptation** of the classic Flappy Bird game, rendered in text form using Python's `curses` library. Navigate a small bird through columns of ASCII obstacles and try to achieve the highest score possible.

## Features

- **Simple Controls**: Press *Space* or *Up Arrow* to flap the bird and gain altitude.
- **Obstacles**: Generate randomized columns at spaced intervals. Survive as long as you can.
- **Themes & Flavors**: The game changes its color theme and background flavor text as your score increases.
- **High Score Persistence**: Uses a SQLite database (`highscores.db`) to track and store your best score.
- **Restart or Quit**: When the game ends, press **R** to restart immediately or **Q** to quit.

![image](https://github.com/user-attachments/assets/8d2d2f0a-d7f7-4d53-a4bd-979087b918ee)


## Requirements

- Python 3.x
- `curses` (usually pre-installed on Unix-like systems)
- `sqlite3` (standard with Python)
  

## Usage

Run the game from your terminal:

```bash
python flappy_bird.py
```

When the intro screen appears, press *Space* to start.  
Avoid obstacles by flapping and keep track of your score at the top-right.  
After a game over, check your new high score, press **R** to try again, or **Q** to exit.

---
