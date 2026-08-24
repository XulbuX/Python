#!/usr/bin/env python3
# x-cmds:file[update]

"""Quickly convert a HEX value to a percentage."""

from xulbux import ArgumentParser, S, StyledText, console


def hex_to_percent(hex_val: str | None) -> float:
    """Convert a hex value to a percentage."""

    if not hex_val:
        return 0.0
    elif hex_val.startswith("#"):
        hex_val = hex_val[1:]
    elif hex_val.lower().startswith("0x"):
        hex_val = hex_val[2:]

    return round((int(hex_val, 16) / ((16 ** len(hex_val)) - 1)) * 100, 2)


def main() -> None:
    pct = hex_to_percent(ARGS.hex.val())
    StyledText("", ((S.DIM | S.BR.WHITE)("  =  "), (S.WHITE | S.BOLD)(f"{pct}%")), "", sep="\n").print()


if __name__ == "__main__":
    args = ArgumentParser(
        title="Hex → Percent",
        subtitle="Quickly convert a hex value to a percentage",
        examples=[
            ("{cmd} FFFFFF", "Six digits, 100%"),
            ("{cmd} 80", "Two digits, ~50%"),
            ("{cmd} 0", "Single digit, 0%"),
        ],
    )

    args.add_arg("hex", help="Hex value to convert")

    global ARGS
    ARGS = args.parse()

    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        console.fail(exc, start="\n", end="\n\n")
