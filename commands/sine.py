#!/usr/bin/env python3
# x-cmds:file[update]

"""Show a sine wave animation inside the terminal."""

import math
import time
import xulbux as xx
from xulbux import S, StyledText

ARGS = xx.console.get_args({
    "speed": {"-s", "--speed"},
    "y_stretch": {"-y", "--y-stretch"},
    "help": {"-h", "--help"},
})


# fmt: off
def print_help() -> None:
    title = ["  Sine", " — Show a sine wave animation inside the terminal  "]
    StyledText(
        "",
        ("▄" * len("".join(title))),
        (S.INVERSE | S.BG.BLACK)(S.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        (S.BOLD("Usage: "), S.BR.GREEN("sine "), S.BR.BLUE("[options]")),
        "",
        S.BOLD("Options:"),
        ("  ", S.BR.BLUE("-s"), ", ", S.BR.BLUE("--speed"), "        Animation speed multiplier ", S.DIM("(default: 1.0)")),
        ("  ", S.BR.BLUE("-y"), ", ", S.BR.BLUE("--y-stretch"), "    Vertical stretch of wave cycles ", S.DIM("(default: 1.0)")),  # ruff:ignore[line-too-long]
        "",
        S.BOLD("Controls:"),
        ("  ", S.BR.RED("Ctrl(⌘)", S.DIM("+"), "C"), "          Stop the animation"),
        "",
        S.BOLD("Examples:"),
        ("  ", S.BR.GREEN("sine"), "                  ", S.DIM("# ", S.ITALIC("Default wave"))),
        ("  ", S.BR.GREEN("sine "), S.BR.BLUE("--speed", S.DIM("="), "2"), "        ", S.DIM("# ", S.ITALIC("Scroll twice as fast"))),  # ruff:ignore[line-too-long]
        ("  ", S.BR.GREEN("sine "), S.BR.BLUE("--y-stretch", S.DIM("="), "3"), "    ", S.DIM("# ", S.ITALIC("Cycles 3× more stretched out"))),  # ruff:ignore[line-too-long, ambiguous-unicode-character-string]
        ("  ", S.BR.GREEN("sine "), S.BR.BLUE("-s", S.DIM("="), "0.5"), " ", S.BR.BLUE("-y", S.DIM("="), "0.5"), "    ", S.DIM("# ", S.ITALIC("Half speed, half stretch"))),  # ruff:ignore[line-too-long]
        "",
        sep="\n",
    ).print()
# fmt: on


def show_wave(width: int, speed: tuple[float, float] = (5, 1)) -> None:
    t = 0
    half_w = width // 2
    prev_x: int | None = None

    def wave_x(step: float) -> int:
        return max(0, min(width - 1, int(half_w * math.sin(math.radians(step * speed[0])) + half_w)))

    while True:
        x1 = wave_x(t)  # Upper half of this terminal row.
        x2 = wave_x(t + 0.5)  # Lower half of this terminal row.

        # Upper half: connect from previous position to x1:
        lo_u = min(prev_x, x1) if prev_x is not None else x1
        hi_u = max(prev_x, x1) if prev_x is not None else x1
        # Lower half: connect from x1 to x2:
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
    if ARGS.help.exists:
        print_help()
        return

    speed = max(0.1, float(ARGS.speed.values[0])) if ARGS.speed.exists else 1.0
    y_stretch = max(0.1, float(ARGS.y_stretch.values[0])) if ARGS.y_stretch.exists else 1.0

    show_wave(width=xx.console.get_width() - 1, speed=(2 / y_stretch, speed))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
