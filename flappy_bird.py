import curses, time, sys, random, sqlite3
from curses import wrapper

TICK_RATE = 0.08
GRAVITY = 0.4
FLAP_STRENGTH = -1.4
BIRD_X = 10
OBSTACLE_SPACING = 20
GAP_SIZE = 6
SCORE_OFFSET = 2
THEMES = [
    (curses.COLOR_BLUE, curses.COLOR_YELLOW, "▓", "A gentle morning breeze...", curses.COLOR_CYAN),
    (curses.COLOR_MAGENTA, curses.COLOR_WHITE, "▒", "Twilight whispers secrets...", curses.COLOR_RED),
    (curses.COLOR_CYAN, curses.COLOR_GREEN, "█", "Neon dreams flicker by...", curses.COLOR_MAGENTA),
]

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    fg_colors = [curses.COLOR_WHITE, curses.COLOR_YELLOW, curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_RED, curses.COLOR_MAGENTA]
    for i, fg in enumerate(fg_colors, start=1):
        curses.init_pair(i, fg, -1)

def color_pair_for_fg(stdscr, fg):
    return curses.color_pair({
        curses.COLOR_WHITE: 1,
        curses.COLOR_YELLOW: 2,
        curses.COLOR_CYAN: 3,
        curses.COLOR_GREEN: 4,
        curses.COLOR_RED: 5,
        curses.COLOR_MAGENTA: 6
    }.get(fg, 1))

def clear_screen(stdscr):
    stdscr.clear()

