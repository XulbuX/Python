#!/usr/bin/env python3
# x-cmds:file[update]

"""Force delete files or directories, even if they are locked by processes."""

import contextlib
import os
import platform
import shutil
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
import psutil
import xulbux as xx
from xulbux import ArgumentParser, FormatCodes, S

# ************************* CRITICAL PROCESSES THAT SHOULD NEVER BE TERMINATED *************************

PROTECTED_PROCESSES_WINDOWS = {
    "csrss.exe",
    "dwm.exe",
    "lsass.exe",
    "services.exe",
    "smss.exe",
    "svchost.exe",
    "system",
    "wininit.exe",
    "winlogon.exe",
}
PROTECTED_PROCESSES_MACOS = {
    "configd",
    "coreaudiod",
    "Dock",
    "Finder",
    "kernel_task",
    "loginwindow",
    "SystemUIServer",
    "UserEventAgent",
    "WindowServer",
}
PROTECTED_PROCESSES_UNIX = {
    "bash",
    "cron",
    "dbus-daemon",
    "fish",
    "init",
    "kernel",
    "kthreadd",
    "launchd",
    "login",
    "migration",
    "NetworkManager",
    "rcu_sched",
    "rsyslogd",
    "sh",
    "sshd",
    "systemd-journald",
    "systemd-udevd",
    "systemd",
    "watchdog",
    "zsh",
}


def get_protected_processes() -> set[str]:
    """Get the appropriate protected processes list for the current OS."""

    if (system := platform.system()) == "Windows":
        return PROTECTED_PROCESSES_WINDOWS
    elif system == "Darwin":  # macOS
        return PROTECTED_PROCESSES_UNIX | PROTECTED_PROCESSES_MACOS
    else:  # Unix-like
        return PROTECTED_PROCESSES_UNIX


