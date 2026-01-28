#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Tries to package and upload the library in the current or given directory.
Uses 'build'  to build and 'twine' to try to upload the packaged library to PyPI."""
from pathlib import Path
from typing import Optional
from xulbux import FormatCodes, Console, FileSys
import subprocess
import shutil
import sys
import os


ARGS = Console.get_args({
    "lib_base": "before",
    "only_build": {"-ob", "--only-build"},
    "verbose": {"-v", "--verbose"},
    "help": {"-h", "--help"},
})


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
    py_dir = Path.home() / "AppData" / "Roaming" / "Python"
    versions = []
    try:
        for d in py_dir.iterdir():
            if d.name.startswith("Python3"):
                versions.append(d.name)
        return sorted(versions)[-1] if versions else None
    except:
        return None


def find_twine_path() -> Optional[str]:
    twine_exe_paths = [Path(sys.base_prefix) / "Scripts" / "twine.exe"]

    if py_version := get_latest_python_version():
        twine_exe_paths.extend([
            Path.home() / "AppData" / "Local" / "Programs" / "Python" / py_version / "Scripts" / "twine.exe",
            Path.home() / "AppData" / "Roaming" / "Python" / py_version / "Scripts" / "twine.exe",
        ])

    # CHECK PROGRAM FILES FOR PYTHON INSTALLATIONS
    program_files = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
    if program_files.exists():
        try:
            for d in program_files.iterdir():
                if d.name.startswith("Python"):
                    twine_exe_paths.append(d / "Scripts" / "twine.exe")
        except OSError:
            pass

    for path in twine_exe_paths:
        if Path(path).is_file():
            return str(path)

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
    dir_path = Path(dir)
    if dir_path.exists() and dir_path.is_dir():
        if remove_dir:
            shutil.rmtree(dir_path)
            return None
        for item in dir_path.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                Console.fail(f"Failed to delete [white]{item}[_c]. Reason: {e}")


def main() -> None:
    if ARGS.help.exists or not (ARGS.lib_base.exists or ARGS.only_build.exists or ARGS.verbose.exists):
        print_help()
        return

    if ARGS.lib_base.values:
        os.chdir(str(ARGS.lib_base.values[0]))  # CHANGE CWD TO LIB BASE
    run_command(f"py -m build{' --verbose ' if ARGS.verbose.exists else ''}", verbose=ARGS.verbose.exists)
    dist = str(Path.cwd() / "dist")

    if ARGS.only_build.exists:
        Console.done(f"Built to [white]{dist}[_c]\n[dim](Not uploading as per argument.)", start="\n", end="\n\n")
    else:
        twine_path = find_twine_path()
        run_command(f'"{twine_path}" upload{' --verbose ' if ARGS.verbose.exists else ' '}dist/*', verbose=ARGS.verbose.exists)
        Console.done(f"\nSuccessfully built and uploaded the library.", start="\n", end="\n\n")

        if FormatCodes.input("\nDirectly remove [white](dist) directory? [dim]((Y/n) > )").lower() in ("", "y", "yes"):
            FileSys.remove(dist)
            print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
