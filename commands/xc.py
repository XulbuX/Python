#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Execute a command and automatically copy the full output
including metadata to the clipboard, after execution."""
from pathlib import Path
from typing import Optional, Any, IO, cast
from xulbux import StyledText, Console, System, S
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
    StyledText("", S.RED(S.BOLD("[ERROR] "), "'pyperclip' module failed to initialize:"), S.BR.RED(f"  {fmt_error}"), "").print()
    sys.exit(1)


# fmt: off
def print_help():
    title = ["  Execute & Copy", " — Run a command and copy its output to clipboard  "]
    StyledText(
        "",
        ("▄" * len("".join(title))),
        (S.INVERSE | S.BG.BLACK)(S.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        (S.BOLD | S.BR.YELLOW)(
            "⚠ Commands that use dynamic progress bars and such\n",
            "  may not render correctly using this tool.\n",
            "  Interactive STDIN is currently not supported.",
        ),
        "",
        (S.BOLD("Usage: "), S.BR.GREEN("xc "), S.BR.BLUE("[options] "), S.BR.CYAN("<command> [args...]")),
        "",
        S.BOLD("Arguments:"),
        ("  ", S.BR.CYAN("command"), "              Command to execute with its arguments"),
        "",
        S.BOLD("Options:"),
        ("  ", S.BR.BLUE("-nc"), ", ", S.BR.BLUE("--no-command"), "    Do not include the ran command in clipboard"),
        ("  ", S.BR.BLUE("-nm"), ", ", S.BR.BLUE("--no-meta"), "       Do not include metadata in clipboard ", S.DIM("(exit code, duration, date)")),
        ("  ", S.BR.BLUE("-o"), ", ", S.BR.BLUE("--only"), "           Only copy the command output without command or metadata"),
        ("  ", S.BR.BLUE("-a"), ", ", S.BR.BLUE("--ansi"), "           Keep the ANSI codes in the copied output ", S.DIM("(default: ANSI removed)")),
        "",
        S.BOLD("Controls:"),
        ("  ", S.BR.RED("Ctrl(⌘)", S.DIM("+"), "C"), "            Cancel the command and copy the output captured so far"),
        "",
        S.BOLD("Examples:"),
        ("  ", S.BR.GREEN("xc "), S.BR.CYAN("pip show xulbux"), "         ", S.DIM("# ", S.ITALIC("Run and copy Python lib xulbux info"))),
        ("  ", S.BR.GREEN("xc "), S.BR.BLUE("--no-meta "), S.BR.CYAN("git status"), "    ", S.DIM("# ", S.ITALIC("Run and copy git status without metadata"))),
        ("  ", S.BR.GREEN("xc "), S.BR.BLUE("--no-command "), S.BR.CYAN("tree"), "       ", S.DIM("# ", S.ITALIC("Generate an copy a tree listing without the command"))),
        ("  ", S.BR.GREEN("xc "), S.BR.BLUE("--only "), S.BR.CYAN("ls -la"), "           ", S.DIM("# ", S.ITALIC("Run and copy ls -la output only"))),
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

    StyledText("", S.MAGENTA("━━━ Capturing: ", S.BOLD(command_str_display), " ━━━"), "").print()

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
        StyledText("", S.BR.YELLOW("━━━ Command cancelled by user ━━━", S.DIM(" (Ctrl(⌘)+C)"))).print()
        add_nl_before_end = False
        exit_code = 130  # SIGINT

    except FileNotFoundError:
        error_msg = StyledText(S.RED(S.BOLD("[ERROR] "), "Command not found:"), S.BR.RED(f"  {command_args[0]}"), "")
        captured_output.append(error_msg.raw)
        error_msg.print()
        exit_code = 127  # COMMAND NOT FOUND

    except Exception as exc:
        fmt_error = "\n  ".join(str(exc).splitlines())
        error_msg = StyledText(S.RED(S.BOLD("[ERROR] "), "Command execution failed:"), S.BR.RED(f"\n  {fmt_error}"), "")
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
    clipboard_parts.append(str_output if keep_ansi else StyledText.remove_ansi(str_output))

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
        StyledText("", S.BR.RED(S.BOLD("[ERROR] "), "Failed to copy to clipboard:"), f"  {fmt_error}", "").print()
        sys.exit(1)

    lines_count = len(captured_output)
    status_f = S.BR.GREEN if exit_code == 0 else S.BR.RED

    StyledText((
        ("\n" if add_nl_before_end else ""),
        status_f("━━━ Output copied to clipboard ━━━ "),
        S.DIM(
            S.BOLD(str(lines_count)), S.DIM, f" line{'s' if lines_count != 1 else ''}, ",
            S.BOLD(duration_str), S.DIM, ", exit ", S.BOLD(str(exit_code))
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
