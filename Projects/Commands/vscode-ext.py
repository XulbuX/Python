#!/usr/bin/env python3
"""Lists all installed Visual Studio Code extensions with
the option to directly format them as a JSON list."""
from typing import Optional, cast
from xulbux import FormatCodes, Console, Data
import subprocess
import platform
import os


ARGS = Console.get_args(as_json={"-j", "--json"})


def get_common_vscode_locations() -> list[tuple[str, str]]:
    """Returns a list of `(executable_name, path)` tuples for common VS Code locations."""
    locations: list[tuple[str, str]] = []
    system = platform.system()

    if system == "Windows":
        localappdata = os.environ.get("LOCALAPPDATA", "")
        programfiles = os.environ.get("PROGRAMFILES", "")
        programfiles_x86 = os.environ.get("PROGRAMFILES(X86)", "")

        if localappdata:
            locations.extend([
                ("code", os.path.join(localappdata, "Programs", "Microsoft VS Code", "bin", "code.cmd")),
                (
                    "code-insiders",
                    os.path.join(localappdata, "Programs", "Microsoft VS Code Insiders", "bin", "code-insiders.cmd")
                ),
            ])
        if programfiles:
            locations.extend([
                ("code", os.path.join(programfiles, "Microsoft VS Code", "bin", "code.cmd")),
                ("code-insiders", os.path.join(programfiles, "Microsoft VS Code Insiders", "bin", "code-insiders.cmd")),
            ])
        if programfiles_x86:
            locations.extend([
                ("code", os.path.join(programfiles_x86, "Microsoft VS Code", "bin", "code.cmd")),
                ("code-insiders", os.path.join(programfiles_x86, "Microsoft VS Code Insiders", "bin", "code-insiders.cmd")),
            ])

    elif system == "Darwin":  # macOS
        locations.extend([
            ("code", "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
            ("code-insiders", "/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code-insiders"),
            ("code", os.path.expanduser("~/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code")),
            (
                "code-insiders",
                os.path
                .expanduser("~/Applications/Visual Studio Code - Insiders.app/Contents/Resources/app/bin/code-insiders")
            ),
            ("code", "/usr/local/bin/code"),
            ("code-insiders", "/usr/local/bin/code-insiders"),
        ])

    elif system == "Linux":
        locations.extend([
            ("code", "/usr/bin/code"),
            ("code-insiders", "/usr/bin/code-insiders"),
            ("code", "/usr/local/bin/code"),
            ("code-insiders", "/usr/local/bin/code-insiders"),
            ("code", os.path.expanduser("~/.local/bin/code")),
            ("code-insiders", os.path.expanduser("~/.local/bin/code-insiders")),
        ])

    return locations


def find_vscode_executable() -> Optional[tuple[str, str]]:
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
        if os.path.isfile(location):
            return (variant, location)

    return None


def get_vscode_extensions(executable: str) -> Optional[list[str]]:
    try:
        result = subprocess.run([executable, "--list-extensions"], capture_output=True, text=True, shell=True)
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        Console.fail(f"Failed to get extensions: {e.stderr}")


def main() -> None:
    if (vscode_info := find_vscode_executable()) is None:
        FormatCodes.print("[br:red](Visual Studio Code is not installed or could not be found.)")
        raise SystemExit(1)

    variant, executable = vscode_info
    variant_display = "VS Code Insiders" if variant == "code-insiders" else "VS Code"

    extensions = cast(list[str], get_vscode_extensions(executable))
    FormatCodes.print(
        f"\n[b|bg:black]([in]( FOUND ) {len(extensions)} [in]( INSTALLED {variant_display.upper()} EXTENSIONS ))"
    )
    FormatCodes.print(
        "\n[white]" + (
            Data.render(
                extensions,
                indent=2,
                as_json=True,
                syntax_highlighting=True,
            ) if ARGS.as_json.exists else "\n".join(extensions)
        ) + "[_]\n"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
