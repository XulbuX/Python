#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Transform all hex color codes in a file or directory:
uppercase, lowercase, grayscale, hue rotation, inversion, and more."""
from pathlib import Path
from typing import Optional
from xulbux.color import hexa
from xulbux import FormatCodes, Console
import re


ARGS = Console.get_args({
    "path": "before",
    "upper": {"-u", "--upper"},
    "lower": {"-l", "--lower"},
    "grayscale": {"-g", "--grayscale"},
    "rotate": {"-r", "--rotate"},
    "invert": {"-i", "--invert"},
    "help": {"-h", "--help"},
})


def print_help():
    help_text = """
[b|in|bg:black]( Hex Colors \u2014 Transform hex color codes in a file or directory )

[b](Usage:) [br:green](x-hex) [br:cyan](<path>) [br:blue]([operation])

[b](Arguments:)
  [br:cyan](path)                    Path to a file or directory to process

[b](Operations:) [dim]((default: [br:blue](--upper)))
  [br:blue](-u), [br:blue](--upper)              Uppercase all hex colors [dim](([b](#FF0000)))
  [br:blue](-l), [br:blue](--lower)              Lowercase all hex colors [dim](([b](#FF0000)))
  [br:blue](-g), [br:blue](--grayscale)          Convert all hex colors to grayscale
  [br:blue](-r), [br:blue](--rotate[dim](=)DEG)         Rotate the hue of all hex colors by DEG degrees [dim]((0\u2013360))
  [br:blue](-i), [br:blue](--invert)             Invert all hex colors

[b](Examples:)
  [br:green](x-hex) [br:cyan]("./styles.css")                  [dim](# [i](Uppercase hex colors in a single file))
  [br:green](x-hex) [br:cyan]("./src") [br:blue](--lower)               [dim](# [i](Lowercase hex colors in all files))
  [br:green](x-hex) [br:cyan]("./src") [br:blue](--grayscale)           [dim](# [i](Convert all hex colors to grayscale))
  [br:green](x-hex) [br:cyan]("./styles.css") [br:blue](--rotate[dim](=)180)    [dim](# [i](Rotate hue by 180 degrees))
  [br:green](x-hex) [br:cyan]("./styles.css") [br:blue](--invert)           [dim](# [i](Invert all hex colors))
"""
    FormatCodes.print(help_text)


def is_text_file(filepath: Path) -> bool:
    try:
        with filepath.open("r", encoding="utf-8") as file:
            file.read(1024)
        return True
    except UnicodeDecodeError:
        return False


def transform_hex_colors(content: str, operation: str, degrees: int = 0) -> tuple[str, int]:
    pattern = r"(#|0x)([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b"
    changed = 0

    def replace_match(match: re.Match[str]) -> str:
        nonlocal changed
        prefix, hex_value = match.groups()

        if operation == "upper":
            result = hex_value.upper()
        elif operation == "lower":
            result = hex_value.lower()
        else:
            try:
                color = hexa(prefix + hex_value)
                if operation == "grayscale":
                    transformed = color.grayscale()
                elif operation == "rotate":
                    transformed = color.rotate(degrees)
                elif operation == "invert":
                    transformed = color.invert()
                else:
                    return match.group(0)
                # STRIP # AND RESTORE ORIGINAL PREFIX
                result = str(transformed).lstrip("#")
            except Exception:
                return match.group(0)

        new_value = prefix + result
        if new_value != match.group(0):
            changed += 1
        return new_value

    new_content, _ = re.subn(pattern, replace_match, content)
    return new_content, changed


def process_file(file_path: Path, root_dir: str, operation: str, degrees: int = 0) -> None:
    if not is_text_file(file_path):
        return
    try:
        content = file_path.read_text(encoding="utf-8")
        new_content, modified = transform_hex_colors(content, operation, degrees)
        if modified:
            file_path.write_text(new_content, encoding="utf-8")
        log_path = str(file_path.relative_to(root_dir))
        dim = "[dim]" if modified < 1 else ""
        Console.done(
            f"{'[b](Updated)' if modified > 0 else '[dim](Checked)'} [br:cyan|link:file:///{file_path.resolve()}]({log_path})"
            + f" [dim]({((Console.width - 50) - len(log_path)) * '.'})"
            + f" {dim}[blue][[b|br:blue]({modified}){dim}[blue]][_]",
            start="",
            end="\n",
        )
    except Exception as exc:
        Console.fail(f"Error processing [red]({file_path})\n         \t[b|br:red]{exc}[_]", start="", end="\n", exit=False)


def path_validator(path: str) -> Optional[str]:
    if not Path(path).exists():
        max_w = Console.width - 23
        str_p = path if (l := len(path)) <= max_w else f"...{path[l - (max_w - 3):]}"
        return f"Path [i]({str_p}) doesn't exist."


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    if len(ARGS.path.values) != 1:
        path = Console.input(
            "\n[b](Path to file/directory:) ",
            validator=path_validator,
            default_val=".",
        ).strip()
    else:
        path = ARGS.path.values[0]

    # DETERMINE OPERATION
    degrees = 0
    if ARGS.lower.exists:
        operation = "lower"
    elif ARGS.grayscale.exists:
        operation = "grayscale"
    elif ARGS.rotate.exists:
        try:
            degrees = int("".join(ARGS.rotate.values).strip())
        except (ValueError, TypeError):
            Console.fail("--rotate requires a degree value (0\u2013360), e.g. [br:blue](--rotate=180)", start="\n", end="\n\n")
            return
        operation = "rotate"
    elif ARGS.invert.exists:
        operation = "invert"
    else:
        operation = "upper"  # DEFAULT

    print()

    if (target := Path(path)).is_file():
        process_file(target, str(target.parent), operation, degrees)
    elif target.is_dir():
        for file_path in target.rglob("*"):
            if file_path.is_file():
                process_file(file_path, path, operation, degrees)
        print()
    else:
        Console.fail(f"Path not found [white]({path})", end="\n\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
