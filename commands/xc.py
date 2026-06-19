#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Execute a command and automatically copy the full output
including metadata to the clipboard, after execution."""
from pathlib import Path
from typing import Optional, Any, IO, cast
from xulbux.format_codes import FC, F
from xulbux import Console, System
import subprocess
import platform
import shutil
import shlex
import time
import sys

try:
    import pyperclip
except Exception as exc:
    fmt_error = "\n  ".join(str(exc).splitlines())
    FC("", F.RED(F.BOLD("[ERROR] "), "'pyperclip' module failed to initialize:"), F.BR.RED(f"  {fmt_error}"), "").print()
    sys.exit(1)


# fmt: off
def print_help():
    title = ["  Execute & Copy", " — Run a command and copy its output to clipboard  "]
    FC(
        "",
        ("▄" * len("".join(title))),
        (F.INVERSE | F.BG.BLACK)(F.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        (F.BOLD | F.BR.YELLOW)(
            "⚠ Commands that use dynamic progress bars and such\n",
            "  may not render correctly using this tool.\n",
            "  Interactive STDIN is currently not supported.",
        ),
        "",
        (F.BOLD("Usage: "), F.BR.GREEN("xc "), F.BR.BLUE("[options] "), F.BR.CYAN("<command> [args...]")),
        "",
        F.BOLD("Arguments:"),
        ("  ", F.BR.CYAN("command"), "              Command to execute with its arguments"),
        "",
        F.BOLD("Options:"),
        ("  ", F.BR.BLUE("-nc"), ", ", F.BR.BLUE("--no-command"), "    Do not include the ran command in clipboard"),
        ("  ", F.BR.BLUE("-nm"), ", ", F.BR.BLUE("--no-meta"), "       Do not include metadata in clipboard ", F.DIM("(exit code, duration, date)")),
        ("  ", F.BR.BLUE("-o"), ", ", F.BR.BLUE("--only"), "           Only copy the command output without command or metadata"),
        ("  ", F.BR.BLUE("-a"), ", ", F.BR.BLUE("--ansi"), "           Keep the ANSI codes in the copied output ", F.DIM("(default: ANSI removed)")),
        "",
        F.BOLD("Controls:"),
        ("  ", F.BR.RED("Ctrl(⌘)", F.DIM("+"), "C"), "            Cancel the command and copy the output captured so far"),
        "",
        F.BOLD("Examples:"),
        ("  ", F.BR.GREEN("xc "), F.BR.CYAN("pip show xulbux"), "         ", F.DIM("# ", F.ITALIC("Run and copy Python lib xulbux info"))),
        ("  ", F.BR.GREEN("xc "), F.BR.BLUE("--no-meta "), F.BR.CYAN("git status"), "    ", F.DIM("# ", F.ITALIC("Run and copy git status without metadata"))),
        ("  ", F.BR.GREEN("xc "), F.BR.BLUE("--no-command "), F.BR.CYAN("tree"), "       ", F.DIM("# ", F.ITALIC("Generate an copy a tree listing without the command"))),
        ("  ", F.BR.GREEN("xc "), F.BR.BLUE("--only "), F.BR.CYAN("ls -la"), "           ", F.DIM("# ", F.ITALIC("Run and copy ls -la output only"))),
        "",
    ).print()
# fmt: on


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
        escaped_args: list[str] = []
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

    FC("", F.MAGENTA("━━━ Capturing: ", F.BOLD(command_str_display), " ━━━"), "").print()

    process: Optional[subprocess.Popen[str]] = None
    captured_output: list[str] = []
    add_nl_before_end = True
    start_time = time.time()
    exit_code = 0

    #################################### RUN THE COMMAND ####################################
    try:
        # bufsize=1 AND text=True ENABLES LINE-BY-LINE TEXT STREAMING
        general_popen_kwargs: dict[str, Any] = {
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
        FC("", F.BR.YELLOW("━━━ Command cancelled by user ━━━", F.DIM(" (Ctrl(⌘)+C)"))).print()
        add_nl_before_end = False
        exit_code = 130  # SIGINT

    except FileNotFoundError:
        error_msg = FC(F.RED(F.BOLD("[ERROR] "), "Command not found:"), F.BR.RED(f"  {command_args[0]}"), "")
        captured_output.append(error_msg.raw)
        error_msg.print()
        exit_code = 127  # COMMAND NOT FOUND

    except Exception as exc:
        fmt_error = "\n  ".join(str(exc).splitlines())
        error_msg = FC(F.RED(F.BOLD("[ERROR] "), "Command execution failed:"), F.BR.RED(f"\n  {fmt_error}"), "")
        captured_output.append(error_msg.raw)
        error_msg.print()
        exit_code = 1  # GENERAL ERROR

    finally:
        terminate_process(process)

    duration = time.time() - start_time
    duration_str = f"{int(duration * 1000 + 0.5)}ms" if duration < 1 else f"{int(duration + 0.5)}s"

    ################################ BUILD CLIPBOARD CONTENT ################################
    clipboard_parts: list[str] = []

    if not exclude_cmd:
        clipboard_parts.append(
            ("Administrator" if System.is_elevated else Console.user) +
            f" on {platform.node()} ({platform.system()})"
            f" at {"~" if (cwd := Path.cwd()).expanduser() == Path.home() else cwd}\n"
            f"$ {command_str_display}\n\n"
        )

    str_output = "".join(captured_output)
    clipboard_parts.append(str_output if keep_ansi else FC.remove_ansi(str_output))

    if not exclude_meta:
        clipboard_parts.append(
            f"\n{'─' * Console.width}\n"
            f"[{time.ctime(start_time)}]\n"
            f"Took : {duration_str}\n"
            f"Exit : {exit_code}\n"
        )

    clipboard_content = "".join(clipboard_parts)

    ############################### COPY TO CLIPBOARD & EXIT ################################
    try:
        pyperclip.copy(clipboard_content)
    except Exception as exc:
        fmt_error = "\n  ".join(str(exc).splitlines())
        FC("", F.BR.RED(F.BOLD("[ERROR] "), "Failed to copy to clipboard:"), f"  {fmt_error}", "").print()
        sys.exit(1)

    lines_count = len(captured_output)
    status_f = F.BR.GREEN if exit_code == 0 else F.BR.RED

    FC((
        ("\n" if add_nl_before_end else ""),
        status_f("━━━ Output copied to clipboard ━━━ "),
        F.DIM(
            F.BOLD(str(lines_count)), F.DIM, f" line{'s' if lines_count != 1 else ''}, ",
            F.BOLD(duration_str), F.DIM, ", exit ", F.BOLD(str(exit_code))
        )
    ), "").print()

    # EXIT WITH THE SAME CODE AS THE COMMAND
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
