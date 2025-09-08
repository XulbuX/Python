#!/usr/bin/env python3
"""Conway's game of life in the console."""
from xulbux.base.consts import CHARS
from xulbux import FormatCodes, Console
from typing import Optional
import random
import time
import sys


class GameOfLife:

    def __init__(self):
        self.width = Console.w
        self.height = Console.h * 2
        self.grid = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.next_grid = [[False for _ in range(self.width)] for _ in range(self.height)]
        # PRE-COMPUTE UTF-8 BYTE SEQUENCES FOR MAXIMUM EFFICIENCY
        self.c_full = "█".encode('utf-8')
        self.c_upper = "▀".encode('utf-8')
        self.c_lower = "▄".encode('utf-8')
        self.c_empty = " ".encode('utf-8')

    def initialize_random(self, density: float = 0.3) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = random.random() < density

    def count_neighbors(self, x: int, y: int) -> int:
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx]:
                        count += 1
        return count

    def update(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                neighbors = self.count_neighbors(x, y)
                current_state = self.grid[y][x]
                if current_state:
                    self.next_grid[y][x] = neighbors in [2, 3]
                else:
                    self.next_grid[y][x] = neighbors == 3
        self.grid, self.next_grid = self.next_grid, self.grid

    def render(self) -> None:
        frame = bytearray()
        for i, row in enumerate(range(0, self.height - 1, 2)):
            line = bytearray()
            for col in range(self.width):
                upper_filled = self.grid[row][col]
                lower_filled = self.grid[row + 1][col]
                if upper_filled and lower_filled: char_bytes = self.c_full
                elif upper_filled: char_bytes = self.c_upper
                elif lower_filled: char_bytes = self.c_lower
                else: char_bytes = self.c_empty
                line.extend(char_bytes)
            frame.extend(line)
            if i < (self.height - 1) // 2 - 1:
                frame.extend(b"\n")
        sys.stdout.write(f"\x1bc{frame.decode('utf-8')}")

    def add_glider(self, x: int, y: int) -> None:
        glider = [
            [False, True, False],
            [False, False, True],
            [True, True, True],
        ]
        for dy in range(3):
            for dx in range(3):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    self.grid[ny][nx] = glider[dy][dx]

    def add_oscillator(self, x: int, y: int) -> None:
        if 0 <= x < self.width and 0 <= y - 1 < self.height and 0 <= y + 1 < self.height:
            self.grid[y - 1][x] = True
            self.grid[y][x] = True
            self.grid[y + 1][x] = True

    def run(self, gens: Optional[int] = None, delay: float = 0.05) -> None:
        try:
            gen = 0
            while gens is None or gen < gens:
                new_width = Console.w
                new_height = Console.h * 2

                if new_width != self.width or new_height != self.height:
                    old_grid = self.grid
                    self.width = new_width
                    self.height = new_height
                    self.grid = [[False for _ in range(self.width)] for _ in range(self.height)]
                    self.next_grid = [[False for _ in range(self.width)] for _ in range(self.height)]

                    for y in range(min(len(old_grid), self.height)):
                        for x in range(min(len(old_grid[0]), self.width)):
                            self.grid[y][x] = old_grid[y][x]

                self.render()
                self.update()
                gen += 1
                time.sleep(delay)
        except KeyboardInterrupt:
            sys.stdout.write("\x1bc")


def main():
    game = GameOfLife()

    FormatCodes.print("[b](Choose Initialization)", "[b](1) Random pattern", "[b](2) Some classic patterns", sep="\n")
    choice = Console.input("⮡ ", allowed_chars="12", default_val=1, output_type=int)

    match choice:
        case 2:
            game.add_glider(5, 5)
            game.add_glider(15, 8)
            game.add_oscillator(25, 10)
            game.add_oscillator(30, 15)
            for _ in range(20):
                x = random.randint(0, game.width - 1)
                y = random.randint(0, game.height - 1)
                game.grid[y][x] = True
        case _:
            density = 0.2
            density = Console.input(
                f"\nEnter density [[b](0.0 – 1.0)]/([i]({density})): ",
                allowed_chars=CHARS.FLOAT_DIGITS,
                default_val=density,
                output_type=float,
            )
            game.initialize_random(max(0.0, min(1.0, density)))

    delay = 0.02
    delay = Console.input(
        f"\nDelay between generations [[b](secs)]/([i]({delay})): ",
        allowed_chars=CHARS.FLOAT_DIGITS,
        default_val=delay,
        output_type=float,
    )

    game.run(delay=max(0, delay))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
