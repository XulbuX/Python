#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Force delete files or directories, even if they are locked by processes."""
from pathlib import Path
from typing import Optional
from xulbux import FormatCodes, Console, System
import subprocess
import platform
import shutil
import psutil
import time
import sys
import os

######################### CRITICAL PROCESSES THAT SHOULD NEVER BE TERMINATED #########################

PROTECTED_PROCESSES_WINDOWS = {
    "system", "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe", "dwm.exe", "explorer.exe",
    "svchost.exe"
}
PROTECTED_PROCESSES_MACOS = {
    "WindowServer", "Finder", "Dock", "SystemUIServer", "loginwindow", "kernel_task", "UserEventAgent", "coreaudiod", "configd"
}
PROTECTED_PROCESSES_UNIX = {
    "systemd", "init", "kthreadd", "rcu_sched", "migration", "watchdog", "systemd-journald", "systemd-udevd", "dbus-daemon",
    "NetworkManager", "sshd", "cron", "rsyslogd", "login", "bash", "sh", "zsh", "fish", "kernel", "launchd"
}

ARGS = Console.get_args({
    "rm_path": "before",
    "confirm": {"-c", "--confirm"},
    "help": {"-h", "--help"},
})


def print_help():
    help_text = """
[b|in|bg:black]( Force Remove - Delete files/directories even if locked by processes )

[b](Usage:) [br:green](x-rm) [br:cyan](<path>) [br:blue]([options])

[b](Arguments:)
  [br:cyan](path)             The path to the file or directory to delete

[b](Options:)
  [br:blue](-c), [br:blue](--confirm)    Skip confirmation prompt before deletion

[b](Examples:)
  [br:green](x-rm) [br:cyan]("/path/to/directory")             [dim](# [i](Delete a directory))
  [br:green](x-rm) [br:cyan]("/path/to/file.txt") [br:blue](--confirm)    [dim](# [i](Delete a file, skipping confirmation))
"""
    FormatCodes.print(help_text)


def get_protected_processes() -> set[str]:
    """Get the appropriate protected processes list for the current OS."""
    if (system := platform.system()) == "Windows":
        return PROTECTED_PROCESSES_WINDOWS
    elif system == "Darwin":  # macOS
        return PROTECTED_PROCESSES_UNIX | PROTECTED_PROCESSES_MACOS
    else:  # LINUX OR UNIX-LIKE
        return PROTECTED_PROCESSES_UNIX


