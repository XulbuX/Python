#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Show the foreground and background colors
from the current terminal color scheme."""
from xulbux.format_codes import FmtSegment, FC, F
from xulbux import Console

ARGS = Console.get_args({"help": {"-h", "--help"}})


# fmt: off
def print_help():
    title = ["  Terminal Colors", " — Show all foreground and background terminal colors  "]
    FC(
        "",
        ("▄" * len("".join(title))),
        (F.INVERSE | F.BG.BLACK)(F.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        ((F.BOLD)("Usage: "), (F.BR.GREEN)("terminal-colors")),
        "",
    ).print()


SHELL_COLORS: list[list[FmtSegment]] = [
    [F.BLACK,   F.BR.BLACK,   F.WHITE | F.BG.BLACK,   F.WHITE | F.BG.BR.BLACK  ],
    [F.WHITE,   F.BR.WHITE,   F.BLACK | F.BG.WHITE,   F.BLACK | F.BG.BR.WHITE  ],
    [F.RED,     F.BR.RED,     F.BLACK | F.BG.RED,     F.BLACK | F.BG.BR.RED    ],
    [F.YELLOW,  F.BR.YELLOW,  F.BLACK | F.BG.YELLOW,  F.BLACK | F.BG.BR.YELLOW ],
    [F.GREEN,   F.BR.GREEN,   F.BLACK | F.BG.GREEN,   F.BLACK | F.BG.BR.GREEN  ],
    [F.CYAN,    F.BR.CYAN,    F.BLACK | F.BG.CYAN,    F.BLACK | F.BG.BR.CYAN   ],
    [F.BLUE,    F.BR.BLUE,    F.BLACK | F.BG.BLUE,    F.BLACK | F.BG.BR.BLUE   ],
    [F.MAGENTA, F.BR.MAGENTA, F.BLACK | F.BG.MAGENTA, F.BLACK | F.BG.BR.MAGENTA],
]
# fmt: on


def show_shell_colors():
    norm_fg, bright_fg, norm_bg, bright_bg = zip(*SHELL_COLORS)
    output = FC("\n")

    for fgs, bgs in [(norm_fg, norm_bg), (bright_fg, bright_bg)]:
        for fmt in fgs:
            output += FC((fmt("Aa"), " "))
        output += " "
        for fmt in bgs:
            output += FC(fmt(" Aa "))
        output += "\n"

    output.print()


if __name__ == "__main__":
    if ARGS.help.exists:
        print_help()
    else:
        show_shell_colors()
