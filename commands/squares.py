#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""Get the squares of all numbers up to a given number."""

import keyboard
from xulbux import Console, FormatCodes
from xulbux.base.consts import CHARS

ARGS = Console.get_args({"table_cols": {"-c", "--cols"}, "help": {"-h", "--help"}})
TABLE_COLS = int(v) if (v := ARGS.table_cols.get(0)) and v.replace("_", "").isdigit() else 4


def clear_last_lines(count: int) -> None:
    for _ in range(count):
        print("\033[F\033[K", end="")


def wait_key_pressed_and_released(key: str) -> None:
    while not keyboard.is_pressed(key):
        pass
    while keyboard.is_pressed(key):
        pass


def print_help() -> None:
    help_text = """
[b|in|bg:black]( Squares — Calculate the squares of all numbers up to a given number )

[b](Usage:) [br:green](squares) [br:blue]([options])

[b](Options:)
  [br:blue](-c), [br:blue](--cols[dim](=)N)    Number of table columns [dim]((default: 4))

[b](Examples:)
  [br:green](squares)             [dim](# [i](Calculate squares with 4 columns))
  [br:green](squares) [br:blue](--cols[dim](=)6)    [dim](# [i](Calculate squares with 6 columns))
"""
    FormatCodes.print(help_text)


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    FormatCodes.print(
        "═══════════════════ [b](SQUARED NUMBERS — ALL OF THEM!) ═══════════════════\n"
        ">> hold SPACE to pause, while the program is writing down the numbers\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    loops = int(
        Console.input(
            "Until which number do you want all squares to be calculated: ", allowed_chars=CHARS.DIGITS, min_len=1, max_len=7
        )
        or ""
    )

    i = 1
    row_space = len(f"│ {loops}² = {loops * loops:,} │")

    borders = {
        "top": ("╭" + ((row_space * TABLE_COLS) - 2) * "─" + "╮"),
        "bottom": ("╰" + ((row_space * TABLE_COLS) - 2) * "─" + "╯"),
    }

    print(borders["top"])
    while i <= loops:
        row = ""
        if keyboard.is_pressed("space"):
            wait_key_pressed_and_released("space")
        for _ in range(TABLE_COLS):
            if i <= loops:
                output = f"│ {i}² = {i * i:,}"
                row += f"{output}{(row_space - len(output) - 1) * ' '}│"
            else:
                row += f"│{(row_space - 2) * ' '}│"
            i += 1
        print(row)
    print(borders["bottom"])
    print()

    Console.cls()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\x1b[0m", flush=True)
