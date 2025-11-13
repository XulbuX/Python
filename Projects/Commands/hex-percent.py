#!/usr/bin/env python3
"""Quickly convert a 2-digit HEX value to a percentage."""
from xulbux import FormatCodes, Console


ARGS = Console.get_args({"hex_value": "before"}, allow_spaces=True)


def hex_to_percent(hex_val: str) -> float:
    return round((int(hex_val, 16) / 255) * 100, 2)


def main():
    hex_val = (
        ARGS.hex_value.values[0] if len(ARGS.hex_value.values) > 0 else Console.input(
            "\n[b](Enter 2 digit HEX value) (e.g. [br:cyan](FF)) [b](>) ",
            min_len=2,
            max_len=2,
            allowed_chars="0123456789abcdefABCDEF",
        ).strip().upper()
    )
    percent = hex_to_percent(hex_val)
    FormatCodes.print(f"\n  [dim|br:white](=)  [white][b]({percent})%[_]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
