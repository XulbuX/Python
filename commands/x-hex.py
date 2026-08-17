#!/usr/bin/env python3
# x-cmds:file[update]

"""Transform all hex color codes in a file or directory:
uppercase, lowercase, grayscale, hue rotation, inversion, and more."""

import fnmatch
from enum import Enum
from pathlib import Path
import regex as rx
from xulbux import Console, FormatCodes
from xulbux.color import hexa
from xulbux.regex import LazyRegex


class Operation(Enum):
    UPPER = "upper"
    LOWER = "lower"
    GRAYSCALE = "grayscale"
    ROTATE = "rotate"
    INVERT = "invert"


ARGS = Console.get_args({
    "path": "before",
    "upper": {"-u", "--upper"},
    "lower": {"-l", "--lower"},
    "grayscale": {"-g", "--grayscale"},
    "rotate": {"-r", "--rotate"},
    "invert": {"-i", "--invert"},
    "apply_gitignore": {"-G", "--gitignore"},
    "check": {"-d", "--dry"},
    "help": {"-h", "--help"},
})

PATTERNS = LazyRegex(hex=r"(?i)(#)([0-9A-F]{8}|[0-9A-F]{6}|[0-9A-F]{3,4})\b|(0x)([0-9A-F]{8}|[0-9A-F]{6})\b")


def print_help() -> None:
    help_text = """
[b|in|bg:black]( Hex Colors — Transform hex color codes in a file or directory )

[b](Usage:) [br:green](x-hex) [br:cyan](<path> ...) [br:blue]([operation] [options])

[b](Arguments:)
  [br:cyan](path)                One or more paths to files or directories to process

[b](Operations:)
  [br:blue](-u), [br:blue](--upper)         Uppercase all hex colors [dim]((#9EB6FF))
  [br:blue](-l), [br:blue](--lower)         Lowercase all hex colors [dim]((#9eb6ff))
  [br:blue](-g), [br:blue](--grayscale)     Convert all hex colors to grayscale
  [br:blue](-r), [br:blue](--rotate[dim](=)DEG)    Rotate the hue of all hex colors by [br:blue](DEG) degrees [dim]((0-360))
  [br:blue](-i), [br:blue](--invert)        Invert all hex colors
[b](Options:)
  [br:blue](-G), [br:blue](--gitignore)     Apply .gitignore rules when scanning directories
  [br:blue](-d), [br:blue](--dry)           Dry-run: show what would change without modifying any files

[b](Examples:)
  [br:green](x-hex) [br:cyan]("./styles.css")                 [dim](# [i](Uppercase hex colors in a single file))
  [br:green](x-hex) [br:cyan]("./src") [br:blue](--lower)                [dim](# [i](Lowercase hex colors in all files))
  [br:green](x-hex) [br:cyan]("./src") [br:blue](--grayscale)            [dim](# [i](Convert all hex colors to grayscale))
  [br:green](x-hex) [br:cyan]("./styles.css") [br:blue](--rotate[dim](=)180)    [dim](# [i](Rotate hue by 180 degrees))
  [br:green](x-hex) [br:cyan]("./styles.css") [br:blue](--invert)        [dim](# [i](Invert all hex colors))
"""
    FormatCodes.print(help_text)


def is_text_file(filepath: Path) -> bool:
    try:
        with filepath.open("r", encoding="utf-8") as file:
            file.read(1024)
        return True
    except (UnicodeDecodeError, OSError):
        return False