def draw_text_center(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = (w - len(text)) // 2
    stdscr.addstr(y, x, text, attr)

class Bird:
    def __init__(self, y, theme):
        self.x = BIRD_X
        self.y = y
        self.vy = 0
        self.char_frames = ["<", "v", "^"]
        self.frame_index = 0
        self.theme = theme

    def flap(self):
        self.vy = FLAP_STRENGTH
        self.frame_index = (self.frame_index + 1) % len(self.char_frames)

    def update(self):
        self.vy += GRAVITY
        self.y += self.vy

    def draw(self, stdscr):
        char = self.char_frames[self.frame_index]
        color = color_pair_for_fg(stdscr, THEMES[self.theme][1])
        try:
            stdscr.addstr(int(self.y), self.x, char, color)
        except:
            pass

class Obstacle:
    def __init__(self, x, gap_y, gap_size, theme):
        self.x = x
        self.gap_y = gap_y
        self.gap_size = gap_size
        self.theme = theme
        self.width = 5

    def update(self):
        self.x -= 1

    def draw(self, stdscr):
        h, w = stdscr.getmaxyx()
        obs_color = color_pair_for_fg(stdscr, curses.COLOR_WHITE)

        top_end = self.gap_y - 1
        bottom_start = self.gap_y + self.gap_size
        
        # Top segment
        if top_end >= 0:
            try:
                stdscr.addstr(0, self.x, "┌" + "───" + "┐", obs_color)
            except:
                pass
            for yy in range(1, top_end+1):
                if yy < h:
                    try:
                        stdscr.addstr(yy, self.x, "│   │", obs_color)
                    except:
                        pass

        # Bottom segment
        if bottom_start < h:
            for yy in range(bottom_start, h-1):
                if yy >= 0:
                    try:
                        stdscr.addstr(yy, self.x, "│   │", obs_color)
                    except:
                        pass
            if h-1 >= bottom_start:
                try:
                    stdscr.addstr(h-1, self.x, "└" + "───" + "┘", obs_color)
                except:
                    pass

    def collision(self, bird_y):
        return not (self.gap_y <= int(bird_y) < self.gap_y + self.gap_size)

class Particle:
    def __init__(self, x, y, char, color_pair, lifetime=5):
        self.x = x
        self.y = y
        self.char = char
        self.color_pair = color_pair
        self.lifetime = lifetime

    def update(self):
        self.x -= 1
        self.lifetime -= 1

    def draw(self, stdscr):
        if 0 < self.lifetime:
            try:
                stdscr.addstr(int(self.y), int(self.x), self.char, self.color_pair)
            except:
                pass

    def alive(self):
        return self.lifetime > 0


# --------------------
# SQLite High Score Functions
# --------------------
def init_db():
    conn = sqlite3.connect('highscores.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS highscore (id INTEGER PRIMARY KEY, score INTEGER)''')
    conn.commit()
    # Ensure at least one entry
    cur.execute("SELECT score FROM highscore WHERE id=1")
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO highscore (id, score) VALUES (1, 0)")
        conn.commit()
    conn.close()

def get_high_score():
    conn = sqlite3.connect('highscores.db')
    cur = conn.cursor()
    cur.execute("SELECT score FROM highscore WHERE id=1")
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return 0

def set_high_score(new_score):
    conn = sqlite3.connect('highscores.db')
    cur = conn.cursor()
    cur.execute("UPDATE highscore SET score=? WHERE id=1", (new_score,))
    conn.commit()
    conn.close()

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    init_colors()
    init_db()  # Initialize db and ensure high score table exists
    
    while True:  # This loop allows restarting after game over
        h, w = stdscr.getmaxyx()

        current_theme = 0
        bg_color, bird_color, obs_char, flavor_text, particle_color = THEMES[current_theme]

        bird = Bird(h//2, current_theme)
        obstacles = []
        for i in range(5):
            gap_pos = random.randint(5, h-5-GAP_SIZE)
            obstacles.append(Obstacle(w + i*OBSTACLE_SPACING, gap_pos, GAP_SIZE, current_theme))

        score = 0
        particles = []
        game_over = False
        theme_transition_score = 20
        rare_event_triggered = False
        last_time = time.time()

        # Intro screen
        clear_screen(stdscr)
        draw_text_center(stdscr, h//2 - 2, "~~ Flappy Bird Console Edition ~~", color_pair_for_fg(stdscr, curses.COLOR_YELLOW))
        draw_text_center(stdscr, h//2, "Press SPACE to start flapping...", color_pair_for_fg(stdscr, curses.COLOR_CYAN))
        stdscr.refresh()

        while True:
            ch = stdscr.getch()
            if ch == ord(' ') or ch == curses.KEY_UP:
                break
            time.sleep(0.05)

        while True:
            ch = stdscr.getch()
            if ch == ord('q'):
                # If user presses Q mid-game, quit entirely
                return
            if (ch == ord(' ') or ch == curses.KEY_UP) and not game_over:
                bird.flap()

            if not game_over:
                bird.update()
                for o in obstacles:
                    o.update()

                if obstacles and obstacles[0].x < 0:
                    obstacles.pop(0)
                    gap_pos = random.randint(5, h-5-GAP_SIZE)
                    obstacles.append(Obstacle(obstacles[-1].x + OBSTACLE_SPACING, gap_pos, GAP_SIZE, current_theme))
                    score += 1

                if int(bird.y) < 0 or int(bird.y) >= h:
                    game_over = True
                else:
                    for o in obstacles:
                        if o.x <= bird.x < o.x + o.width:
                            if o.collision(bird.y):
                                game_over = True
                                for _ in range(20):
                                    py = bird.y + random.randint(-2, 2)
                                    px = bird.x + random.randint(-1, 1)
                                    particles.append(Particle(px, py, "*", color_pair_for_fg(stdscr, particle_color), lifetime=random.randint(2,6)))
                                break

                if score > 0 and score % theme_transition_score == 0 and score <= theme_transition_score * len(THEMES):
                    new_theme_index = (score // theme_transition_score) % len(THEMES)
                    if new_theme_index != current_theme:
                        current_theme = new_theme_index
                        bg_color, bird_color, obs_char, flavor_text, particle_color = THEMES[current_theme]
                        for o in obstacles:
                            o.theme = current_theme
                        bird.theme = current_theme

                if score > 10 and not rare_event_triggered and random.random() < 0.002:
                    rare_event_triggered = True
                    for runex in range(w//2, w//2+10):
                        particles.append(Particle(runex, h//3, random.choice(["@", "#", "&"]), color_pair_for_fg(stdscr, curses.COLOR_MAGENTA), lifetime=10))

            for p in particles:
                p.update()
            particles = [p for p in particles if p.alive()]

            clear_screen(stdscr)
            for yy in range(h):
                shade = " "
                try:
                    stdscr.addstr(yy, 0, shade * w, color_pair_for_fg(stdscr, bg_color))
                except:
                    pass

            if score % (theme_transition_score//2) == 0 and score != 0:
                draw_text_center(stdscr, 1, flavor_text, color_pair_for_fg(stdscr, curses.COLOR_YELLOW))

            for o in obstacles:
                o.draw(stdscr)

            bird.draw(stdscr)

            for p in particles:
                p.draw(stdscr)

            score_str = f" Score: {score} "
            frame_char = "~"
            score_line = frame_char * (len(score_str) + 2)
            stdscr.addstr(SCORE_OFFSET, w-len(score_line)-2, score_line, color_pair_for_fg(stdscr, curses.COLOR_CYAN))
            stdscr.addstr(SCORE_OFFSET+1, w-len(score_line)-2, frame_char + score_str + frame_char, color_pair_for_fg(stdscr, curses.COLOR_CYAN))
            stdscr.addstr(SCORE_OFFSET+2, w-len(score_line)-2, score_line, color_pair_for_fg(stdscr, curses.COLOR_CYAN))

            if game_over:
                # Update high score if needed
                current_high = get_high_score()
                if score > current_high:
                    set_high_score(score)
                    current_high = score

                draw_text_center(stdscr, h//2, "GAME OVER", color_pair_for_fg(stdscr, curses.COLOR_RED))
                draw_text_center(stdscr, h//2+1, f"Your Score: {score}  |  High Score: {current_high}", color_pair_for_fg(stdscr, curses.COLOR_WHITE))
                draw_text_center(stdscr, h//2+3, "Press R to Restart or Q to Quit", color_pair_for_fg(stdscr, curses.COLOR_WHITE))
                stdscr.refresh()

                # Wait for R or Q
                while True:
                    end_ch = stdscr.getch()
                    if end_ch == ord('q'):
                        return
                    elif end_ch == ord('r'):
                        # Restart the game loop by breaking out to the outer loop
                        break
                    time.sleep(0.05)
                # Break from inner game loop to restart
                break

            stdscr.refresh()

            frame_time = time.time() - last_time
            delay = TICK_RATE - frame_time
            if delay < 0:
                delay = 0.01
            time.sleep(delay)
            last_time = time.time()


if __name__ == "__main__":
    wrapper(main)
