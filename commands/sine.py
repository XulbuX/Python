#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Show a sine wave animation inside the terminal."""
from typing import Generator, Any
from xulbux import FormatCodes, Console
import math
import time


ARGS = Console.get_args({
    "invert": {"-i", "--invert"},
    "help": {"-h", "--help"},
})


def print_help():
    help_text = """\
[b|in|bg:black]( Sine — Show a sine wave animation inside the terminal )

[b](Usage:) [br:green](sine) [br:blue]([options])

[b](Options:)
  [br:blue](-i), [br:blue](--invert)     Invert the wave [dim]((swap filled and empty space))

[b](Examples:)
  [br:green](sine)             [dim](# [i](Show a normal sine wave))
  [br:green](sine) [br:blue](--invert)    [dim](# [i](Show an inverted sine wave))
"""
    FormatCodes.print(help_text)


def smooth_wave(amplitude: int, speed: tuple[float, int]) -> Generator[Any, None, None]:
    while True:
        for i in range(0, 361):
            angle = math.radians(i * speed[0])
            value = amplitude * (math.sin(angle))
            yield value
            time.sleep(1 / (speed[1] * 100))


def show_wave(width: int, speed: tuple[float, int] = (10, 1), chars: list[str] = ["  ", "██"]) -> None:
    for i in smooth_wave(amplitude=round(width / 2), speed=speed):
        idx = int(i + (width // 2))
        print(idx * chars[0] + chars[1] + (width - idx - 1) * chars[0])


def main() -> None:
    print()

    if ARGS.help.exists:
        print_help()
        return

    show_wave(
        width=(Console.width // 2) - 1,
        speed=(5, 1),
        chars=["██", "  "] if ARGS.invert.exists else ["  ", "██"],
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
