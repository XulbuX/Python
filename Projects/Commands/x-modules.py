#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""List all modules imported across Python files in the script directory.
Can filter to show only non-standard library modules."""
from pathlib import Path
from typing import Optional
from xulbux.console import Spinner
from xulbux import FormatCodes, Console, FileSys, Data
import subprocess
import sys
import re


ARGS = Console.get_args(
    allow_spaces=True,
    external_only={"-e", "--external"},
    directory={"-d", "--dir", "--directory"},
    recursive={"-r", "--recursive"},
    list={"-l", "--list"},
    as_json={"-j", "--json"},
    install={"-i", "--install"},
    help={"-h", "--help"},
)

# PYTHON STANDARD LIBRARY MODULES (Python 3.x)
STDLIB_MODULES = {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore", "atexit", "audioop", "base64", "bdb",
    "binascii", "binhex", "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
    "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser", "contextlib", "contextvars", "copy",
    "copyreg", "cProfile", "crypt", "csv", "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis",
    "distutils", "doctest", "email", "encodings", "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch",
    "formatter", "fractions", "ftplib", "functools", "gc", "getopt", "getpass", "gettext", "glob", "graphlib", "grp", "gzip",
    "hashlib", "heapq", "hmac", "html", "http", "imaplib", "imghdr", "imp", "importlib", "inspect", "io", "ipaddress",
    "itertools", "json", "keyword", "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox", "mailcap", "marshal",
    "math", "mimetypes", "mmap", "modulefinder", "msilib", "msvcrt", "multiprocessing", "netrc", "nis", "nntplib", "numbers",
    "operator", "optparse", "os", "ossaudiodev", "parser", "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint", "profile", "pstats", "pty", "pwd", "py_compile",
    "pyclbr", "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter", "runpy", "sched",
    "secrets", "select", "selectors", "shelve", "shlex", "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr", "socket",
    "socketserver", "spwd", "sqlite3", "ssl", "stat", "statistics", "string", "stringprep", "struct", "subprocess", "sunau",
    "symbol", "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "test",
    "textwrap", "threading", "time", "timeit", "tkinter", "token", "tokenize", "tomllib", "trace", "traceback", "tracemalloc",
    "tty", "turtle", "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile",
    "zipimport", "zlib", "_thread"
}


def print_help():
    help_text = """\
[b|in|bg:black]( Modules - List all imported modules across scripts )

[b](Usage:) [br:green](modules) [br:blue]([options])

[b](Options:)
  [br:blue](-e), [br:blue](--external)          Show only non-standard library modules
  [br:blue](-d), [br:blue](--directory PATH)    Specify directory to scan [dim]((default: script directory))
  [br:blue](-r), [br:blue](--recursive)         Scan subdirectories recursively
  [br:blue](-l), [br:blue](--list)              Output only module names without extra info
  [br:blue](-j), [br:blue](--json)              Output as JSON format [dim]((ignored if [br:blue](-i) is used))
  [br:blue](-i), [br:blue](--install)           Install all external modules using pip

