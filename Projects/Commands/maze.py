#!/usr/bin/env python3
"""Play a maze game in the console.
Controls and options are shown on startup."""
from xulbux import FormatCodes, Console, FileSys
from collections import deque
from pathlib import Path
from typing import Optional, cast
from heapq import heappush, heappop
import keyboard
import random
import array
import math
import time
import sys
import os


class MazeTooLargeError(Exception):
    ...


class Maze:

    def __init__(
        self,
        width: int,
        height: int,
        bg: str = "0",
        wall: str = "1",
        start: str = "2",
        goal: str = "3",
        player: str = "4",
        solution: str = "5",
        render_opts: Optional[dict[str, str | int | tuple[str, str]]] = None,
        render_ascii: bool = False,
    ):
        # PRE-COMPUTE TILES
        self.bg_byte: int = ord(bg)
        self.wall_byte: int = ord(wall)
        self.start_byte: int = ord(start)
        self.goal_byte: int = ord(goal)
        self.player_byte: int = ord(player)
        self.solution_byte: int = ord(solution)
        # RENDER
        self.render_opts: dict[str, str | int | tuple[str, str]] = ({
            "bg": " ",
            "wall": "█",
            "start": " ",
            "goal": "▞",
            "player": "▒",
            "solution": "░",
            "stretch_w": 2,
        } if render_ascii else {
            "bg": " ",
            "wall": "█",
            "start": ("█", "[br:green]"),
            "goal": ("█", "[br:red]"),
            "player": ("█", "[br:yellow]"),
            "solution": ("█", "[dim]"),
            "stretch_w": 2,
        })
        if render_opts is not None:
            self.render_opts.update(render_opts)
        self.show_solution: bool = False
        self.render_ascii: bool = render_ascii
        self.render_opts["stretch_w"] = max(1, self.render_opts["stretch_w"])
        self.rendered_tiles: dict[int, str] = {
            self.bg_byte: self._render_char(cast(str | tuple[str, str], self.render_opts["bg"])),
            self.wall_byte: self._render_char(cast(str | tuple[str, str], self.render_opts["wall"])),
            self.start_byte: self._render_char(cast(str | tuple[str, str], self.render_opts["start"])),
            self.goal_byte: self._render_char(cast(str | tuple[str, str], self.render_opts["goal"])),
            self.player_byte: self._render_char(cast(str | tuple[str, str], self.render_opts["player"])),
            self.solution_byte: self._render_char(cast(str | tuple[str, str], self.render_opts["solution"])),
        }
        # GENERATE MAZE
        self.width: int = width - 2
        self.height: int = height - 2
        self.maze = self._generate()
        # POSITIONS
        self.start_pos: list[int] = self._get_pos(self.start_byte)
        self.goal_pos: list[int] = self._get_pos(self.goal_byte)
        self.player_pos: list[int] = list(self.start_pos)
        # PLAYER
        self.under_player: int = self.maze[self.player_pos[0]][self.player_pos[1]]
        self._move_player(0, 0)

    def play(self) -> None:
        self.goal_reached: bool = False
        self._game_main_loop()

    def _find_start_pos(
        self,
        maze: list[bytearray],
        center_y: int,
        center_x: int,
    ) -> tuple[int, int]:
        visited = set()
        queue = deque([(center_y, center_x, 0)])
        furthest_point = (center_y, center_x)
        max_dist = 0
        height, width = len(maze), len(maze[0])
        while queue:
            y, x, dist = queue.popleft()
            if dist > max_dist and maze[y][x] == self.bg_byte:
                max_dist = dist
                furthest_point = (y, x)
            for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_y, new_x = y + dy, x + dx
                pos = (new_y, new_x)
                if (pos not in visited and 0 <= new_y < height and 0 <= new_x < width and maze[new_y][new_x] == self.bg_byte):
                    visited.add(pos)
                    queue.append((new_y, new_x, dist + 1))
        return furthest_point

    def _trim_borders(self, maze: list[bytearray]) -> list[bytearray]:
        while True:
            if not any(change for change in (
                    all(row[0] == self.wall_byte for row in maze),
                    all(row[-1] == self.wall_byte for row in maze),
                    all(cell == self.wall_byte for cell in maze[0]),
                    all(cell == self.wall_byte for cell in maze[-1]),
            )):
                break
            if all(row[0] == self.wall_byte for row in maze):
                maze = [row[1:] for row in maze]
            if all(row[-1] == self.wall_byte for row in maze):
                maze = [row[:-1] for row in maze]
            if all(cell == self.wall_byte for cell in maze[0]):
                maze = maze[1:]
            if all(cell == self.wall_byte for cell in maze[-1]):
                maze = maze[:-1]
        return maze

    def _add_borders(self, maze: list[bytearray]) -> list[bytearray]:
        border = bytearray([self.wall_byte] * (len(maze[0]) + 2))
        return ([border] + [bytearray([self.wall_byte]) + row + bytearray([self.wall_byte]) for row in maze] + [border])

    def _generate(self) -> list[bytearray]:
        width = self.width if self.width % 2 == 1 else self.width - 1
        height = self.height if self.height % 2 == 1 else self.height - 1
        center_y, center_x = height // 2, width // 2
        maze = array.array("B", [self.wall_byte] * (width * height))

        def idx(x: int, y: int) -> int:
            return y * width + x

        stack = [(center_x, center_y)]
        maze[idx(center_x, center_y)] = self.bg_byte
        while stack:
            x, y = stack[-1]
            directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
            random.shuffle(directions)
            found_path = False
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < width and 0 <= new_y < height and maze[idx(new_x, new_y)] == self.wall_byte):
                    maze[idx(x + dx // 2, y + dy // 2)] = self.bg_byte
                    maze[idx(new_x, new_y)] = self.bg_byte
                    stack.append((new_x, new_y))
                    found_path = True
                    break
            if not found_path:
                stack.pop()
        maze_2d = []
        for y in range(height):
            start_idx = y * width
            row = bytearray(maze[start_idx:start_idx + width])
            maze_2d.append(row)
        start_pos = self._find_start_pos(maze_2d, center_y, center_x)
        maze_2d[center_y][center_x] = self.goal_byte
        maze_2d[start_pos[0]][start_pos[1]] = self.start_byte
        final_maze = self._trim_borders(maze_2d)
        return self._add_borders(final_maze)

    def _render_char(self, value: str | tuple[str, str]) -> str:
        if isinstance(value, str):
            return value * cast(int, self.render_opts["stretch_w"])
        else:
            return f"{value[1]}({value[0] * cast(int, self.render_opts["stretch_w"])})"

    def _get_pos(self, tile: int) -> list[int]:
        for y in range(self.height):
            try:
                x = self.maze[y].index(tile)
                return [y, x]
            except ValueError:
                continue
        return [0, 0]

    def _move_player(self, dy: int, dx: int) -> None:
        new_y = self.player_pos[0] + dy
        new_x = self.player_pos[1] + dx
        if self.maze[new_y][new_x] == self.wall_byte:
            return
        self.maze[self.player_pos[0]][self.player_pos[1]] = self.under_player
        self.player_pos[0], self.player_pos[1] = new_y, new_x
        self.under_player = self.maze[new_y][new_x]
        self.maze[new_y][new_x] = self.player_byte

    def _find_path(
        self,
        start: int = ord("2"),
        goal: int = ord("3"),
    ) -> set[tuple[int, int]]:
        start_pos = goal_pos = None
        positions = [(y, x) for y, row in enumerate(self.maze) for x, cell in enumerate(row) if cell in (start, goal)]
        start_pos = next(pos for pos in positions if self.maze[pos[0]][pos[1]] == start)
        goal_pos = next(pos for pos in positions if self.maze[pos[0]][pos[1]] == goal)
        height, width = len(self.maze), len(self.maze[0])
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        def manhattan_distance(pos1: tuple[int, int]) -> int:
            return abs(pos1[0] - goal_pos[0]) + abs(pos1[1] - goal_pos[1])

        open_set = []
        heappush(open_set, (0, start_pos))
        came_from = {}
        g_score = {start_pos: 0}
        f_score = {start_pos: manhattan_distance(start_pos)}
        while open_set:
            current = heappop(open_set)[1]
            if current == goal_pos:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_pos)
                return set(path)
            current_g = g_score[current]
            y, x = current
            for dy, dx in directions:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < height and 0 <= nx < width and self.maze[ny][nx] != self.wall_byte):
                    continue
                neighbor = (ny, nx)
                tentative_g_score = current_g + 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_value = tentative_g_score + manhattan_distance(neighbor)
                    f_score[neighbor] = f_value
                    heappush(open_set, (f_value, neighbor))
        return set()

    def _play_finish_animation(
        self,
        duration: float = 4.0,
        noise: float = 30.0,
        fps: int = 24,
    ) -> None:
        """Play a circular dissolve animation from the goal position.\n
        ----------------------------------------------------------------
        duration: Animation duration in seconds
        noise: Noise percentage (0-100) affecting the circle shape
        fps: Frames per second for the animation"""
        start_time, noise_range, noise_map = time.time(), noise / 100.0, {}
        min_noise, max_noise = 1 - noise_range, 1 + noise_range
        width, height = len(self.maze[0]), len(self.maze)
        max_distance = math.sqrt(height**2 + width**2)
        for y in range(height):
            for x in range(width):
                noise_map[(y, x)] = random.uniform(min_noise, max_noise)
        frame_delay = 1.0 / fps
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            progress = elapsed / duration
            current_radius = progress * max_distance * 1.2
            for y in range(height):
                for x in range(width):
                    dist = math.sqrt((y - self.goal_pos[0])**2 + (x - self.goal_pos[1])**2)
                    if dist * noise_map.get((y, x), 1.0) < current_radius:
                        self.maze[y][x] = self.bg_byte
            self.render(True)
            time.sleep(frame_delay)
        for y in range(height):
            for x in range(width):
                self.maze[y][x] = self.bg_byte
        self.render(True)

    def render(self, output_to_console: bool = False, show_solution: bool = False) -> Optional[str]:
        if self.show_solution or show_solution:
            solution_path = self._find_path(self.player_byte, self.goal_byte)
        else:
            solution_path = set()
        maze_lines = ()
        for y, row in enumerate(self.maze):
            line = ""
            for x, c in enumerate(row):
                if (self.show_solution or show_solution) and ((y, x) in solution_path and c == self.bg_byte):
                    line += self.rendered_tiles.get(self.solution_byte, "")
                else:
                    line += self.rendered_tiles.get(c, self.rendered_tiles.get(self.bg_byte, ""))
            maze_lines += (line, )
        if output_to_console:
            if self.render_ascii:
                sys.stdout.write("\033c" + "\n".join(maze_lines))
                sys.stdout.flush()
            else:
                FormatCodes.print("\033c" + "\n".join(maze_lines), end="")
        else:
            return "\n".join(maze_lines)

    def _game_main_loop(self) -> None:
        directions = {
            72: (-1, 0),  # UP
            80: (1, 0),  # DOWN
            75: (0, -1),  # LEFT
            77: (0, 1),  # RIGHT
            "w": (-1, 0),
            "s": (1, 0),
            "a": (0, -1),
            "d": (0, 1),
        }
        wait = 0
        while not self.goal_reached:
            self.render(True)
            if wait > 0:
                time.sleep(wait)
            while not self.goal_reached:
                event = keyboard.read_event()
                key = event.scan_code if event.scan_code in directions else event.name
                if key in directions:
                    self._move_player(*directions[key])
                    if self.player_pos == self.goal_pos:
                        self.goal_reached, self.show_solution = True, False
                        self._play_finish_animation()
                    wait = 0.05
                    break
                elif key in ("esc", "q"):
                    print("\x1bc\x1b[0m", end="", flush=True)
                    raise KeyboardInterrupt
                elif key == "h":
                    self.show_solution = not self.show_solution
                    wait = 0.2
                    break
                elif key == "f":
                    self.goal_reached, self.show_solution = True, False
                    self._play_finish_animation()
                    break


