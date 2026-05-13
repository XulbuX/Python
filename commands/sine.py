#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Show a sine wave animation inside the terminal."""
from typing import Optional
from xulbux import FormatCodes, Console
import math
import time


ARGS = Console.get_args({
    "speed": {"-s", "--speed"},
    "y_stretch": {"-y", "--y-stretch"},
    "help": {"-h", "--help"},
})


def print_help():
    help_text = """\
[b|in|bg:black]( Sine — Show a sine wave animation inside the terminal )

[b](Usage:) [br:green](sine) [br:blue]([options])

[b](Options:)
  [br:blue](-s), [br:blue](--speed)        Animation speed multiplier [dim]((default: 1.0))
  [br:blue](-y), [br:blue](--y-stretch)    Vertical stretch of wave cycles [dim]((default: 1.0))

[b](Examples:)
  [br:green](sine)                  [dim](# [i](Default wave))
  [br:green](sine) [br:blue](--speed[dim](=)2)        [dim](# [i](Scroll twice as fast))
  [br:green](sine) [br:blue](--y-stretch[dim](=)3)    [dim](# [i](Cycles 3× more stretched out))
  [br:green](sine) [br:blue](-s[dim](=)0.5) [br:blue](-y[dim](=)2)      [dim](# [i](Half speed, double stretch))
"""
    FormatCodes.print(help_text)


def show_wave(width: int, speed: tuple[float, float] = (5, 1)) -> None:
    t = 0
    half_w = width // 2
    prev_x: Optional[int] = None

    def wave_x(step: float) -> int:
        return max(0, min(
            width - 1,
            int(half_w * math.sin(math.radians(step * speed[0])) + half_w),
        ))

    while True:
        x1 = wave_x(t)  # UPPER HALF OF THIS TERMINAL ROW
        x2 = wave_x(t + 0.5)  # LOWER HALF OF THIS TERMINAL ROW

        # UPPER HALF: CONNECT FROM PREVIOUS POSITION TO x1
        lo_u = min(prev_x, x1) if prev_x is not None else x1
        hi_u = max(prev_x, x1) if prev_x is not None else x1
        # LOWER HALF: CONNECT FROM x1 TO x2
        lo_l, hi_l = min(x1, x2), max(x1, x2)

        line: list[str] = []
        for col in range(width):
            upper = lo_u <= col <= hi_u
            lower = lo_l <= col <= hi_l
            if upper and lower:
                c = "█"
            elif upper:
                c = "▀"
            elif lower:
                c = "▄"
            else:
                c = " "
            line.append(c)

        print("".join(line))

        prev_x = x2
        t += 1

        time.sleep(1 / (speed[1] * 100))


def main() -> None:
    print()

    if ARGS.help.exists:
        print_help()
        return

    speed = max(0.1, float(ARGS.speed.values[0])) if ARGS.speed.exists else 1.0
    y_stretch = max(0.1, float(ARGS.y_stretch.values[0])) if ARGS.y_stretch.exists else 1.0

    show_wave(width=Console.width - 1, speed=(5 / y_stretch, speed))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
