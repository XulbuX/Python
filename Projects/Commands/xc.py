#!/usr/bin/env python3
"""Execute a command and automatically copy the full output
including metadata to the clipboard, after execution."""
from pathlib import Path
from typing import IO, cast
from xulbux import FormatCodes, Console, System
import subprocess
import platform
import shlex
import time
import sys

try:
    import pyperclip
except ImportError:
    FormatCodes.print("[br:red](Error: 'pyperclip' module not found.)")
    FormatCodes.print("[yellow](Please run: [b](pip install pyperclip))")
    sys.exit(1)


def print_help():
    help_text = """
[b|in|bg:black]( Execute & Copy - Run a command and copy its output to clipboard )

[b](Usage:) [br:green](xc) [br:blue]([options]) [br:cyan](<command> [args...])

[b](Arguments:)
  [br:cyan](command)              Command to execute with its arguments

[b](Options:)
  [br:blue](-nc), [br:blue](--no-command)    Do not include the ran command in clipboard
  [br:blue](-nm), [br:blue](--no-meta)       Do not include metadata in clipboard [dim]((exit code, duration, date))

[b](Examples:)
  [br:green](xc) [br:cyan](python --version)              [dim](# [i](Run and copy Python version))
  [br:green](xc) [br:cyan](git status)                    [dim](# [i](Run and copy git status))
  [br:green](xc) [br:cyan](npm test)                      [dim](# [i](Run tests and copy output))
  [br:green](xc) [br:cyan](dir /s)                        [dim](# [i](Directory listing with subdirs))
"""
    FormatCodes.print(help_text)


def extract_flag(args, flag_values):
    """Remove flags from args and return `(flag_present, filtered_args)`"""
    filtered = [arg for arg in args if arg.lower().strip() not in flag_values]
    return len(filtered) < len(args), filtered


def main():
    if len(sys.argv) < 2 or extract_flag(sys.argv[1:], {"-h", "--help"})[0]:
        print_help()
        sys.exit(0)

    command_args = sys.argv[1:]
    # [help: {-h, --help}, no_command: {-nc, --no-command}, no_meta: {-nm, --no-meta}, command: after]
    exclude_cmd, command_args = extract_flag(command_args, {"-nc", "--no-command"})
    exclude_meta, command_args = extract_flag(command_args, {"-nm", "--no-meta"})
    command_str = shlex.join(command_args)

    FormatCodes.print(f"\n[br:cyan](━━━ Capturing: [b]({command_str}) ━━━)\n")

    captured_output = []
    start_time = time.time()
    exit_code = 0

    try:
        #################################### RUN THE COMMAND ####################################
        # bufsize=1 AND text=True ENABLES LINE-BY-LINE TEXT STREAMING
        process = subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,  # ALLOWS US TO READ IT
            stderr=subprocess.STDOUT,  # MERGES ERRORS INTO THE MAIN OUTPUT STREAM (CHRONOLOGICAL ORDER)
            text=True,
            bufsize=1,
        )

        ######################### STREAM OUTPUT TO CONSOLE + CAPTURE IT #########################
        while True:
            if (
                not (line := cast(IO[str], process.stdout).readline()) \
                and process.poll() is not None
            ):
                break
            if line:
                sys.stdout.write(line)
                captured_output.append(line)

        # WAIT FOR PROCESS TO FULLY CLOSE TO GET RETURN CODE
        exit_code = process.wait()

    except KeyboardInterrupt:
        FormatCodes.print("\n[br:yellow](━━━ Command cancelled by user [dim]((Ctrl+C)) ━━━)\n")
        exit_code = 130  # SIGINT
    except FileNotFoundError:
        error_msg = FormatCodes.to_ansi(f"[red]([b]([ERROR]) Command not found:)\n  [br:red]({command_args[0]})\n")
        captured_output.append(FormatCodes.remove_ansi(error_msg))
        sys.stdout.write(error_msg)
        sys.stdout.flush()
        exit_code = 127  # COMMAND NOT FOUND
    except Exception as e:
        fmt_error = "\n  ".join(str(e).splitlines())
        error_msg = FormatCodes.to_ansi(f"[red]([b]([ERROR]) Command execution failed:)[br:red]\n  {fmt_error}\n[_c]")
        captured_output.append(FormatCodes.remove_ansi(error_msg))
        sys.stdout.write(error_msg)
        sys.stdout.flush()
        exit_code = 1  # GENERAL ERROR

    end_time = time.time()
    duration = end_time - start_time

    ################################ BUILD CLIPBOARD CONTENT ################################
    clipboard_parts = []

    if not exclude_cmd:
        clipboard_parts.append(
            ("Administrator" if System.is_elevated else Console.user) +
            f" on {platform.node()} ({platform.system()})"
            f" at {"~" if (cwd := Path.cwd()).expanduser() == Path.home() else cwd}\n"
            f"$ {command_str}\n\n"
        )

    clipboard_parts.append("".join(captured_output))

    if not exclude_meta:
        clipboard_parts.append(
            f"\n{'─' * 60}\n"
            f"[{time.ctime(start_time)}]\n"
            f"Took : {duration * 1000:.2f}ms\n"
            f"Exit : {exit_code}\n"
        )

    clipboard_content = "".join(clipboard_parts)

    try:
        pyperclip.copy(clipboard_content)
    except Exception as e:
        fmt_error = "\n  ".join(str(e).splitlines())
        FormatCodes.print(f"\n[br:red]([b]([ERROR]) Failed to copy to clipboard:)[br:red]\n  {fmt_error}\n[_c]")
        sys.exit(1)

    lines_count = len(captured_output)
    FormatCodes.print(
        f"\n[{'br:green' if exit_code == 0 else 'br:red'}](━━━ Output copied to clipboard "
        f"[dim]/([b]({lines_count})[dim] line{'s' if lines_count != 1 else ''}, "
        f"[b]({duration * 1000:.2f}ms)[dim], exit code [b]({exit_code})[dim])[_dim] ━━━)\n"
    )

    # EXIT WITH THE SAME CODE AS THE COMMAND
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
