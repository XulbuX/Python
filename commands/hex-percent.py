#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""Quickly convert a 2-digit HEX value to a percentage."""

from xulbux import Console, FormatCodes

ARGS = Console.get_args({"hex_value": "before", "help": {"-h", "--help"}})


def print_help() -> None:
    help_text = """
[b|in|bg:black]( Hex → Percent — Quickly convert a 2-digit HEX value to a percentage )

[b](Usage:) [br:green](hex-percent) [br:cyan](<hex>)

[b](Arguments:)
  [br:cyan](hex)               2-digit HEX value to convert

[b](Examples:)
  [br:green](hex-percent) [br:cyan](FF)    [dim](# [i](100% opacity))
  [br:green](hex-percent) [br:cyan](80)    [dim](# [i](~50% opacity))
  [br:green](hex-percent) [br:cyan](00)    [dim](# [i](0% opacity))
"""
    FormatCodes.print(help_text)


def hex_to_percent(hex_val: str) -> float:
    return round((int(hex_val, 16) / 255) * 100, 2)


def main() -> None:
    if ARGS.help.exists or not ARGS.hex_value.values:
        print_help()
        return

    percent = hex_to_percent(ARGS.hex_value.values[0])
    FormatCodes.print(f"\n  [dim|br:white](=)  [white][b]({percent})%[_]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
