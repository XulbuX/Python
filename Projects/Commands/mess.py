#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Displays an animated, random text character mess.
The mess can be made faster and displayed in color."""
from xulbux import FormatCodes, Console
import random
import time


ARGS = Console.get_args(
    fast_mode={"-f", "--fast"},
    color_mode={"-c", "--color"},
)

x = ["0", "1"]
f = ["dim", "bold", "inverse", "underline", "strikethrough", "double-underline"]
if ARGS.color_mode.exists:
    f.extend([
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "BR:black", "BR:red", "BR:green", "BR:yellow",
        "BR:blue", "BR:magenta", "BR:cyan", "BR:white", "BG:black", "BG:red", "BG:green", "BG:yellow", "BG:blue", "BG:magenta",
        "BG:cyan", "BG:white", "BG:BR:black", "BG:BR:red", "BG:BR:green", "BG:BR:yellow", "BG:BR:blue", "BG:BR:magenta",
        "BG:BR:cyan", "BG:BR:white", "randomCL", "randomBG"
    ])


def random_hexa() -> str:
    return f"#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}"


def replace_special(text: str) -> str:
    return text.replace("randomCL", random_hexa()).replace("randomBG", f"BG:{random_hexa()}")


def main() -> None:
    while True:
        line = "".join((f"[{replace_special(random.choice(f))}]" if random.randint(0, 1) == 1 else "")
                       + (random.choice(x) if random.randint(0, 1) == 1 else " ") + "[_]" for _ in range(Console.w))
        FormatCodes.print(line)
        if not ARGS.fast_mode.exists:
            time.sleep(0.025)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
