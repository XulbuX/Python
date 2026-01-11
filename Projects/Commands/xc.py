#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Execute a command and automatically copy the full output
including metadata to the clipboard, after execution."""
from pathlib import Path
from typing import Optional, IO, cast
from xulbux import FormatCodes, Console, System
import subprocess
import platform
import shutil
import shlex
import time
import sys

try:
    import pyperclip
except Exception as e:
    fmt_error = "\n  ".join(str(e).splitlines())
    FormatCodes.print(f"\n[red]([b]([ERROR]) 'pyperclip' module failed to initialize:)\n  [br:red]{fmt_error}[_c]\n")
    sys.exit(1)


def print_help():
    help_text = """
[b|in|bg:black]( Execute & Copy - Run a command and copy its output to clipboard )

[b|br:yellow]⚠ Commands that use dynamic progress bars and such
  may not render correctly using this tool.
  Interactive STDIN is currently not supported.[_b|_c]

[b](Usage:) [br:green](xc) [br:blue]([options]) [br:cyan](<command> [args...])

[b](Arguments:)
  [br:cyan](command)              Command to execute with its arguments

[b](Options:)
  [br:blue](-nc), [br:blue](--no-command)    Do not include the ran command in clipboard
  [br:blue](-nm), [br:blue](--no-meta)       Do not include metadata in clipboard [dim]((exit code, duration, date))
  [br:blue](-o), [br:blue](--only)           Only copy the command output without command or metadata
  [br:blue](-a), [br:blue](--ansi)           Keep the ANSI codes in the copied output [dim]((default: ANSI removed))

