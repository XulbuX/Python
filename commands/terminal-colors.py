#!/usr/bin/env python3
# x-cmds:file[update]

"""Show the foreground and background colors
from the current terminal color scheme."""

from xulbux.ansi import AnyStyle, S, StyledText
from xulbux.console import get_args

ARGS = get_args({
    "help": {"-h", "--help"},
})

SHELL_COLORS: list[list[AnyStyle]] = [
    [S.BLACK, S.BR.BLACK, S.WHITE | S.BG.BLACK, S.WHITE | S.BG.BR.BLACK],
    [S.WHITE, S.BR.WHITE, S.BLACK | S.BG.WHITE, S.BLACK | S.BG.BR.WHITE],
    [S.RED, S.BR.RED, S.BLACK | S.BG.RED, S.BLACK | S.BG.BR.RED],
    [S.YELLOW, S.BR.YELLOW, S.BLACK | S.BG.YELLOW, S.BLACK | S.BG.BR.YELLOW],
    [S.GREEN, S.BR.GREEN, S.BLACK | S.BG.GREEN, S.BLACK | S.BG.BR.GREEN],
    [S.CYAN, S.BR.CYAN, S.BLACK | S.BG.CYAN, S.BLACK | S.BG.BR.CYAN],
    [S.BLUE, S.BR.BLUE, S.BLACK | S.BG.BLUE, S.BLACK | S.BG.BR.BLUE],
    [S.MAGENTA, S.BR.MAGENTA, S.BLACK | S.BG.MAGENTA, S.BLACK | S.BG.BR.MAGENTA],
]


def print_help() -> None:
    title = ["  Terminal Colors", " — Show all foreground and background terminal colors  "]
    StyledText(
        "",
        ("▄" * len("".join(title))),
        (S.INVERSE | S.BG.BLACK)(S.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        ((S.BOLD)("Usage: "), (S.BR.GREEN)("terminal-colors")),
        "",
        sep="\n",
    ).print()


def show_shell_colors() -> None:
    norm_fg, bright_fg, norm_bg, bright_bg = zip(*SHELL_COLORS, strict=False)
    output = StyledText("\n")

    for fgs, bgs in [(norm_fg, norm_bg), (bright_fg, bright_bg)]:
        output += "  "
        for fmt in fgs:
            output += StyledText(fmt("Aa"), " ")
        output += "  "
        for fmt in bgs:
            output += StyledText(fmt(" Aa "))
        output += "\n"

    output.print()


if __name__ == "__main__":
    if ARGS.help.exists:
        print_help()
    else:
        show_shell_colors()
