#!/usr/bin/env python3
"""List all modules imported across Python files in the script directory.
Can filter to show only non-standard library modules."""
from xulbux import FormatCodes, Console, Data, Path
from typing import Optional
import re
import os


ARGS = Console.get_args({
    "external": ["-e", "--external"],
    "directory": ["-d", "--dir", "--directory"],
    "recursive": ["-r", "--recursive"],
    "no_formatting": ["-nf", "--no-formatting"],
    "as_json": ["-j", "--json"],
    "help": ["-h", "--help"],
})

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
    help_text = """
[b|in]( Modules - List all imported modules across scripts )

[b](Usage:) [br:green](modules) [br:blue]([options])

[b](Options:)
  [br:blue](-e), [br:blue](--external)          Show only non-standard library modules
  [br:blue](-d), [br:blue](--directory PATH)    Specify directory to scan (default: script directory)
  [br:blue](-r), [br:blue](--recursive)         Scan subdirectories recursively
  [br:blue](-nf), [br:blue](--no-formatting)    Only output the libraries-list without extra info
  [br:blue](-j), [br:blue](--json)              Output as JSON format

[b](Examples:)
  [br:green](modules)                    [dim](# [i](List all imported modules))
  [br:green](modules) [br:blue](--external)         [dim](# [i](List only external/third-party modules))
  [br:green](modules) [br:blue](-d "./src")         [dim](# [i](Scan specific directory))
  [br:green](modules) [br:blue](-d "./src" -r)      [dim](# [i](Scan directory recursively))
  [br:green](modules) [br:blue](--no-formatting)    [dim](# [i](Output only the module names without extra info))
  [br:green](modules) [br:blue](--json)             [dim](# [i](Output as JSON format))
"""
    FormatCodes.print(help_text)


def extract_imports(file_path: str) -> set[str]:
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


def get_all_modules(directory: str, recursive: bool = False, external_only: bool = False) -> dict[str, list[str]]:
    """Get all modules used across Python files, grouped by module name."""
    module_usage: dict[str, list[str]] = {}

    if not os.path.isdir(directory):
        raise ValueError(f"Directory not found: {directory}")

    def scan_directory(dir_path: str, base_path: Optional[str] = None):
        """Scan a directory for Python files and extract imports."""
        if base_path is None:
            base_path = dir_path
        try:
            for entry in os.listdir(dir_path):
                full_path = os.path.join(dir_path, entry)
                if os.path.isfile(full_path) and os.path.splitext(entry)[1] in (".py", ".pyw"):
                    for module in extract_imports(full_path):
                        if external_only and module in STDLIB_MODULES:
                            continue
                        if module not in module_usage:
                            module_usage[module] = []
                        module_usage[module].append(os.path.splitext(os.path.relpath(full_path, base_path))[0])
                elif recursive and os.path.isdir(full_path):
                    scan_directory(full_path, base_path)
        except PermissionError:
            pass  # SKIP DIRECTORIES WE CAN'T ACCESS

    scan_directory(directory)
    return module_usage


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    directory = os.path.abspath(os.path.expanduser(ARGS.directory.value)) if ARGS.directory.value else Path.script_dir

    modules = get_all_modules(
        directory=directory,
        recursive=ARGS.recursive.exists,
        external_only=ARGS.external.exists,
    )

    if not modules:
        if ARGS.external.exists:
            FormatCodes.print("\n[i|dim](No external modules found)\n")
        else:
            FormatCodes.print("\n[i|dim](No modules found)\n")
        return

    if ARGS.as_json.exists:
        if ARGS.no_formatting.exists:
            json_data = sorted(modules.keys())
        else:
            json_data = {module: sorted(files) for module, files in sorted(modules.items())}
        FormatCodes.print(f"\n{Data.to_str(
            json_data,
            indent=2,
            as_json=True,
            _syntax_highlighting=True,
        )}\n")

    else:
        title = "EXTERNAL MODULES" if ARGS.external.exists else "ALL MODULES"
        output = f"\n[b|in]( {title} )\n"

        if ARGS.no_formatting.exists:
            output += f"\n[b|br:green]{'\n'.join(sorted(modules.keys()))}[_]"
        else:
            num_width = len(str(len(modules)))
            for i, (module, files) in enumerate(sorted(modules.items()), 1):
                usage_count = len(files)
                output += f"\n [i|dim|br:green]({i:>{num_width}})  [b|br:green]({module})"
                output += f" [dim](used in {usage_count} file{'s' if usage_count != 1 else ''})"

                if usage_count <= 5:
                    output += f" [br:cyan]({', '.join(sorted(files))})"
                else:
                    output += f" [br:cyan]({', '.join(sorted(files)[:3])}, [dim](+{usage_count - 3} more))"

        output += "\n"
        FormatCodes.print(output)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
