#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""Lists all installed Visual Studio Code extensions with
the option to directly format them as a JSON list."""

import os
import platform
import subprocess
from pathlib import Path
from typing import cast
from xulbux import Console, Data, S, StyledText

ARGS = Console.get_args({"as_json": {"-j", "--json"}, "help": {"-h", "--help"}})


# fmt: off
def print_help() -> None:
    title = ["  VS Code Extensions", " — List all installed Visual Studio Code extensions  "]
    StyledText(
        "",
        ("▄" * len("".join(title))),
        (S.INVERSE | S.BG.BLACK)(S.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        (S.BOLD("Usage: "), S.BR.GREEN("vscode-ext "), S.BR.BLUE("[options]")),
        "",
        S.BOLD("Options:"),
        ("  ", S.BR.BLUE("-j"), ", ", S.BR.BLUE("--json"), "    Output as a JSON list"),
        "",
        S.BOLD("Examples:"),
        ("  ", S.BR.GREEN("vscode-ext"), "           ", S.DIM("# ", S.ITALIC("List all installed extensions"))),
        ("  ", S.BR.GREEN("vscode-ext "), S.BR.BLUE("--json"), "    ", S.DIM("# ", S.ITALIC("Output all extension as a JSON list"))),  # noqa: E501
        "",
        sep="\n",
    ).print()
# fmt: on


def get_common_vscode_locations() -> list[tuple[str, str]]:
    """Returns a list of `(executable_name, path)` tuples for common VS Code locations."""
    locations: list[tuple[str, str]] = []
    system = platform.system()

    if system == "Windows":
        localappdata = os.environ.get("LOCALAPPDATA", "")
        programfiles = os.environ.get("PROGRAMFILES", "")
        programfiles_x86 = os.environ.get("PROGRAMFILES(X86)", "")

        if localappdata:
            locations.extend(
                [
                    ("code", str(Path(localappdata) / "Programs" / "Microsoft VS Code" / "bin" / "code.cmd")),
                    (
                        "code-insiders",
                        str(Path(localappdata) / "Programs" / "Microsoft VS Code Insiders" / "bin" / "code-insiders.cmd"),
                    ),
                ]
            )
        if programfiles:
            locations.extend(
                [
                    ("code", str(Path(programfiles) / "Microsoft VS Code" / "bin" / "code.cmd")),
                    ("code-insiders", str(Path(programfiles) / "Microsoft VS Code Insiders" / "bin" / "code-insiders.cmd")),
                ]
            )
        if programfiles_x86:
            locations.extend(
                [
                    ("code", str(Path(programfiles_x86) / "Microsoft VS Code" / "bin" / "code.cmd")),
                    (
                        "code-insiders",
                        str(Path(programfiles_x86) / "Microsoft VS Code Insiders" / "bin" / "code-insiders.cmd"),
                    ),
                ]
            )

    elif system == "Darwin":  # macOS
        locations.extend(
            [
                ("code", "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
                ("code-insiders", "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code-insiders"),
                (
                    "code",
                    str(
                        Path.home()
                        / "Applications"
                        / "Visual Studio Code.app"
                        / "Contents"
                        / "Resources"
                        / "app"
                        / "bin"
                        / "code"
                    ),
                ),
                (
                    "code-insiders",
                    str(
                        Path.home()
                        / "Applications"
                        / "Visual Studio Code - Insiders.app"
                        / "Contents"
                        / "Resources"
                        / "app"
                        / "bin"
                        / "code-insiders"
                    ),
                ),
                ("code", "/usr/local/bin/code"),
                ("code-insiders", "/usr/local/bin/code-insiders"),
            ]
        )

    elif system == "Linux":
        locations.extend(
            [
                ("code", "/usr/bin/code"),
                ("code-insiders", "/usr/bin/code-insiders"),
                ("code", "/usr/local/bin/code"),
                ("code-insiders", "/usr/local/bin/code-insiders"),
                ("code", str(Path.home() / ".local" / "bin" / "code")),
                ("code-insiders", str(Path.home() / ".local" / "bin" / "code-insiders")),
            ]
        )

    return locations


def find_vscode_executable() -> tuple[str, str] | None:
    """Finds VS Code or VS Code Insiders executable.<br>
    Returns a tuple of `(variant_name, executable_path)` or `None` if not found."""
    # FIRST, TRY TO FIND IN 'PATH' ENV VARIABLE
    for variant in ["code", "code-insiders"]:
        try:
            command = "where" if platform.system() == "Windows" else "which"
            result = subprocess.run([command, variant], capture_output=True, check=True, text=True)
            executable = result.stdout.strip().split("\n")[0]  # GET FIRST RESULT
            if executable:
                return (variant, executable)
        except subprocess.CalledProcessError:
            continue

    # IF NOT IN 'PATH' ENV-VAR, CHECK COMMON INSTALLATION LOCATIONS
    for variant, location in get_common_vscode_locations():
        if Path(location).is_file():
            return (variant, location)

    return None


def get_vscode_extensions(executable: str) -> list[str] | None:
    try:
        result = subprocess.run([executable, "--list-extensions"], capture_output=True, text=True, shell=True)
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        Console.fail(f"Failed to get extensions: {e.stderr}")


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    if (vscode_info := find_vscode_executable()) is None:
        StyledText(S.BR.RED("Visual Studio Code is not installed or could not be found."))
        raise SystemExit(1)

    variant, executable = vscode_info
    variant_display = "VS Code Insiders" if variant == "code-insiders" else "VS Code"

    extensions = cast("list[str]", get_vscode_extensions(executable))

    StyledText(
        "",
        "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄",
        (S.INVERSE | S.BG.BLACK)("  Found ", S.BOLD(str(len(extensions))), f" installed {variant_display} extensions  "),
        "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀",
        "",
        S.WHITE(
            Data.render(extensions, indent=2, as_json=True, syntax_highlighting=True).raw
            if ARGS.as_json.exists
            else "\n".join(extensions)
        ),
        "",
        sep="\n",
    ).print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
