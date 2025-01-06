from xulbux import Console, FormatCodes
from pathlib import Path
import sys
import re


def capitalize_hex_colors(content: str) -> tuple[str, bool]:
    pattern = r"(#|0x)([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b"

    def replace_match(match):
        prefix, hex_value = match.groups()
        return prefix + hex_value.upper()

    new_content, count = re.subn(pattern, replace_match, content)
    return new_content, count > 0


def process_file(file_path: Path) -> None:
    try:
        content = file_path.read_text(encoding="utf-8")
        new_content, modified = capitalize_hex_colors(content)
        if modified:
            file_path.write_text(new_content, encoding="utf-8")
            Console.done(f"Updated: [br:cyan]({file_path})", start="", end="\n")
    except Exception as e:
        Console.fail(
            f"Error processing [white]({file_path})\n         \t[br:red]({e})",
            start="\n\n",
        )


def main(path: str) -> None:
    target = Path(path)
    if target.is_file():
        process_file(target)
    elif target.is_dir():
        for file_path in target.rglob("*"):
            if file_path.is_file():
                process_file(file_path)
    else:
        Console.fail(f"Path not found [white]({path})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        path = input("Enter the path to the file or directory: ").strip()
    else:
        path = sys.argv[1]
    print()
    main(path)