def load_gitignore_patterns(directory: str) -> list[tuple[str, str]]:
    patterns: list[tuple[str, str]] = []
    current_dir = Path(directory).resolve()

    for parent in [current_dir, *list(current_dir.parents)]:
        gitignore_path = parent / ".gitignore"

        if gitignore_path.exists():
            try:
                with open(gitignore_path, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append((str(parent), line))

            except (OSError, UnicodeDecodeError):
                continue

    return patterns


def is_gitignored(file_path: str, patterns: list[tuple[str, str]]) -> bool:
    if not patterns:
        return False

    file_path = str(Path(file_path).resolve())

    for gitignore_dir, pattern in patterns:
        full_pattern = str(Path(gitignore_dir) / (pattern[1:] if pattern.startswith("/") else pattern))

        if pattern.endswith("/"):
            if Path(file_path).is_dir() and fnmatch.fnmatch(file_path, full_pattern):
                return True

        else:
            if fnmatch.fnmatch(file_path, full_pattern):
                return True

            parent = Path(file_path)

            while parent != parent.parent:
                parent = parent.parent
                if fnmatch.fnmatch(str(parent), full_pattern):
                    return True

    return False


def process_file(file_path: Path, root_dir: str, operation: Operation, degrees: int = 0, dry_run: bool = False) -> None:  # ruff:ignore[complex-structure]
    if not is_text_file(file_path):
        return

    log_path = str(file_path.relative_to(root_dir))

    try:
        changed = 0
        # IN DRY-RUN MODE, SKIP COLLECTING OUTPUT LINES ENTIRELY
        out_lines: list[str] | None = None if dry_run else []

        def replace_match(match: rx.Match[str]) -> str:
            nonlocal changed
            h_prefix, h_hex, ox_prefix, ox_hex = match.groups()
            prefix = h_prefix or ox_prefix
            hex_value = h_hex or ox_hex

            if operation == Operation.UPPER:
                result = hex_value.upper()
            elif operation == Operation.LOWER:
                result = hex_value.lower()
            else:
                try:
                    color = hexa(prefix + hex_value)

                    if operation == Operation.GRAYSCALE:
                        transformed = color.grayscale()
                    elif operation == Operation.ROTATE:
                        transformed = color.rotate(degrees)
                    elif operation == Operation.INVERT:
                        transformed = color.invert()
                    else:
                        return match.group(0)

                    # STRIP # AND RESTORE ORIGINAL PREFIX
                    result = str(transformed).lstrip("#")

                except Exception:
                    return match.group(0)

            if (new_value := prefix + result) != match.group(0):
                changed += 1

            return new_value

        # STREAM LINE-BY-LINE: NEVER LOADS FULL FILE INTO MEMORY
        with file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if "#" not in line and "0x" not in line:
                    if out_lines is not None:
                        out_lines.append(line)
                else:
                    new_line = PATTERNS.hex.sub(replace_match, line)
                    if out_lines is not None:
                        out_lines.append(new_line)

        if changed and not dry_run and out_lines:
            file_path.write_text("".join(out_lines), encoding="utf-8")

        was_modified: bool = changed > 0
        dim: str = "[dim]" if not was_modified else ""
        title: str = "Would update" if was_modified and dry_run else ("Updated" if was_modified else "[dim|green](✓ checked)")

        if len(log_path) > (max_path_len := max(10, Console.width - 50)):
            log_path = "…" + log_path[-max_path_len:]
        dots = max(0, max_path_len - len(log_path))

        Console.log(
            title,
            f"{dim}[br:cyan|link:file:///{file_path.resolve()}]({log_path})[_] "
            f"{dim}[br:black]{dots * '.'}[_]{' ' if dots > 0 else ''}"
            f"{dim}[blue][[b|br:blue]({changed}){dim}[blue]][_]",
            title_bg_color="br:blue" if was_modified else None,
            start="",
            end="\n",
        )

    except Exception as exc:
        Console.fail(
            f"Error processing [br:red|link:file:///{file_path.resolve()}]({log_path}):\n[red]{exc}[_]",
            start="",
            end="\n",
            exit=False,
        )


def main() -> None:  # ruff:ignore[complex-structure]
    if ARGS.help.exists or not ARGS.path.values:
        print_help()
        return

    paths = ARGS.path.values

    # DETERMINE OPERATION
    degrees = 0
    if ARGS.upper.exists:
        operation = Operation.UPPER
    elif ARGS.lower.exists:
        operation = Operation.LOWER
    elif ARGS.grayscale.exists:
        operation = Operation.GRAYSCALE
    elif ARGS.rotate.exists:
        try:
            degrees = int("".join(ARGS.rotate.values).strip())
        except (ValueError, TypeError):
            Console.fail(
                "[br:blue](--rotate) requires a degree value (0-360), e.g. [br:blue](--rotate=180)", start="\n", end="\n\n"
            )
            return
        operation = Operation.ROTATE
    elif ARGS.invert.exists:
        operation = Operation.INVERT
    else:
        Console.fail(
            "No operation given.\n"
            "Use [br:blue](--upper), [br:blue](--lower), [br:blue](--grayscale),"
            "[br:blue](--rotate[dim](=)DEG) or [br:blue](--invert).",
            start="\n",
            end="\n\n",
        )
        return

    dry_run = ARGS.check.exists

    for path in paths:
        print()

        if (target := Path(path)).is_file():
            process_file(target, str(target.parent), operation, degrees, dry_run)

        elif target.is_dir():
            gitignore_patterns = load_gitignore_patterns(path) if ARGS.apply_gitignore.exists else []

            for file_path in target.rglob("*"):
                if file_path.is_file():
                    if ARGS.apply_gitignore.exists and is_gitignored(str(file_path), gitignore_patterns):
                        continue
                    process_file(file_path, path, operation, degrees, dry_run)

        else:
            Console.fail(f"Path not found [white]{path}[_]", exit=False)

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
