"""Lists all installed Visual Studio Code extensions with
the option to directly format them as a JSON list."""
from xulbux import FormatCodes, Console, Data
from typing import Optional, cast
import subprocess
import platform
import sys


FIND_ARGS = {"as_json": ["-j", "--json"]}


def check_vscode_installed() -> bool:
    try:
        command = "where" if platform.system() == "Windows" else "which"
        subprocess.run([command, "code"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def get_vscode_extensions() -> Optional[list[str]]:
    try:
        result = subprocess.run(["code", "--list-extensions"], capture_output=True, text=True, shell=True)
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        Console.fail(f"Failed to get extensions: {e.stderr}")


def main() -> None:
    args = Console.get_args(FIND_ARGS)
    if not check_vscode_installed():
        FormatCodes.print("[br:red](Visual Studio Code is not installed or not in PATH.)")
        sys.exit(1)
    extensions = cast(list[str], get_vscode_extensions())
    FormatCodes.print(f"\n[white]Installed extensions: [b]{len(extensions)}[_]")
    FormatCodes.print(
        "\n[white]" + (Data.to_str(extensions, as_json=True) if args.as_json.exists else "\n".join(extensions)) + "[_]\n"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
