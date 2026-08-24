#!/usr/bin/env python3
# x-cmds:file[update]

"""Get the squares of all numbers up to a given number."""

import keyboard
import xulbux as xx
from xulbux import ArgumentParser, FormatCodes, S
from xulbux.base.consts import CHARS


def clear_last_lines(count: int) -> None:
    for _ in range(count):
        print("\033[F\033[K", end="")


def wait_key_pressed_and_released(key: str) -> None:
    while not keyboard.is_pressed(key):
        pass
    while keyboard.is_pressed(key):
        pass


def main() -> None:
    table_cols = ARGS.table_cols.val(int, default=4)

    FormatCodes.print(
        "═══════════════════ [b](SQUARED NUMBERS — ALL OF THEM!) ═══════════════════\n"
        ">> hold SPACE to pause, while the program is writing down the numbers\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    loops = int(
        xx.console.input(
            "Until which number do you want all squares to be calculated: ", allowed_chars=CHARS.DIGITS, min_len=1, max_len=7
        )
        or ""
    )

    i = 1
    row_space = len(f"│ {loops}² = {loops * loops:,} │")

    borders = {
        "top": ("╭" + ((row_space * table_cols) - 2) * "─" + "╮"),
        "bottom": ("╰" + ((row_space * table_cols) - 2) * "─" + "╯"),
    }

    print(borders["top"])
    while i <= loops:
        row = ""
        if keyboard.is_pressed("space"):
            wait_key_pressed_and_released("space")
        for _ in range(table_cols):
            if i <= loops:
                output = f"│ {i}² = {i * i:,}"
                row += f"{output}{(row_space - len(output) - 1) * ' '}│"
            else:
                row += f"│{(row_space - 2) * ' '}│"
                i += 1
        print(row)
    print(borders["bottom"])
    print()

    xx.console.cls()


if __name__ == "__main__":
    args = ArgumentParser(
        title="Squares",
        subtitle="Calculate the squares of all numbers up to a given number",
        examples=[
            ("{cmd}", "Calculate squares with 4 columns"),
            ("{cmd} --cols=6", "Calculate squares with 6 columns"),
        ],
    )

    args.add_opt(
        {"-c", "--cols"},
        "table_cols",
        expects_value="N",
        help=("Number of table columns ", S.DIM("(default: 4)")),
    )

    global ARGS
    ARGS = args.parse()

    try:
        main()
    except KeyboardInterrupt:
        print("\x1b[0m", flush=True)