[b](Examples:)
  [br:green](modules)                 [dim](# [i](List all imported modules))
  [br:green](modules) [br:blue](--external)      [dim](# [i](List only external/third-party modules))
  [br:green](modules) [br:blue](-d "./src")      [dim](# [i](Scan specific directory))
  [br:green](modules) [br:blue](-d "./src" -r)   [dim](# [i](Scan directory recursively))
  [br:green](modules) [br:blue](--list)          [dim](# [i](Output only the list of module names))
  [br:green](modules) [br:blue](--json)          [dim](# [i](Output as JSON format))
  [br:green](modules) [br:blue](--install)       [dim](# [i](Install all external modules))
"""
    FormatCodes.print(help_text)


def extract_imports(file_path: Path) -> set[str]:
    """Extract all imported module names from a Python file."""
    imports = set()
    import_pattern = re.compile(r"^\s*(?:from\s+(\S+)|import\s+(\S+))", re.MULTILINE)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

            # REMOVE DOCSTRINGS AND COMMENTS BEFORE PROCESSING
            # TRIPLE-QUOTED STRINGS (DOCSTRINGS)
            content = re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', '', content)
            # SINGLE/DOUBLE QUOTED STRINGS
            content = re.sub(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', '', content)
            # COMMENTS (LINES STARTING WITH #)
            content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)

            for match in import_pattern.finditer(content):
                module = match.group(1) or match.group(2)
                # SKIP RELATIVE IMPORTS (starting with .)
                if module.startswith("."):
                    continue
                # ADD TOP-LEVEL MODULE NAME
                imports.add(module.split(".")[0])
    except Exception:
        pass

    return imports


def get_all_modules(directory: Path, recursive: bool = False, external_only: bool = False) -> dict[str, list[str]]:
    """Get all modules used across Python files, grouped by module name."""
    module_usage: dict[str, list[str]] = {}

    if not directory.is_dir():
        raise ValueError(f"Directory not found: {directory}")

    def scan_directory(dir_path: Path, base_path: Optional[Path] = None):
        """Scan a directory for Python files and extract imports."""
        if base_path is None:
            base_path = dir_path
        try:
            for full_path in dir_path.iterdir():
                if full_path.is_file() and full_path.suffix in (".py", ".pyw"):
                    for module in extract_imports(full_path):
                        if external_only and module in STDLIB_MODULES:
                            continue
                        if module not in module_usage:
                            module_usage[module] = []
                        module_usage[module].append(str(full_path.relative_to(base_path).with_suffix('')))
                elif recursive and full_path.is_dir():
                    scan_directory(full_path, base_path)
        except PermissionError:
            pass  # SKIP DIRECTORIES WE CAN'T ACCESS

    scan_directory(directory)
    return module_usage


def show_and_install_modules(modules: dict[str, list[str]], external_only: bool, install: bool = False) -> None:
    title_start = "INSTALLING" if install else "FOUND"
    output = (
        f"[b|bg:black]([in]( {title_start} ) {len(modules)} [in]( EXTERNAL MODULES ))\n" if external_only
        else f"[b|bg:black]([in]( {title_start} ) {len(modules)} [in]( MODULES ))\n"
    )

    if ARGS.list.exists:
        output += f"\n[b|br:cyan]{'\n'.join(sorted(modules.keys()))}[_]"
    else:
        console_w = Console.w
        num_width = len(str(len(modules)))
        for i, (module, files) in enumerate(sorted(modules.items()), 1):
            usage_count = len(files)
            line = f"\n [i|dim|br:cyan]({i:>{num_width}})  [b|br:cyan]({module})"
            line += f" [dim](used in {usage_count} file{'s' if usage_count != 1 else ''})"
            rendered_line_len = len(FormatCodes.remove(line))

            if usage_count <= 5:
                if (rendered_line_len + len(file_paths := ", ".join(sorted(files)))) > console_w:
                    line += f" {file_paths[:console_w - (rendered_line_len + 1)]}…"
                else:
                    line += f" {file_paths}"
            else:
                file_paths = ", ".join(sorted(files)[:3])
                overflow_part = f", [dim](+{usage_count - 3} more)"
                rendered_overflow_len = len(FormatCodes.remove(overflow_part))
                if (rendered_line_len + len(file_paths) + rendered_overflow_len) > console_w:
                    line += f" {file_paths[:console_w - (rendered_line_len + rendered_overflow_len + 1)]}…{overflow_part}"
                else:
                    line += f" {file_paths}{overflow_part}"

            output += line

    output += "\n"
    FormatCodes.print(output)

    ################################################## INSTALLATION ##################################################
    if not install:
        return
    if not Console.confirm("Proceed with installation?"):
        FormatCodes.print("\n[i|dim](Installation cancelled.)\n")
        return

    print()
    failed_modules = []

    for module in sorted(modules):
        with Spinner(f"Installing [b]({module})", ["[br:cyan]({l} [b]({a})) "]).context():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", module],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 MINUTE TIMEOUT PER MODULE
                )
                
                if result.returncode == 0:
                    FormatCodes.print(f"[br:green](✓ Installed [b]({module}))")
                else:
                    FormatCodes.print(f"[br:red](⨯ Failed to install [b]({module}):)\n[red]│ " + "\n[red]│ ".join(result.stderr.strip().splitlines()) + "[_]")
                    failed_modules.append(module)
            except subprocess.TimeoutExpired:
                FormatCodes.print(f"[br:red](⨯ Timed out installing [b]({module}))")
                failed_modules.append(module)
            except Exception as e:
                FormatCodes.print(f"[br:red](⨯ Error installing [b]({module}):)\n[red]│ " + "\n[red]│ ".join(str(e).splitlines()) + "[_]")
                failed_modules.append(module)

    print()
    if failed_modules:
        FormatCodes.print(f"[b|br:yellow](Failed to install {len(failed_modules)} module{'s' if len(failed_modules) != 1 else ''}:)")
        for module in failed_modules:
            FormatCodes.print(f"[yellow]([dim]( • ){module})")
        print()
    else:
        FormatCodes.print("[b|br:green](All modules installed successfully!)\n")


def main() -> None:
    print()

    if ARGS.help.exists:
        print_help()
        return

    external_only = ARGS.external_only.exists or ARGS.install.exists
    directory = Path(ARGS.directory.value).expanduser().resolve() if ARGS.directory.value else FileSys.script_dir

    with Spinner().context():
        modules = get_all_modules(
            directory=directory,
            recursive=ARGS.recursive.exists,
            external_only=external_only,
        )

    if not modules:
        if external_only:
            FormatCodes.print("[i|dim](No external modules found)\n")
        else:
            FormatCodes.print("[i|dim](No modules found)\n")
        return

    if not ARGS.install.exists and ARGS.as_json.exists:
        if ARGS.list.exists:
            json_data = sorted(modules.keys())
        else:
            json_data = {module: sorted(files) for module, files in sorted(modules.items())}
        FormatCodes.print(f"\n{Data.render(
            json_data,
            indent=2,
            as_json=True,
            syntax_highlighting=True,
        )}\n")

    else:
        show_and_install_modules(modules, external_only, ARGS.install.exists)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        FormatCodes.print("\n[i|dim](Cancelled by user.)\n")
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
