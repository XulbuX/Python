"""Quickly convert a 2-digit HEX value to a percentage."""
from xulbux import FormatCodes, Console
import sys


ARGS = sys.argv[1:]  # [hex_value]


def hex_to_percent(hex_val: str) -> float:
    return round((int(hex_val, 16) / 255) * 100, 2)


if __name__ == "__main__":
    try:
        hex_val = (
            ARGS[0] if len(ARGS) > 0 else FormatCodes.input("Enter HEX value [dim]([2 digits] (e.g. 'FF')) > ").strip().upper()
        )
        percent = hex_to_percent(hex_val)
        FormatCodes.print(f"\n  [#EEF|dim](=)  [white][b]({percent})%[_]\n")
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
