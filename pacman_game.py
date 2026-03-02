import random
import tkinter as tk
from dataclasses import dataclass

CELL_SIZE = 24
MAP_LAYOUT = [
    "###################",
    "#........#........#",
    "#.###.##.#.##.###.#",
    "#o# #....P....# #o#",
    "#.###.#.###.#.###.#",
    "#.....#..G..#.....#",
    "#####.###.###.#####",
    "#.................#",
    "###################",
]

WALL = "#"
PELLET = "."
POWER = "o"
EMPTY = " "
PLAYER = "P"
GHOST = "G"

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


class PacManLikeGame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pac-Man Like (Tkinter)")

        self.grid = [list(row) for row in MAP_LAYOUT]
        self.height = len(self.grid)
        self.width = len(self.grid[0])

        self.score = 0
        self.lives = 3
        self.power_ticks = 0
        self.game_over = False

        self.player = self._find_entity(PLAYER)
        self.ghost = self._find_entity(GHOST)
        self.player.direction = (0, 0)
        self.pending_direction = (0, 0)

        self.canvas = tk.Canvas(
            root,
            width=self.width * CELL_SIZE,
            height=self.height * CELL_SIZE + 36,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.root.bind("<KeyPress>", self.on_key)
        self.tick_rate_ms = 130
        self.draw()
        self.loop()

    def _find_entity(self, symbol: str) -> Entity:
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == symbol:
                    self.grid[y][x] = EMPTY
                    return Entity(x, y)
        raise ValueError(f"Missing '{symbol}' in MAP_LAYOUT")

    def on_key(self, event: tk.Event):
        if self.game_over:
            if event.keysym.lower() == "r":
                self.__init__(self.root)
            return

        if event.keysym in DIRS:
            self.pending_direction = DIRS[event.keysym]

    def loop(self):
        if not self.game_over:
            self.update_player()
            self.update_ghost()
            self.check_collisions()
            self.draw()
            self.check_win()
        self.root.after(self.tick_rate_ms, self.loop)

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
            self.power_ticks = 45
            self.grid[self.player.y][self.player.x] = EMPTY

        if self.power_ticks > 0:
            self.power_ticks -= 1

    def update_ghost(self):
        gx, gy = self.ghost.x, self.ghost.y

        possible = []
        for dx, dy in DIRS.values():
            nx, ny = gx + dx, gy + dy
            if self.can_move(nx, ny):
                possible.append((dx, dy))

        if not possible:
            return

        if self.power_ticks > 0:
            # Run away from player while powered up
            possible.sort(
                key=lambda d: abs((gx + d[0]) - self.player.x)
                + abs((gy + d[1]) - self.player.y),
                reverse=True,
            )
            self.ghost.direction = possible[0]
        else:
            # Mostly chase, sometimes wander
            if random.random() < 0.75:
                possible.sort(
                    key=lambda d: abs((gx + d[0]) - self.player.x)
                    + abs((gy + d[1]) - self.player.y)
                )
                self.ghost.direction = possible[0]
            else:
                self.ghost.direction = random.choice(possible)

        dx, dy = self.ghost.direction
        self.ghost.x += dx
        self.ghost.y += dy

    def check_collisions(self):
        if (self.player.x, self.player.y) != (self.ghost.x, self.ghost.y):
            return

        if self.power_ticks > 0:
            self.score += 200
            self.ghost = self._find_respawn()
        else:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            self.player = self._find_spawn(PLAYER)
            self.ghost = self._find_spawn(GHOST)
            self.player.direction = (0, 0)
            self.pending_direction = (0, 0)

    def _find_spawn(self, symbol: str) -> Entity:
        for y, row in enumerate(MAP_LAYOUT):
            for x, cell in enumerate(row):
                if cell == symbol:
                    return Entity(x, y)
        raise RuntimeError("Spawn point not found")

    def _find_respawn(self) -> Entity:
        g = self._find_spawn(GHOST)
        g.direction = (0, 0)
        return g

    def check_win(self):
        for row in self.grid:
            if PELLET in row or POWER in row:
                return
        self.game_over = True

    def draw(self):
        self.canvas.delete("all")

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                x0 = x * CELL_SIZE
                y0 = y * CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE

                if cell == WALL:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill="#1e40ff", outline="#123")
                elif cell == PELLET:
                    self.canvas.create_oval(
                        x0 + 9,
                        y0 + 9,
                        x0 + 15,
                        y0 + 15,
                        fill="#ffe082",
                        outline="",
                    )
                elif cell == POWER:
                    self.canvas.create_oval(
                        x0 + 6,
                        y0 + 6,
                        x0 + 18,
                        y0 + 18,
                        fill="#fff59d",
                        outline="",
                    )

        # Draw player
        px0 = self.player.x * CELL_SIZE + 2
        py0 = self.player.y * CELL_SIZE + 2
        px1 = px0 + CELL_SIZE - 4
        py1 = py0 + CELL_SIZE - 4
        self.canvas.create_oval(px0, py0, px1, py1, fill="#ffeb3b", outline="")

        # Draw ghost
        gx0 = self.ghost.x * CELL_SIZE + 3
        gy0 = self.ghost.y * CELL_SIZE + 3
        gx1 = gx0 + CELL_SIZE - 6
        gy1 = gy0 + CELL_SIZE - 6
        ghost_color = "#7dd3fc" if self.power_ticks > 0 else "#ef4444"
        self.canvas.create_rectangle(gx0, gy0, gx1, gy1, fill=ghost_color, outline="")

        status = f"Score: {self.score}   Lives: {self.lives}"
        if self.power_ticks > 0:
            status += "   POWER!"
        if self.game_over:
            if self.lives <= 0:
                status += "   GAME OVER (press R to restart)"
            else:
                status += "   YOU WIN! (press R to restart)"

        self.canvas.create_text(
            10,
            self.height * CELL_SIZE + 18,
            anchor="w",
            fill="white",
            font=("TkDefaultFont", 11, "bold"),
            text=status,
        )


if __name__ == "__main__":
    root = tk.Tk()
    PacManLikeGame(root)
    root.mainloop()
