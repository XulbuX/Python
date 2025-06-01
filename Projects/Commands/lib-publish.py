"""Tries to package and upload the library in the current or given directory.
Uses 'twine' to try to upload the packaged library to PyPI."""
# pip install build twine xulbux
from xulbux import FormatCodes, Console, Path
from xulbux.xx_console import Args
from typing import Optional
import subprocess
import shutil
import sys
import os


FIND_ARGS = {
    "lib_base": [
        "-p", "--path", "-d", "--dir", "--directory",
        "-b", "--base-dir", "-l", "--lib", "--library"
    ],
    "verbose": ["-v", "--verbose"],
}


def get_latest_python_version() -> Optional[str]:
    py_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Python")
    versions = []
    try:
        for d in os.listdir(py_dir):
            if d.startswith("Python3"):
                versions.append(d)
        return sorted(versions)[-1] if versions else None
    except:
        return None


def find_twine_path() -> Optional[str]:
    if py_version := get_latest_python_version():
        python_paths = [
            os.path.join(sys.base_prefix, "Scripts", "twine.exe"),
            os.path.join(
                os.path.expanduser("~"), "AppData", "Local", "Programs",
                "Python", py_version, "Scripts", "twine.exe"
            ),
            os.path.join(
                os.path.expanduser("~"), "AppData", "Roaming",
                "Python", py_version, "Scripts", "twine.exe"
            ),
        ]
        for path in python_paths:
            if os.path.isfile(path):
                return path
    Console.fail("[white](twine.exe) not found in expected locations. Please verify installation.")


def run_command(command: str) -> None:
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        Console.fail(f"Error executing command: {e}")
        sys.exit(1)


def remove_dir_contents(dir: str, remove_dir: bool = False) -> None:
    if os.path.exists(dir) and os.path.isdir(dir):
        if remove_dir:
            shutil.rmtree(dir)
            return None
        for filename in os.listdir(dir):
            file_path = os.path.join(dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                Console.fail(f"Failed to delete [white]{file_path}[_c]. Reason: {e}")


def main(args: Args) -> None:
    os.chdir(args.lib_base.value)
    run_command(f"py -m build{' --verbose ' if args.verbose.exists else ''}")
    twine_path = find_twine_path()
    run_command(f'"{twine_path}" upload{' --verbose ' if args.verbose.exists else ' '}dist/*')
    if FormatCodes.input("\nDirectly remove [white](dist) directory? [dim]((Y/n) > )").lower() in ("", "y", "yes"):
        Path.remove(os.path.join(os.getcwd(), "dist"))
        print()


if __name__ == "__main__":
    try:
        main(Console.get_args(FIND_ARGS))
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
