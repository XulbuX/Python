from xulbux import FormatCodes, Console, System
from typing import Optional
from pathlib import Path
import platform
import shutil
import psutil
import time
import sys
import os

######################### CRITICAL PROCESSES THAT SHOULD NEVER BE TERMINATED #########################

PROTECTED_PROCESSES_WINDOWS = {
    'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe', 'winlogon.exe', 'dwm.exe', 'explorer.exe',
    'svchost.exe'
}
PROTECTED_PROCESSES_MACOS = {
    'WindowServer', 'Finder', 'Dock', 'SystemUIServer', 'loginwindow', 'kernel_task', 'UserEventAgent', 'coreaudiod', 'configd'
}
PROTECTED_PROCESSES_UNIX = {
    'systemd', 'init', 'kthreadd', 'rcu_sched', 'migration', 'watchdog', 'systemd-journald', 'systemd-udevd', 'dbus-daemon',
    'NetworkManager', 'sshd', 'cron', 'rsyslogd', 'login', 'bash', 'sh', 'zsh', 'fish', 'kernel', 'launchd'
}

ARGS = Console.get_args(
    {
        "rem_path": "before",
        "no_confirm": ["-nc", "--no-confirm"],
        "help": ["-h", "--help"],
    },
    allow_spaces=True,
)


def print_help():
    help_text = """
[b|in|bg:black]( Force Remove - Delete files/directories even if locked by processes )

[b](Usage:) [br:green](x-rm) [br:cyan](<path>) [br:blue]([options])

[b](Arguments:)
  [br:cyan](path)                 The path to the file or directory to delete

[b](Options:)
  [br:blue](-nc), [br:blue](--no-confirm)    Skip confirmation prompt before deletion

[b](Examples:)
  [br:green](x-rm) [br:cyan]("/path/to/directory")                [dim](# [i](Delete a directory))
  [br:green](x-rm) [br:cyan]("/path/to/file.txt") [br:blue](--no-confirm)    [dim](# [i](Delete a file skipping confirmation))
"""
    FormatCodes.print(help_text)


def get_protected_processes() -> set[str]:
    """Get the appropriate protected processes list for the current OS."""
    if (system := platform.system()) == 'Windows':
        return PROTECTED_PROCESSES_WINDOWS
    elif system == 'Darwin':  # macOS
        return PROTECTED_PROCESSES_UNIX | PROTECTED_PROCESSES_MACOS
    else:  # LINUX OR UNIX-LIKE
        return PROTECTED_PROCESSES_UNIX


def find_processes_using_path(path: Path) -> list[psutil.Process]:
    """Find all processes that have handles to the given path."""
    processes = []
    path = path.resolve()
    system = platform.system()

    for proc in psutil.process_iter(['pid', 'name', 'open_files', 'cwd', 'exe']):
        try:
            # CHECK OPEN FILES
            if proc.info['open_files']:
                for file in proc.info['open_files']:
                    file_path = file.path if hasattr(file, 'path') else str(file)
                    if (p := str(path).lower()) in (f := file_path.lower()) or f in p:
                        processes.append(proc)
                        break

            # ON UNIX SYSTEMS, ALSO CHECK CURRENT WORKING DIRECTORY
            if system != 'Windows':
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
        if platform.system() != 'Windows':
            base_name = os.path.basename(name)
            if base_name in protected_set:
                return True

        # CHECK IF IT'S PID 1 (init/systemd/launchd) - NEVER TERMINATE THIS
        if proc.pid == 1:
            return True

        # ON UNIX, PROTECT PROCESSES OWNED BY ROOT RUNNING CRITICAL SERVICES
        if platform.system() != 'Windows':
            try:
                if proc.username() == 'root' and proc.pid < 1000:
                    return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

        return False
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return True  # ERR ON THE SIDE OF CAUTION


def terminate_process(proc: psutil.Process) -> bool:
    """Attempt to terminate a process."""
    try:
        print(f"  Terminating process: {proc.name()} (PID: {proc.pid})")
        proc.terminate()
        proc.wait(timeout=5)
        return True
    except psutil.TimeoutExpired:
        print(f"  Process didn't terminate gracefully, killing: {proc.name()} (PID: {proc.pid})")
        try:
            proc.kill()
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return False
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        print(f"  Access denied or process no longer exists: {proc.name()} (PID: {proc.pid})")
        return False


