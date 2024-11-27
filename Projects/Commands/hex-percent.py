from xulbux.xx_format_codes import FormatCodes
from xulbux.xx_console import Console
import sys


ARGS = sys.argv[1:]


def hex_to_percent(hex_val: str) -> float:
    return round((int(hex_val, 16) / 255) * 100, 2)


if __name__ == "__main__":
    try:
        hex_val = (
            ARGS[0]
            if len(ARGS) > 0
            else FormatCodes.input("Enter HEX value [dim]([2 digits] (e.g. 'FF')) > ")
            .strip()
            .upper()
        )
        percent = hex_to_percent(hex_val)
        FormatCodes.print(f"\n  [#EEF|dim](=)  [white][b]({percent})%[_]\n")
    except KeyboardInterrupt:
        Console.exit()
    except Exception as e:
        print("ERROR:", e)