def main():

    def smart_split(s: str, char: str = " ") -> list[str]:
        return (s.lower().strip().split(char) if char in s.lower().strip() else s.lower().strip().split())

    Console.log_box_filled(
        " [b](WASD ⏶⏴⏷⏵)  : move the player",
        "     [b](H)      : toggle solution",
        "     [b](F)      : finish maze",
        "   [b](ESC Q)    : exit game",
        "   [b](ENTER)    : start game normal",
        "[b](SHIFT+ENTER) : start game ASCII",
        "   [b](SPACE)    : generate to file",
        start="\n",
        end="\n\n",
    )

    while True:
        event = keyboard.read_event()
        if event.event_type == "down":
            if event.name == "enter":
                ascii_mode = keyboard.is_pressed("shift")
                while True:
                    Maze(
                        Console.w // 2,
                        Console.h,
                        render_ascii=ascii_mode,
                    ).play()
            elif event.name == "space":
                w, h = (
                    int(val.strip()) for val in smart_split(
                        FormatCodes.input("[br:green]What dimensions should the maze be? [dim](([i](25x25)))[_]\n ⤷ ").strip()
                        or "25x25",
                        "x",
                    )
                )
                dir_path = Path(FormatCodes.input(
                    "[br:green]In which directory should the maze files be saved? [dim](([i](base directory)))[_]\n ⤷ "
                )) or FileSys.script_dir
                files = (
                    os.path.normpath(f"{dir_path}/maze_{w}x{h}.txt"),
                    os.path.normpath(f"{dir_path}/maze_{w}x{h}_solution.txt"),
                )
                FormatCodes.print("\n[dim](generating maze...       )", end="")
                maze = Maze(w, h, render_ascii=True)
                info = (
                    f"═════ MAZE [{w}×{h}] TILES ═════\n" + f"│ START = {maze.rendered_tiles[maze.player_byte]}\n"
                    + f"│ GOAL  = {maze.rendered_tiles[maze.goal_byte]}\n\n"
                )
                FormatCodes.print("\r[dim](rendering maze...        )", end="")
                maze.show_solution = False
                content = info + (maze.render() or "")
                FormatCodes.print("\r[dim](writing maze file...     )", end="")
                with open(files[0], "w", encoding="utf-8") as f:
                    f.write(content)
                FormatCodes.print("\r[dim](rendering solution...    )", end="")
                maze.show_solution = True
                content = info + (maze.render() or "")
                FormatCodes.print("\r[dim](writing solution file... )", end="")
                with open(files[1], "w", encoding="utf-8") as f:
                    f.write(content)
                FormatCodes.print("\r[dim](finalizing...            )", end="")
                sizes = [
                    f"(" + next(
                        f"{os.path.getsize(f)/1024**i:.1f} {u}"
                        for i, u in enumerate(["B", "KB", "MB", "GB", "TB"]) if os.path.getsize(f) < 1024**(i + 1)
                    ) + ")" for f in files
                ]
                Console.log_box_filled(
                    f"Saved maze to [b]{files[0]}[_b] [[i]{sizes[0]}[_i]]",
                    f"Saved solution to [b]{files[1]}[_b] [[i]{sizes[1]}[_i]]",
                    start="\r",
                )
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\x1b[0m", end="", flush=True)
