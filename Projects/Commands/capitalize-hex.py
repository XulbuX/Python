from xulbux import Console, FormatCodes
from pathlib import Path
import sys
import re


def is_text_file(filepath: Path):
    try:
        with filepath.open("r", encoding="utf-8") as file:
            file.read(1024)
        return True
    except UnicodeDecodeError:
        return False


def capitalize_hex_colors(content: str) -> tuple[str, int]:
    pattern = r"(#|0x)([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b"

    def replace_match(match: re.Match) -> str:
        prefix, hex_value = match.groups()
        return prefix + hex_value.upper()

    new_content, count = re.subn(pattern, replace_match, content)
    return new_content, count


def process_file(file_path: Path, root_dir: Path = Path.cwd()) -> None:
    if not is_text_file(file_path):
        return
    try:
        content = file_path.read_text(encoding="utf-8")
        new_content, modified = capitalize_hex_colors(content)
        if modified:
            file_path.write_text(new_content, encoding="utf-8")
        log_path = str(file_path.relative_to(root_dir))
        Console.done(
            f"{'[b](Updated)' if modified > 0 else '[dim](Checked)'} [br:cyan]({log_path})"
            + f" [dim]({((Console.w() - 50) - len(log_path)) * '.'}) [blue][[b|br:blue]({modified})[blue]]",
            start="",
            end="\n",
        )
    except Exception as e:
        Console.fail(
            f"Error processing [red]({file_path})\n         \t[b|br:red]{e}[_]",
            start="",
            end="\n",
            exit=False,
        )


def main(path: str) -> None:
    target = Path(path)
    if target.is_file():
        process_file(target)
    elif target.is_dir():
        for file_path in target.rglob("*"):
            if file_path.is_file():
                process_file(file_path, path)
    else:
        Console.fail(f"Path not found [white]({path})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        path = input("\nEnter the path to the file or directory: ").strip()
    else:
        path = sys.argv[1]
    if path in ("", None):
        Console.fail("No path was provided")
    print()
    main(path)
