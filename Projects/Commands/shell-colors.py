from xulbux import FormatCodes, Console


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

ARGS = Console.get_args({"sample_text": {"-t", "--text"}})


def show_shell_colors():
    sample_text = ARGS.sample_text.values[0] if ARGS.sample_text.values else "Some sample text."

    for format_codes in SHELL_COLORS.values():
        print()

        for i, format_code in enumerate(format_codes):
            display_text = f"[{format_code}]({sample_text})"
            FormatCodes.print(f"{display_text:<{len(display_text) + 2}}", end="" if not i % 2 else "\n")

    print()


if __name__ == "__main__":
    show_shell_colors()