[b](Examples:)
  [br:green](xc) [br:cyan](pip show xulbux)         [dim](# [i](Run and copy Python lib xulbux info))
  [br:green](xc) [br:blue](--no-meta) [br:cyan](git status)    [dim](# [i](Run and copy git status without metadata))
  [br:green](xc) [br:blue](--no-command) [br:cyan](tree)       [dim](# [i](Generate an copy a tree listing without the command))
  [br:green](xc) [br:blue](--only) [br:cyan](ls -la)           [dim](# [i](Run and copy ls -la output only))
"""
    FormatCodes.print(help_text)


def parse_flags_and_command(args: list[str]) -> tuple[bool, bool, bool, bool, list[str]]:
    """Parse `xc` flags at the start, then extract the command."""
    show_help, exclude_cmd, exclude_meta, keep_ansi = False, False, False, False

    i = 0
    while i < len(args):
        arg = args[i].lower().strip()

        # CHECK FOR XC FLAGS
        if arg in {"-h", "--help"}:
            show_help = True
            i += 1
        elif arg in {"-nc", "--no-command"}:
            exclude_cmd = True
            i += 1
        elif arg in {"-nm", "--no-meta"}:
            exclude_meta = True
            i += 1
        elif arg in {"-o", "--only"}:
            exclude_cmd = True
            exclude_meta = True
            i += 1
        elif arg in {"-a", "--ansi"}:
            keep_ansi = True
            i += 1
        else:
            # NOT AN XC FLAG, THIS IS THE START OF THE COMMAND
            break

    return show_help, exclude_cmd, exclude_meta, keep_ansi, args[i:]


def terminate_process(process: Optional[subprocess.Popen[str]]) -> None:
    """Safely terminate a `subprocess.Popen` process."""
    if process is None:
        return
    try:
        process.terminate()
        process.wait(timeout=2)
    except:
        try:
            process.kill()
        except:
            pass


def main() -> None:
    ################################### PARSE ARGS & INIT ###################################
    show_help, exclude_cmd, exclude_meta, keep_ansi, command_args = parse_flags_and_command(
        sys.argv[1:]  # [no_command: {-nc, --no-command}, no_meta: {-nm, --no-meta}, only: {-o, --only}, help: {-h, --help}, command: after]
    )

    if show_help or not command_args:
        print_help()
        sys.exit(0)

    # PROPERLY CONSTRUCT COMMAND STRING FOR THE SHELL
    if platform.system() == "Windows":
        # ON WINDOWS, USE POWERSHELL-STYLE COMMAND WITH -Command FLAG
        escaped_args = []
        for arg in command_args:
            if " " in arg or '"' in arg or "'" in arg:
                escaped_arg = "'" + arg.replace("'", "''") + "'"
            else:
                escaped_arg = arg
            escaped_args.append(escaped_arg)
        command_for_shell = " ".join(escaped_args)
        command_str_display = subprocess.list2cmdline(command_args)
    else:
        command_for_shell = shlex.join(command_args)
        command_str_display = command_for_shell

    FormatCodes.print(f"\n[br:cyan](━━━ Capturing: [b]({command_str_display}) ━━━)\n")

    process: Optional[subprocess.Popen[str]] = None
    add_nl_before_end = True
    captured_output = []
    start_time = time.time()
    exit_code = 0

    #################################### RUN THE COMMAND ####################################
    try:
        # bufsize=1 AND text=True ENABLES LINE-BY-LINE TEXT STREAMING
        general_popen_kwargs = {
            "stdin": None,  # KEEP STDIN CONNECTED TO TERMINAL FOR INTERACTIVE COMMANDS
            "stdout": subprocess.PIPE,  # ALLOWS US TO READ IT
            "stderr": subprocess.STDOUT,  # MERGES ERRORS INTO THE MAIN OUTPUT STREAM (CHRONOLOGICAL ORDER)
            "shell": True,  # USE SHELL TO INTERPRET FOR ACCESS TO ALIASES, PATH, …
            "text": True,
            "bufsize": 1,
            "errors": "replace",  # REPLACE INVALID CHARS INSTEAD OF FAILING
        }

        if platform.system() == "Windows":
            process = subprocess.Popen(
                [
                    "pwsh.exe" if shutil.which("pwsh") else "powershell.exe",
                    "-NoProfile",
                    "-Command",
                    f"$env:PYTHONIOENCODING='utf-8'; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; {command_for_shell}",
                ],
                encoding="utf-8",
                **general_popen_kwargs,
            )
        else:
            process = subprocess.Popen(
                command_for_shell,
                encoding=sys.stdout.encoding or "utf-8",
                **general_popen_kwargs,
            )

        # STREAM OUTPUT TO CONSOLE + CAPTURE IT
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
        FormatCodes.print("\n[br:yellow]━━━ Command cancelled by user ━━━ [dim]((Ctrl+C))[_c]")
        add_nl_before_end = False
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

    finally:
        terminate_process(process)

    duration = time.time() - start_time
    duration_str = f"{int(duration * 1000 + 0.5)}ms" if duration < 1 else f"{int(duration + 0.5)}s"

    ################################ BUILD CLIPBOARD CONTENT ################################
    clipboard_parts = []

    if not exclude_cmd:
        clipboard_parts.append(
            ("Administrator" if System.is_elevated else Console.user) +
            f" on {platform.node()} ({platform.system()})"
            f" at {"~" if (cwd := Path.cwd()).expanduser() == Path.home() else cwd}\n"
            f"$ {command_str_display}\n\n"
        )

    str_output = "".join(captured_output)
    clipboard_parts.append(str_output if keep_ansi else FormatCodes.remove_ansi(str_output))

    if not exclude_meta:
        clipboard_parts.append(
            f"\n{'─' * Console.w}\n"
            f"[{time.ctime(start_time)}]\n"
            f"Took : {duration_str}\n"
            f"Exit : {exit_code}\n"
        )

    clipboard_content = "".join(clipboard_parts)

    ############################### COPY TO CLIPBOARD & EXIT ################################
    try:
        pyperclip.copy(clipboard_content)
    except Exception as e:
        fmt_error = "\n  ".join(str(e).splitlines())
        FormatCodes.print(f"\n[br:red]([b]([ERROR]) Failed to copy to clipboard:)[br:red]\n  {fmt_error}\n[_c]")
        sys.exit(1)

    lines_count = len(captured_output)
    FormatCodes.print(
        ("\n" if add_nl_before_end else "") +
        f"[{'br:green' if exit_code == 0 else 'br:red'}](━━━ Output copied to clipboard ━━━ "
        f"[dim]/([b]({lines_count})[dim] line{'s' if lines_count != 1 else ''}, "
        f"[b]({duration_str})[dim], exit [b]({exit_code})[dim])[_dim])\n"
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