def take_ownership_windows(path: Path) -> bool:
    """Take ownership of a file/directory on Windows."""

    FormatCodes.print(f"[b](Taking ownership of [br:cyan]({path.name})...)")

    try:
        # Take ownership using `takeown`:
        result = subprocess.run(
            ["takeown", "/F", str(path)] + (["/R", "/D", "Y"] if path.is_dir() else []),
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=(
                subprocess.CREATE_NO_WINDOW  # type:ignore[type-unknown]
                if platform.system() == "Windows"
                else 0
            ),
        )

        if result.returncode != 0:
            FormatCodes.print(f"[yellow][b](⚠ takeown failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        # Grant full control using `icacls`:
        result = subprocess.run(
            ["icacls", str(path), "/grant", f"{os.getlogin()}:F", "/C", "/Q"] + (["/T"] if path.is_dir() else []),
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type:ignore[type-unknown]
        )

        if result.returncode != 0:
            FormatCodes.print(f"[yellow][b](⚠ icacls failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print("[green](✓ Successfully took ownership)")
        return True

    except subprocess.TimeoutExpired:
        FormatCodes.print("[yellow][b](⚠ takeown/icacls timed out, some ownership may have been granted)[_]")
        return True
    except Exception as exc:
        FormatCodes.print(f"[red][b](✗ Error taking ownership:)\n  {str(exc).replace('\n', '\n  ')}[_]")
        return False


def remove_attributes_windows(path: Path) -> bool:
    """Remove file attributes on Windows (readonly, system, hidden)."""

    FormatCodes.print(f"[b](Removing attributes from [br:cyan]({path.name})...)")

    try:
        result = subprocess.run(
            ["attrib", "-R", "-S", "-H", str(path)] + (["/S", "/D"] if path.is_dir() else []),
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type:ignore[type-unknown]
        )

        if result.returncode != 0:
            FormatCodes.print(f"[yellow][b](⚠ attrib failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print("[green](✓ Successfully removed attributes)")
        return True

    except subprocess.TimeoutExpired:
        FormatCodes.print("[yellow][b](⚠ attrib timed out, some attributes may have been cleared)[_]")
        return True
    except Exception as exc:
        FormatCodes.print(f"[red][b](✗ Error removing attributes:)\n  {str(exc).replace('\n', '\n  ')}[_]")
        return False


def change_permissions_unix(path: Path) -> bool:
    """Change permissions on Unix systems."""

    FormatCodes.print(f"[b](Changing permissions for [br:cyan]({path.name})...)")

    try:
        # Try to make everything writable:
        result = subprocess.run(
            ["chmod", "-R", "777", str(path)] if path.is_dir() else ["chmod", "777", str(path)], capture_output=True, text=True
        )

        if result.returncode != 0:
            FormatCodes.print(f"[yellow][b](⚠ chmod failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print("[green](✓ Successfully changed permissions)")
        return True

    except Exception as exc:
        FormatCodes.print(f"[red][b](✗ Error changing permissions:)\n  {str(exc).replace('\n', '\n  ')}[_]")
        return False


def unlock_file_macos(path: Path) -> bool:
    """Unlock files on macOS using `chflags`."""

    FormatCodes.print(f"[b](Unlocking [br:cyan]({path.name}) on macOS...)")

    try:
        # Remove all flags including user immutable and system immutable:
        result = subprocess.run(
            ["chflags", "-R", "nouchg,nouappnd,nosappnd,nosunlnk", str(path)]
            if path.is_dir()
            else ["chflags", "nouchg,nouappnd,nosappnd,nosunlnk", str(path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            FormatCodes.print(f"[yellow][b](⚠ chflags failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print("[green](✓ Successfully unlocked file)")
        return True

    except Exception as exc:
        FormatCodes.print(f"[red][b](✗ Error unlocking file:)\n  {str(exc).replace('\n', '\n  ')}[_]")
        return False


def try_advanced_deletion_techniques(path: Path) -> bool:
    """Try advanced OS-specific deletion techniques."""

    system = platform.system()
    success = False

    if system == "Windows":
        if remove_attributes_windows(path):
            success = True
        if take_ownership_windows(path):
            success = True

    elif system == "Darwin":  # macOS
        if unlock_file_macos(path):
            success = True
        if change_permissions_unix(path):
            success = True

    else:  # Unix-like
        if change_permissions_unix(path):
            success = True

    return success


def find_processes_using_path(path: Path) -> list[psutil.Process]:
    """Find all processes that have handles to the given path."""

    processes: list[psutil.Process] = []
    system = platform.system()
    path = path.resolve()

    for proc in psutil.process_iter(["pid", "name", "open_files", "cwd", "exe"]):
        try:
            # Check open files:
            if proc.info["open_files"]:
                for file in proc.info["open_files"]:
                    file_path = file.path if hasattr(file, "path") else str(file)
                    if (p := str(path).lower()) in (f := file_path.lower()) or f in p:
                        processes.append(proc)
                        break

            # On Unix systems, also check current working directory:
            if system != "Windows":
                with suppress(psutil.AccessDenied, psutil.NoSuchProcess):
                    if ((p := str(path).lower()) in (c := proc.cwd().lower()) or c in p) and proc not in processes:
                        processes.append(proc)

        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            continue

    return processes


def is_protected_process(proc: psutil.Process) -> bool:
    """Check if a process is in the protected list."""

    try:
        name = proc.name().lower()
        protected_set = get_protected_processes()

        # Check exact name match:
        if name in protected_set:
            return True

        # For Unix systems, also check without extension and base name:
        if platform.system() != "Windows":
            base_name = Path(name).name
            if base_name in protected_set:
                return True

        # Check if it's PID 1 (init/systemd/launchd); never terminate this:
        if proc.pid == 1:
            return True

        # On Unix, protect processes owned by root running critical services:
        if platform.system() != "Windows":
            with suppress(psutil.AccessDenied, psutil.NoSuchProcess):
                if proc.username() == "root" and proc.pid < 1000:
                    return True

        return False
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return True  # Err on the side of caution.


def terminate_process(proc: psutil.Process) -> bool:
    """Attempt to terminate a process."""

    try:
        FormatCodes.print(f"  Terminating [magenta]({proc.name().strip()}) [dim]((PID [magenta]({proc.pid})))...")
        proc.terminate()
        proc.wait(timeout=5)
        return True

    except psutil.TimeoutExpired:
        FormatCodes.print(
            f"  [b|yellow](⚠ Process didn't terminate gracefully, killing:)\n"
            f"    [magenta]({proc.name().strip()}) [dim|yellow]((PID [magenta]({proc.pid})[yellow]))"
        )
        try:
            proc.kill()
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return False

    except (psutil.AccessDenied, psutil.NoSuchProcess):
        FormatCodes.print(
            f"  [b|red](✗ Access denied or process no longer exists:)\n"
            f"    [magenta]({proc.name().strip()}) [dim]((PID [magenta]({proc.pid})))"
        )
        return False


def attempt_deletion(path: Path) -> bool:
    """Attempt to delete a path."""

    FormatCodes.print(f"[b]Deleting [br:cyan]({path.name})...[_b]")

    try:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
    except PermissionError:
        FormatCodes.print("[b|yellow](⚠ Permission denied!)")
    except OSError as exc:
        # On Unix systems, we might get different errors:
        if platform.system() != "Windows":
            FormatCodes.print(f"[yellow][b](⚠ Deletion blocked:)\n  {str(exc).replace('\n', '\n  ')}[_]")
        else:
            FormatCodes.print(f"[red][b](✗ Error during deletion:)\n  {str(exc).replace('\n', '\n  ')}[_]")
    except Exception as exc:
        FormatCodes.print(f"[red][b](✗ Error during deletion:)\n  {str(exc).replace('\n', '\n  ')}[_]")

    return not path.exists()


def force_delete(path: Path) -> bool:  # ruff:ignore[complex-structure]
    """Force delete a file or directory, terminating processes if needed."""

    print()

    # Try to delete without terminating processes:
    if attempt_deletion(path):
        FormatCodes.print(f"[b|green](✓ Successfully deleted:) [br:cyan|link:file:///{path.resolve()}]({path.name})\n")
        return True

    # First try advanced deletion techniques:
    FormatCodes.print("[yellow](  Trying advanced deletion techniques...)")

    if try_advanced_deletion_techniques(path):
        time.sleep(0.5)
        if attempt_deletion(path):
            FormatCodes.print(f"\n[b|green](✓ Successfully deleted:) [br:cyan|link:file:///{path.resolve()}]({path.name})\n")
            return True

    # Now try to find processes using the path:
    FormatCodes.print("[yellow](  Searching for processes using this path...)")
    processes = find_processes_using_path(path)

    if processes:
        FormatCodes.print(f"[b](Found [magenta]({(ln := len(processes))}) process{'' if ln == 1 else 'es'} using this path:)")
        for proc in processes:
            with contextlib.suppress(psutil.AccessDenied, psutil.NoSuchProcess):
                FormatCodes.print(f"  [magenta]({proc.name()}) [dim]((PID [magenta]({proc.pid})))")

        # Check for protected processes:
        protected = [p for p in processes if is_protected_process(p)]
        if protected:
            FormatCodes.print("\n[b|red](⯃ The following critical system processes are using this path:)")
            for proc in protected:
                with contextlib.suppress(psutil.AccessDenied, psutil.NoSuchProcess):
                    FormatCodes.print(f"  [magenta]({proc.name()}) [dim]((PID [magenta]({proc.pid})))")
            FormatCodes.print("  [red](These processes will [b](NOT) be terminated for system safety.)\n")
            return False

        # Terminate non-protected processes:
        FormatCodes.print("[b](Terminating processes...)")
        terminated: list[psutil.Process] = []
        for proc in processes:
            if terminate_process(proc):
                terminated.append(proc)

        if not terminated:
            FormatCodes.print("[red](Failed to terminate any processes.)\n")
        else:
            time.sleep(1)
            if attempt_deletion(path):
                FormatCodes.print(
                    f"\n[b|green](✓ Successfully deleted:) [br:cyan|link:file:///{path.resolve()}]({path.name})\n"
                )
                return True

    # Still failed; give up :(
    FormatCodes.print("\n[b|red]✗ Failed to delete even after trying all techniques :([_]\n")

    if not xx.system.is_elevated():
        if platform.system() == "Windows":
            FormatCodes.print("[dim|blue](ⓘ [i](Try running with Administrator privileges.))\n")
        else:
            FormatCodes.print("[dim|blue](ⓘ [i](Try running with sudo for elevated privileges.))\n")
    else:
        FormatCodes.print(
            "[dim|blue](ⓘ [i](The file/directory may be protected by the system or in use by a kernel-level process.))\n"
        )

    return False


def path_validator(path: str) -> str | None:
    """Validate the input path."""

    if not Path(path).exists():
        max_w = xx.console.get_width() - 23
        str_p = path if (length := len(path)) <= max_w else f"...{path[length - (max_w - 3) :]}"
        return f"Path [i]({str_p}) doesn't exist."


def main() -> None:
    FormatCodes.print(f"\n[b|bg:black]( {platform.system()} [in]( FORCE DELETE UTILITY ))")
    xx.console.log_box_bordered(
        "[yellow](This will terminate processes if needed.)",
        "[yellow](Critical system processes are protected.)",
        border_style="dim|yellow",
    )

    if not xx.system.is_elevated():
        if platform.system() == "Windows":
            FormatCodes.print("\n[yellow](⚠ Not running as Administrator. Some operations may fail.)")
        else:
            FormatCodes.print(
                "\n[yellow](⚠ Not running as root. Some operations may fail.)\n"
                "  [dim|yellow](Consider running:) [b|br:white](sudo) [white](python) [br:green](x-rm) [br:cyan](<path>)"
            )

    target_path_str = ARGS.path.val(default="") or ARGS.confirmed.val(default="")
    if not target_path_str:
        target_path_str = xx.console.input("\n[b](Path to file/directory to delete > )", validator=path_validator)

    if not (target_path := Path(target_path_str)).exists():
        xx.console.fail(f"Path [br:cyan]({target_path}) does not exist!", start="\n", end="\n\n")

    if not ARGS.confirmed.exists and not xx.console.confirm(
        f"\n[b](Are you sure you want to delete [br:cyan|bg:black]({target_path.name})?)", default_is_yes=False
    ):
        xx.console.exit("Deletion aborted.", start="\n", end="\n\n", exit_code=0)

    sys.exit(0 if force_delete(target_path) else 1)


if __name__ == "__main__":
    args = ArgumentParser(
        title="Force Remove",
        subtitle="Delete files/directories even if they are locked",
        examples=[
            ('{cmd} "/path/to/directory"', "Delete a directory"),
            ('{cmd} -y="/path/to/file.txt"', "Delete a file, skipping confirmation"),
        ],
    )

    args.add_arg("path", required=False, help="The path to the file/directory to delete")
    args.add_opt(
        {"-y", "--yes"},
        "confirmed",
        expects_value="PATH",
        help=("Skip confirmation prompt for ", S.BR.BLUE("PATH"), " deletion"),
    )

    global ARGS
    ARGS = args.parse()

    try:
        main()
    except KeyboardInterrupt:
        FormatCodes.print("[b|red](✗ Canceled by user.)\n")
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