def force_delete(path: Path) -> bool:
    """Force delete a file or directory, terminating processes if needed."""

    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        return False

    print(f"\nAttempting to delete: {path}")

    # TRY TO DELETE WITHOUT TERMINATING PROCESSES
    try:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        print(f"✓ Successfully deleted: {path}")
        return True
    except PermissionError:
        print("Permission denied. Searching for processes using this path...")
    except OSError as e:
        # ON UNIX SYSTEMS, WE MIGHT GET DIFFERENT ERRORS
        if platform.system() != 'Windows':
            print(f"Deletion blocked: {e}. Searching for processes using this path...")
        else:
            print(f"Error during deletion: {e}")
            return False
    except Exception as e:
        print(f"Error during deletion: {e}")
        return False

    # [2] CHECK IF WE NEED ELEVATED PRIVILEGES
    if platform.system() != 'Windows' and os.geteuid() != 0:  # type: ignore[unknown-attr]
        print("\n⚠ Note: Running without root privileges. Some operations may fail.")
        print("  Consider running with sudo for full functionality.\n")

    # FIND PROCESSES USING THE PATH
    processes = find_processes_using_path(path)

    if not processes:
        print("No processes found using this path, but deletion still failed.")
        if platform.system() == 'Windows':
            print("The file may be locked by the system or you may need administrator privileges.")
        else:
            print("The file may be locked by the system or you may need root privileges (sudo).")
        return False

    print(f"\nFound {len(processes)} process(es) using this path:")
    for proc in processes:
        try:
            print(f"  - {proc.name()} (PID: {proc.pid})")
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    # CHECK FOR PROTECTED PROCESSES
    protected = [p for p in processes if is_protected_process(p)]
    if protected:
        print("\n⚠ Warning: The following critical system processes are using this path:")
        for proc in protected:
            try:
                print(f"  - {proc.name()} (PID: {proc.pid})")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        print("These processes will NOT be terminated for system safety.")
        return False

    # TERMINATE NON-PROTECTED PROCESSES
    print("\nTerminating processes...")
    terminated = []
    for proc in processes:
        if terminate_process(proc):
            terminated.append(proc)

    if not terminated:
        print("Failed to terminate any processes.")
        return False

    # WAIT A MOMENT FOR FILE HANDLES TO BE RELEASED
    time.sleep(1)

    # RETRY DELETION
    try:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        print(f"\n✓ Successfully deleted: {path}")
        return True
    except Exception as e:
        print(f"\n⨯ Failed to delete even after terminating processes: {e}")
        if platform.system() != 'Windows' and os.geteuid() != 0:  # type: ignore[unknown-attr]
            print("  Try running with sudo for elevated privileges.")
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

    FormatCodes.print(
        f"\n[b|bg:black]( {platform.system()} [in]( Force Delete Utility ))\n\n"
        "[br:yellow]⚠ This script will terminate processes if needed.\n"
        "  [dim](Critical system processes are protected.)[_c]\n"
    )

    if len(target_path := "".join(ARGS.rem_path.values)) == 0:
        target_path = Console.input(
            "[b](Path to file/directory to delete > )",
            validator=path_validator,
        )
    target_path = Path(target_path)

    if not target_path.exists():
        Console.fail(f"Path [br:cyan]({target_path}) does not exist!")

    # CHECK PRIVILEGES
    if not System.is_elevated:
        if platform.system() == 'Windows':
            FormatCodes.print("[br:yellow](⚠ Not running as Administrator. Some operations may fail.)\n")
        else:
            FormatCodes.print(
                "[br:yellow](⚠ Not running as root. Some operations may fail.)\n"
                "[dim|br:yellow](⮡ Consider running:) [b|br:white](sudo) [white](python) [br:green](x-rm) [br:cyan](<path>)\n"
            )

    if not ARGS.no_confirm.exists and not Console.confirm(
            f"[b](Are you sure you want to delete) [br:cyan]({target_path})[b](?)",
            default_is_yes=False,
    ):
        Console.exit("Deletion aborted.", start="\n", end="\n\n", exit_code=0)

    sys.exit(0 if force_delete(target_path) else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