def take_ownership_windows(path: Path) -> bool:
    """Take ownership of a file/directory on Windows."""
    FormatCodes.print(f"[b](Taking ownership of [br:cyan]({path})...)")

    try:
        # TAKE OWNERSHIP USING 'takeown'
        result = subprocess.run(
            ["takeown", "/F", str(path)] + (["/R", "/D", "Y"] if path.is_dir() else []),
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )

        if result.returncode != 0:
            FormatCodes.print(f"[br:yellow][b](⚠ takeown failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        # GRANT FULL CONTROL USING 'icacls'
        result = subprocess.run(
            ["icacls", str(path), "/grant", f"{os.getlogin()}:F", "/C", "/Q"] + (["/T"] if path.is_dir() else []),
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            FormatCodes.print(f"[br:yellow][b](⚠ icacls failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print(f"[br:green](✓ Successfully took ownership)")
        return True

    except Exception as e:
        FormatCodes.print(f"[br:red][b](⨯ Error taking ownership:)\n  {str(e).replace('\n', '\n  ')}[_]")
        return False


def remove_attributes_windows(path: Path) -> bool:
    """Remove file attributes on Windows (readonly, system, hidden)."""
    FormatCodes.print(f"[b](Removing file attributes from [br:cyan]({path})...)")

    try:
        result = subprocess.run(
            ["attrib", "-R", "-S", "-H", str(path)] + (["/S", "/D"] if path.is_dir() else []),
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            FormatCodes.print(f"[br:yellow][b](⚠ attrib failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print(f"[br:green](✓ Successfully removed attributes)")
        return True

    except Exception as e:
        FormatCodes.print(f"[br:red][b](⨯ Error removing attributes:)\n  {str(e).replace('\n', '\n  ')}[_]")
        return False


def change_permissions_unix(path: Path) -> bool:
    """Change permissions on Unix systems."""
    FormatCodes.print(f"[b](Changing permissions for [br:cyan]({path})...)")

    try:
        # TRY TO MAKE EVERYTHING WRITABLE
        result = subprocess.run(
            ["chmod", "-R", "777", str(path)] if path.is_dir() else ["chmod", "777", str(path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            FormatCodes.print(f"[br:yellow][b](⚠ chmod failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print(f"[br:green](✓ Successfully changed permissions)")
        return True

    except Exception as e:
        FormatCodes.print(f"[br:red][b](⨯ Error changing permissions:)\n  {str(e).replace('\n', '\n  ')}[_]")
        return False


def unlock_file_macos(path: Path) -> bool:
    """Unlock files on macOS using chflags."""
    FormatCodes.print(f"[b](Unlocking [br:cyan]({path}) on macOS...)")

    try:
        # REMOVE ALL FLAGS INCLUDING USER IMMUTABLE AND SYSTEM IMMUTABLE
        result = subprocess.run(
            ["chflags", "-R", "nouchg,nouappnd,nosappnd,nosunlnk", str(path)] if path.is_dir() \
            else ["chflags", "nouchg,nouappnd,nosappnd,nosunlnk", str(path)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            FormatCodes.print(f"[br:yellow][b](⚠ chflags failed:)\n  {result.stderr.strip().replace('\n', '\n  ')}[_]")
            return False

        FormatCodes.print(f"[br:green](✓ Successfully unlocked file)")
        return True

    except Exception as e:
        FormatCodes.print(f"[br:red][b](⨯ Error unlocking file:)\n  {str(e).replace('\n', '\n  ')}[_]")
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

    else:  # LINUX/UNIX-LIKE
        if change_permissions_unix(path):
            success = True

    return success


def find_processes_using_path(path: Path) -> list[psutil.Process]:
    """Find all processes that have handles to the given path."""
    processes = []
    path = path.resolve()
    system = platform.system()

    for proc in psutil.process_iter(["pid", "name", "open_files", "cwd", "exe"]):
        try:
            # CHECK OPEN FILES
            if proc.info["open_files"]:
                for file in proc.info["open_files"]:
                    file_path = file.path if hasattr(file, "path") else str(file)
                    if (p := str(path).lower()) in (f := file_path.lower()) or f in p:
                        processes.append(proc)
                        break

            # ON UNIX SYSTEMS, ALSO CHECK CURRENT WORKING DIRECTORY
            if system != "Windows":
                try:
                    if ((p := str(path).lower()) in (c := proc.cwd().lower()) or c in p) and proc not in processes:
                        processes.append(proc)
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

        except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
            continue

    return processes


def is_protected_process(proc: psutil.Process) -> bool:
    """Check if a process is in the protected list."""
    try:
        name = proc.name().lower()
        protected_set = get_protected_processes()

        # CHECK EXACT NAME MATCH
        if name in protected_set:
            return True

        # FOR UNIX SYSTEMS, ALSO CHECK WITHOUT EXTENSION AND BASE NAME
        if platform.system() != "Windows":
            base_name = Path(name).name
            if base_name in protected_set:
                return True

        # CHECK IF IT'S PID 1 (init/systemd/launchd) - NEVER TERMINATE THIS
        if proc.pid == 1:
            return True

        # ON UNIX, PROTECT PROCESSES OWNED BY ROOT RUNNING CRITICAL SERVICES
        if platform.system() != "Windows":
            try:
                if proc.username() == "root" and proc.pid < 1000:
                    return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        return False
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return True  # ERR ON THE SIDE OF CAUTION


def terminate_process(proc: psutil.Process) -> bool:
    """Attempt to terminate a process."""
    try:
        FormatCodes.print(f"  Terminating [magenta]({proc.name().strip()}) [dim]((PID [br:magenta]({proc.pid})))...")
        proc.terminate()
        proc.wait(timeout=5)
        return True
    except psutil.TimeoutExpired:
        FormatCodes.print(
            f"  [b|br:yellow](⚠ Process didn't terminate gracefully, killing:)\n"
            f"    [magenta]({proc.name().strip()}) [dim|br:yellow]((PID [br:magenta]({proc.pid})[br:yellow]))"
        )
        try:
            proc.kill()
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return False
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        FormatCodes.print(
            f"  [b|br:red](⨯ Access denied or process no longer exists:)\n"
            f"    [magenta]({proc.name().strip()}) [dim]((PID [br:magenta]({proc.pid})))"
        )
        return False


def attempt_deletion(path: Path) -> bool:
    """Attempt to delete a path."""
    FormatCodes.print(f"[b](Deleting [br:cyan]({path})...)")
    try:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
    except PermissionError:
        FormatCodes.print("[b|br:yellow](⚠ Permission denied!)")
    except OSError as e:
        # ON UNIX SYSTEMS, WE MIGHT GET DIFFERENT ERRORS
        if platform.system() != "Windows":
            FormatCodes.print(f"[br:yellow][b](⚠ Deletion blocked:)\n  {str(e).replace('\n', '\n  ')}[_]")
        else:
            FormatCodes.print(f"[br:red][b](⨯ Error during deletion:)\n  {str(e).replace('\n', '\n  ')}[_]")
    except Exception as e:
        FormatCodes.print(f"[br:red][b](⨯ Error during deletion:)\n  {str(e).replace('\n', '\n  ')}[_]")
    return not path.exists()


def force_delete(path: Path) -> bool:
    """Force delete a file or directory, terminating processes if needed."""
    print()

    # TRY TO DELETE WITHOUT TERMINATING PROCESSES
    if attempt_deletion(path):
        FormatCodes.print(f"[b|br:green](✓ Successfully deleted:) [br:cyan]({path})\n")
        return True

    # FIRST TRY ADVANCED DELETION TECHNIQUES
    FormatCodes.print("[br:yellow](  Trying advanced deletion techniques...)")

    if try_advanced_deletion_techniques(path):
        time.sleep(0.5)
        if attempt_deletion(path):
            FormatCodes.print(f"\n[b|br:green](✓ Successfully deleted:) [br:cyan]({path})\n")
            return True

    # NOW TRY TO FIND PROCESSES USING THE PATH
    FormatCodes.print("[br:yellow](  Searching for processes using this path...)")
    processes = find_processes_using_path(path)

    if processes:
        FormatCodes.print(f"[b](Found [magenta]({(l := len(processes))}) process{'' if l == 1 else 'es'} using this path:)")
        for proc in processes:
            try:
                FormatCodes.print(f"  [magenta]({proc.name()}) [dim]((PID [br:magenta]({proc.pid})))")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        # CHECK FOR PROTECTED PROCESSES
        protected = [p for p in processes if is_protected_process(p)]
        if protected:
            FormatCodes.print("\n[b|br:red](⯃ The following critical system processes are using this path:)")
            for proc in protected:
                try:
                    FormatCodes.print(f"  [magenta]({proc.name()}) [dim]((PID [br:magenta]({proc.pid})))")
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
            FormatCodes.print("  [br:red](These processes will [b](NOT) be terminated for system safety.)\n")
            return False

        # TERMINATE NON-PROTECTED PROCESSES
        FormatCodes.print("[b](Terminating processes...)")
        terminated = []
        for proc in processes:
            if terminate_process(proc):
                terminated.append(proc)

        if not terminated:
            FormatCodes.print("[br:red](Failed to terminate any processes.)\n")
        else:
            time.sleep(1)
            if attempt_deletion(path):
                FormatCodes.print(f"\n[b|br:green](✓ Successfully deleted:) [br:cyan]({path})\n")
                return True

    # STILL FAILED - GIVE UP :(
    FormatCodes.print(f"\n[b|br:red](⨯ Failed to delete even after trying all techniques :()\n")

    if not System.is_elevated:
        if platform.system() == "Windows":
            FormatCodes.print("[dim|br:blue](ⓘ [i](Try running with Administrator privileges.))\n")
        else:
            FormatCodes.print("[dim|br:blue](ⓘ [i](Try running with sudo for elevated privileges.))\n")
    else:
        FormatCodes.print(
            "[dim|br:blue](ⓘ [i](The file/directory may be protected by the system or in use by a kernel-level process.))\n"
        )

    return False


def path_validator(path: str) -> Optional[str]:
    if not Path(path).exists():
        max_w = Console.w - 23
        str_p = path if (l := len(path)) <= max_w else f"...{path[l - (max_w - 3):]}"
        return f"Path [i]({str_p}) doesn't exist."


def main():
    if ARGS.help.exists:
        print_help()
        return

    FormatCodes.print(f"\n[b|bg:black]( {platform.system()} [in]( FORCE DELETE UTILITY ))")
    Console.log_box_bordered(
        "[br:yellow](This will terminate processes if needed.)",
        "[br:yellow](Critical system processes are protected.)",
        border_style="dim|br:yellow",
    )

    if not System.is_elevated:
        if platform.system() == "Windows":
            FormatCodes.print("\n[br:yellow](⚠ Not running as Administrator. Some operations may fail.)")
        else:
            FormatCodes.print(
                "\n[br:yellow](⚠ Not running as root. Some operations may fail.)\n"
                "  [dim|br:yellow](Consider running:) [b|br:white](sudo) [white](python) [br:green](x-rm) [br:cyan](<path>)"
            )

    if len(target_path := "".join(ARGS.rm_path.values)) == 0:
        target_path = Console.input("\n[b](Path to file/directory to delete > )", validator=path_validator)

    if not (target_path := Path(target_path)).exists():
        Console.fail(f"Path [br:cyan]({target_path}) does not exist!", start="\n", end="\n\n")

    if not ARGS.confirm.exists and not Console.confirm(
            f"\n[b](Are you sure you want to delete) [br:cyan]({target_path})[b](?)",
            default_is_yes=False,
    ):
        Console.exit("Deletion aborted.", start="\n", end="\n\n", exit_code=0)

    sys.exit(0 if force_delete(target_path) else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        FormatCodes.print("[b|br:red](⨯ Canceled by user.)\n")
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
