#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Show the foreground and background colors
from the current terminal color scheme."""
from xulbux import FormatCodes, Console


ARGS = Console.get_args({"help": {"-h", "--help"}})


def print_help():
    help_text = """
[b|in|bg:black]( Terminal Colors — Show all foreground and background terminal colors )

[b](Usage:) [br:green](terminal-colors)
"""
    FormatCodes.print(help_text)


SHELL_COLORS = {
    "Black": ["black", "br:black", "br:white|bg:black", "br:white|bg:br:black"],
    "White": ["white", "br:white", "black|bg:white", "black|bg:br:white"],
    "Red": ["red", "br:red", "black|bg:red", "black|bg:br:red"],
    "Yellow": ["yellow", "br:yellow", "black|bg:yellow", "black|bg:br:yellow"],
    "Green": ["green", "br:green", "black|bg:green", "black|bg:br:green"],
    "Cyan": ["cyan", "br:cyan", "black|bg:cyan", "black|bg:br:cyan"],
    "Blue": ["blue", "br:blue", "black|bg:blue", "black|bg:br:blue"],
    "Magenta": ["magenta", "br:magenta", "black|bg:magenta", "black|bg:br:magenta"],
}


def show_shell_colors():
    print()

    for format_codes in SHELL_COLORS.values():
        FormatCodes.print(f"[{format_codes[0]}](Aa) ", end="")
    print("  ", end="")
    for format_codes in SHELL_COLORS.values():
        FormatCodes.print(f"[{format_codes[2]}]( Aa )", end="")
    print()
    for format_codes in SHELL_COLORS.values():
        FormatCodes.print(f"[{format_codes[1]}](Aa) ", end="")
    print("  ", end="")
    for format_codes in SHELL_COLORS.values():
        FormatCodes.print(f"[{format_codes[3]}]( Aa )", end="")

    print("\n")


if __name__ == "__main__":
    if ARGS.help.exists:
        print_help()
    else:
        show_shell_colors()
