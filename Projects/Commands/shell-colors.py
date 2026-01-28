from xulbux import FormatCodes


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
    show_shell_colors()
