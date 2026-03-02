import random
import tkinter as tk
from dataclasses import dataclass

CELL_SIZE = 26
STATUS_BAR_HEIGHT = 42
TICK_RATE_MS = 120
POWER_TICKS = 55
GHOST_EAT_SCORE = 200

MAP_LAYOUT = [
    "###########################",
    "#o..........#..........o..#",
    "#.#####.###.#.###.#####.#.#",
    "#.#   #.#.......#.#   #.#.#",
    "#.# # #.#.#####.#.# # #.#.#",
    "#...#...#...P...#...#...#.#",
    "###.#.#####.#.#####.#.###.#",
    "#...#.....#...#.....#...#.#",
    "#.#####.#.#####.#.#####.#.#",
    "#.......#...#...#.......#.#",
    "#.###.#####.#.#####.###.#.#",
    "#o..#.......A.......#..o#.#",
    "###.#.###.#.#.#.###.#.###.#",
    "#.....#...B.C.D...#.....#.#",
    "###########################",
]

WALL = "#"
PELLET = "."
POWER = "o"
EMPTY = " "
PLAYER = "P"

DIRS = {
    "Left": (-1, 0),
    "Right": (1, 0),
    "Up": (0, -1),
    "Down": (0, 1),
}


@dataclass
class Entity:
    x: int
    y: int
    direction: tuple[int, int] = (0, 0)


@dataclass
class Ghost(Entity):
    name: str = ""
    color: str = "#ef4444"
    personality: str = "chaser"


class PacManLikeGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pac-Man Like Deluxe (Tkinter)")

        self.grid = [list(row) for row in MAP_LAYOUT]
        self.height = len(self.grid)
        self.width = len(self.grid[0])

        self.score = 0
        self.lives = 3
        self.power_ticks = 0
        self.game_over = False
        self.game_win = False

        self.player_spawn = self._find_symbol(PLAYER)
        self.player = Entity(*self.player_spawn)
        self.pending_direction = (0, 0)

        self.ghost_specs = {
            "A": ("Blinky", "#ef4444", "chaser"),
            "B": ("Pinky", "#f472b6", "ambusher"),
            "C": ("Inky", "#38bdf8", "random"),
            "D": ("Clyde", "#f59e0b", "scatter"),
        }
        self.ghost_spawns: dict[str, tuple[int, int]] = {}
        self.ghosts = self._spawn_ghosts()

        self.canvas = tk.Canvas(
            root,
            width=self.width * CELL_SIZE,
            height=self.height * CELL_SIZE + STATUS_BAR_HEIGHT,
            bg="#020617",
            highlightthickness=0,
        )
        self.canvas.pack(padx=12, pady=12)

        self.root.bind("<KeyPress>", self.on_key)
        self.draw()
        self.loop()

    def _find_symbol(self, symbol: str) -> tuple[int, int]:
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == symbol:
                    self.grid[y][x] = EMPTY
                    return x, y
        raise ValueError(f"Missing '{symbol}' in MAP_LAYOUT")

    def _spawn_ghosts(self) -> list[Ghost]:
        ghosts = []
        for marker, spec in self.ghost_specs.items():
            x, y = self._find_symbol(marker)
            self.ghost_spawns[marker] = (x, y)
            name, color, personality = spec
            ghosts.append(Ghost(x=x, y=y, name=name, color=color, personality=personality))
        return ghosts

    def on_key(self, event: tk.Event):
        if self.game_over:
            if event.keysym.lower() == "r":
                self.reset_game()
            return
        if event.keysym in DIRS:
            self.pending_direction = DIRS[event.keysym]

    def reset_game(self):
        self.grid = [list(row) for row in MAP_LAYOUT]
        self.score = 0
        self.lives = 3
        self.power_ticks = 0
        self.game_over = False
        self.game_win = False
        self.player_spawn = self._find_symbol(PLAYER)
        self.player = Entity(*self.player_spawn)
        self.pending_direction = (0, 0)
        self.ghost_spawns.clear()
        self.ghosts = self._spawn_ghosts()

    def loop(self):
        if not self.game_over:
            self.update_player()
            self.update_ghosts()
            self.check_collisions()
            self.check_win()
        self.draw()
        self.root.after(TICK_RATE_MS, self.loop)

    def can_move(self, x: int, y: int) -> bool:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        return self.grid[y][x] != WALL

    def update_player(self):
        px, py = self.player.x, self.player.y
        ndx, ndy = self.pending_direction
        if self.can_move(px + ndx, py + ndy):
            self.player.direction = self.pending_direction

        dx, dy = self.player.direction
        nx, ny = px + dx, py + dy
        if self.can_move(nx, ny):
            self.player.x, self.player.y = nx, ny

        cell = self.grid[self.player.y][self.player.x]
        if cell == PELLET:
            self.score += 10
            self.grid[self.player.y][self.player.x] = EMPTY
        elif cell == POWER:
            self.score += 50
            self.power_ticks = POWER_TICKS
            self.grid[self.player.y][self.player.x] = EMPTY

        if self.power_ticks > 0:
            self.power_ticks -= 1

    def _valid_moves(self, entity: Entity) -> list[tuple[int, int]]:
        moves = []
        for dx, dy in DIRS.values():
            nx, ny = entity.x + dx, entity.y + dy
            if self.can_move(nx, ny):
                # avoid immediate reversal unless needed
                if (dx, dy) == (-entity.direction[0], -entity.direction[1]) and len(moves) > 0:
                    continue
                moves.append((dx, dy))
        return moves

    def _target_move(self, ghost: Ghost, moves: list[tuple[int, int]]) -> tuple[int, int]:
        gx, gy = ghost.x, ghost.y
        px, py = self.player.x, self.player.y

        if self.power_ticks > 0:
            return max(moves, key=lambda d: abs((gx + d[0]) - px) + abs((gy + d[1]) - py))

        if ghost.personality == "chaser":
            return min(moves, key=lambda d: abs((gx + d[0]) - px) + abs((gy + d[1]) - py))

        if ghost.personality == "ambusher":
            look_x = px + self.player.direction[0] * 2
            look_y = py + self.player.direction[1] * 2
            return min(moves, key=lambda d: abs((gx + d[0]) - look_x) + abs((gy + d[1]) - look_y))

        if ghost.personality == "scatter":
            corner_target = (self.width - 2, self.height - 2)
            if random.random() < 0.25:
                return random.choice(moves)
            return min(
                moves,
                key=lambda d: abs((gx + d[0]) - corner_target[0]) + abs((gy + d[1]) - corner_target[1]),
            )

        # random personality
        if random.random() < 0.55:
            return random.choice(moves)
        return min(moves, key=lambda d: abs((gx + d[0]) - px) + abs((gy + d[1]) - py))

    def update_ghosts(self):
        for ghost in self.ghosts:
            moves = self._valid_moves(ghost)
            if not moves:
                ghost.direction = (-ghost.direction[0], -ghost.direction[1])
                continue
            ghost.direction = self._target_move(ghost, moves)
            ghost.x += ghost.direction[0]
            ghost.y += ghost.direction[1]

    def check_collisions(self):
        for i, ghost in enumerate(self.ghosts):
            if (ghost.x, ghost.y) != (self.player.x, self.player.y):
                continue
            if self.power_ticks > 0:
                self.score += GHOST_EAT_SCORE
                marker = list(self.ghost_specs.keys())[i]
                sx, sy = self.ghost_spawns[marker]
                self.ghosts[i].x, self.ghosts[i].y = sx, sy
                self.ghosts[i].direction = (0, 0)
            else:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                    self.game_win = False
                    return
                self.player = Entity(*self.player_spawn)
                self.pending_direction = (0, 0)
                for gi, mk in enumerate(self.ghost_specs.keys()):
                    sx, sy = self.ghost_spawns[mk]
                    self.ghosts[gi].x, self.ghosts[gi].y = sx, sy
                    self.ghosts[gi].direction = (0, 0)
                return

    def check_win(self):
        for row in self.grid:
            if PELLET in row or POWER in row:
                return
        self.game_over = True
        self.game_win = True

    def draw_tile(self, x: int, y: int, cell: str):
        x0, y0 = x * CELL_SIZE, y * CELL_SIZE
        x1, y1 = x0 + CELL_SIZE, y0 + CELL_SIZE

        if cell == WALL:
            self.canvas.create_rectangle(x0, y0, x1, y1, fill="#0f172a", outline="#1e3a8a", width=1)
            self.canvas.create_rectangle(x0 + 3, y0 + 3, x1 - 3, y1 - 3, outline="#38bdf8", width=1)
        elif cell == PELLET:
            self.canvas.create_oval(x0 + 10, y0 + 10, x0 + 16, y0 + 16, fill="#f8fafc", outline="")
        elif cell == POWER:
            self.canvas.create_oval(x0 + 7, y0 + 7, x0 + 19, y0 + 19, fill="#fde68a", outline="")

    def draw_player(self):
        px0 = self.player.x * CELL_SIZE + 2
        py0 = self.player.y * CELL_SIZE + 2
        px1 = px0 + CELL_SIZE - 4
        py1 = py0 + CELL_SIZE - 4
        self.canvas.create_oval(px0, py0, px1, py1, fill="#facc15", outline="#f59e0b", width=2)

        # eye for better look
        self.canvas.create_oval(px0 + 12, py0 + 6, px0 + 16, py0 + 10, fill="#111827", outline="")

    def draw_ghost(self, ghost: Ghost):
        gx0 = ghost.x * CELL_SIZE + 4
        gy0 = ghost.y * CELL_SIZE + 4
        gx1 = gx0 + CELL_SIZE - 8
        gy1 = gy0 + CELL_SIZE - 8

        color = "#93c5fd" if self.power_ticks > 0 else ghost.color
        self.canvas.create_arc(gx0, gy0, gx1, gy1 + 10, start=0, extent=180, fill=color, outline=color)
        self.canvas.create_rectangle(gx0, gy0 + (CELL_SIZE // 2) - 2, gx1, gy1 + 2, fill=color, outline=color)

        eye_color = "#0f172a" if self.power_ticks > 0 else "white"
        self.canvas.create_oval(gx0 + 4, gy0 + 8, gx0 + 8, gy0 + 12, fill=eye_color, outline="")
        self.canvas.create_oval(gx0 + 12, gy0 + 8, gx0 + 16, gy0 + 12, fill=eye_color, outline="")

    def draw(self):
        self.canvas.delete("all")

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                self.draw_tile(x, y, cell)

        self.draw_player()
        for ghost in self.ghosts:
            self.draw_ghost(ghost)

        self.canvas.create_rectangle(
            0,
            self.height * CELL_SIZE,
            self.width * CELL_SIZE,
            self.height * CELL_SIZE + STATUS_BAR_HEIGHT,
            fill="#111827",
            outline="#334155",
        )

        status = f"Score: {self.score}   Lives: {self.lives}"
        if self.power_ticks > 0:
            status += "   POWER MODE"
        if self.game_over:
            status += "   YOU WIN!" if self.game_win else "   GAME OVER"
            status += " (Press R to restart)"

        self.canvas.create_text(
            12,
            self.height * CELL_SIZE + 22,
            anchor="w",
            fill="#e2e8f0",
            font=("TkDefaultFont", 12, "bold"),
            text=status,
        )


if __name__ == "__main__":
    root = tk.Tk()
    PacManLikeGame(root)
    root.mainloop()
