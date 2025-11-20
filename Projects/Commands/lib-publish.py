#!/usr/bin/env python3
"""Tries to package and upload the library in the current or given directory.
Uses 'build'  to build and 'twine' to try to upload the packaged library to PyPI."""
from xulbux import FormatCodes, Console, Path
from xulbux.console import Args
from typing import Optional
import subprocess
import shutil
import sys
import os


ARGS = Console.get_args({
    "lib_base": "before",
    "only_build": {"-ob", "--only-build"},
    "verbose": {"-v", "--verbose"},
    "help": {"-h", "--help"},
}, allow_spaces=True)


def print_help():
    help_text = """
[b|in|bg:black]( Library Publisher - Build and publish Python libraries to PyPI )

[b](Usage:) [br:green](lib-publish) [br:cyan](<lib_base>) [br:blue]([options])

[b](Arguments:)
  [br:cyan](lib_base)             Base directory of the library [dim]((default: CWD))

[b](Options:)
  [br:blue](-ob), [br:blue](--only-build)    Only build the library, do not upload to PyPI
  [br:blue](-v), [br:blue](--verbose)        Show verbose output during build and upload

[b](Examples:)
  [br:green](lib-publish) [br:cyan]("/path/to/lib_base_dir") [br:blue](--verbose)       [dim](# [i](Build and upload with verbose output))
  [br:green](lib-publish) [br:cyan]("/path/to/lib_base_dir") [br:blue](--only-build)    [dim](# [i](Only build the library, do not upload))
"""
    FormatCodes.print(help_text)


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
        twine_exe_paths = [
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
        for path in twine_exe_paths:
            if os.path.isfile(path):
                return path
    Console.fail("[white](twine.exe) not found in expected locations. Please verify installation.")


def run_command(command: str, verbose: bool = False) -> None:
    try:
        if verbose:
            Console.info(f"Running command: [white]{command}[_c]", start="\n", end="\n\n")
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


def main() -> None:
    if ARGS.help.exists or not (ARGS.lib_base.exists or ARGS.only_build.exists or ARGS.verbose.exists):
        print_help()
        return

    if ARGS.lib_base.exists:
        os.chdir(str(ARGS.lib_base.values[0]))  # CHANGE CWD TO LIB BASE
    run_command(f"py -m build{' --verbose ' if ARGS.verbose.exists else ''}", verbose=ARGS.verbose.exists)
    dist = os.path.join(os.getcwd(), "dist")

    if ARGS.only_build.exists:
        Console.done(f"Built to [white]{dist}[_c]\n[dim](Not uploading as per argument.)", start="\n", end="\n\n")
    else:
        twine_path = find_twine_path()
        run_command(f'"{twine_path}" upload{' --verbose ' if ARGS.verbose.exists else ' '}dist/*', verbose=ARGS.verbose.exists)
        Console.done(f"\nSuccessfully built and uploaded the library.", start="\n", end="\n\n")

        if FormatCodes.input("\nDirectly remove [white](dist) directory? [dim]((Y/n) > )").lower() in ("", "y", "yes"):
            Path.remove(dist)
            print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
