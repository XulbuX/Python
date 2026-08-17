#!/usr/bin/env python3
# x-cmds:file[update]

"""Quickly convert a HEX value to a percentage."""

from xulbux import S, StyledText, console

ARGS = console.get_args({
    "hex_value": "before",
    "help": {"-h", "--help"},
})


def print_help() -> None:
    title = ["  Hex → Percent", " — Quickly convert a hex value to a percentage  "]
    StyledText(
        "",
        ("▄" * len("".join(title))),
        (S.INVERSE | S.BG.BLACK)(S.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        (S.BOLD("Usage: "), S.BR.GREEN("hex-percent "), S.BR.CYAN("<hex>")),
        "",
        S.BOLD("Arguments:"),
        ("  ", S.BR.CYAN("hex"), "    Hex value to convert"),
        "",
        S.BOLD("Examples:"),
        ("  ", S.BR.GREEN("hex-percent"), " ", S.BR.CYAN("FF"), "    ", S.DIM("# ", S.ITALIC("Two digits, 100%"))),
        ("  ", S.BR.GREEN("hex-percent"), " ", S.BR.CYAN("80"), "    ", S.DIM("# ", S.ITALIC("Two digits, ~50%"))),
        ("  ", S.BR.GREEN("hex-percent"), " ", S.BR.CYAN("0"), "     ", S.DIM("# ", S.ITALIC("Single digits, 0%"))),
        "",
        sep="\n",
    ).print()


def hex_to_percent(hex_val: str) -> float:
    """Convert a hex value to a percentage."""

    if hex_val.startswith("#"):
        hex_val = hex_val[1:]
    elif hex_val.lower().startswith("0x"):
        hex_val = hex_val[2:]

    if not hex_val:
        return 0.0

    max_val = (16 ** len(hex_val)) - 1
    return round((int(hex_val, 16) / max_val) * 100, 2)


def main() -> None:
    if ARGS.help.exists or not ARGS.hex_value.values:
        print_help()
        return

    pct = hex_to_percent(ARGS.hex_value.values[0])
    StyledText("", ((S.DIM | S.BR.WHITE)("  =  "), (S.WHITE | S.BOLD)(f"{pct}%")), "", sep="\n").print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        console.fail(exc, start="\n", end="\n\n")
