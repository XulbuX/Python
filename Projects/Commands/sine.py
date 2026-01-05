#!/usr/bin/env python3
"""Show a sine wave animation inside the console."""
from typing import Generator, Any
from xulbux import Console
import math
import time


ARGS = Console.get_args(
    allow_spaces=True,
    invert={"-i", "--invert", "--inverse"},
)


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


if __name__ == "__main__":
    try:
        print()
        show_wave(
            width=(Console.w // 2) - 1,
            speed=(5, 1),
            chars=["██", "  "] if ARGS.invert.exists else ["  ", "██"],
        )
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
