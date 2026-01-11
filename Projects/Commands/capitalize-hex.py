#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Searches and capitalizes all found hex colors
in a single file or every file in a directory."""
from pathlib import Path
from typing import Optional
from xulbux import Console
import re


ARGS = Console.get_args(path="before")


def is_text_file(filepath: Path):
    try:
        with filepath.open("r", encoding="utf-8") as file:
            file.read(1024)
        return True
    except UnicodeDecodeError:
        return False


def capitalize_hex_colors(content: str) -> tuple[str, int]:
    pattern = r"(#|0x)([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b"
    changed = 0

    def replace_match(match: re.Match) -> str:
        nonlocal changed
        prefix, hex_value = match.groups()
        upper_hex = hex_value.upper()
        if hex_value != upper_hex:
            changed += 1
        return prefix + upper_hex

    new_content, _ = re.subn(pattern, replace_match, content)
    return new_content, changed


def process_file(file_path: Path, root_dir: str) -> None:
    if not is_text_file(file_path):
        return
    try:
        content = file_path.read_text(encoding="utf-8")
        new_content, modified = capitalize_hex_colors(content)
        if modified:
            file_path.write_text(new_content, encoding="utf-8")
        log_path = str(file_path.relative_to(root_dir))
        dim = "[dim]" if modified < 1 else ""
        Console.done(
            f"{'[b](Updated)' if modified > 0 else '[dim](Checked)'} [br:cyan]({log_path})"
            + f" [dim]({((Console.w - 50) - len(log_path)) * '.'})" + f" {dim}[blue][[b|br:blue]({modified}){dim}[blue]][_]",
            start="",
            end="\n",
        )
    except Exception as e:
        Console.fail(f"Error processing [red]({file_path})\n         \t[b|br:red]{e}[_]", start="", end="\n", exit=False)


def path_validator(path: str) -> Optional[str]:
    if not Path(path).exists():
        max_w = Console.w - 23
        str_p = path if (l := len(path)) <= max_w else f"...{path[l - (max_w - 3):]}"
        return f"Path [i]({str_p}) doesn't exist."


def main() -> None:
    if len(ARGS.path.values) != 1:
        path = Console.input(
            "\n[b](Path to file/directory:) ",
            validator=path_validator,
            default_val=".",
        ).strip()
    else:
        path = ARGS.path.values[0]

    print()

    if (target := Path(path)).is_file():
        process_file(target, str(target.parent))
    elif target.is_dir():
        for file_path in target.rglob("*"):
            if file_path.is_file():
                process_file(file_path, path)
        print()
    else:
        Console.fail(f"Path not found [white]({path})", end="\n\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
