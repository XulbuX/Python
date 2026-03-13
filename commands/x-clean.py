#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""System Paths Cleaner — clean broken registry entries, env vars, shortcuts, and more."""

from pathlib import Path
from typing import Optional
from datetime import datetime
from xulbux import FormatCodes, Console, System, FileSys
from xulbux.console import Throbber
import subprocess
import winreg
import json
import os

try:
    from win32com.client import Dispatch as COMDispatch
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False


########################################## CONSTANTS ##########################################

SCRIPT_DIR = FileSys.script_dir
BACKUPS_DIR = SCRIPT_DIR / "backups"

# REGISTRY UNINSTALL LOCATIONS
REGISTRY_UNINSTALL_PATHS: list[tuple[int, str]] = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
]

# REGISTRY APP PATHS LOCATIONS (BONUS)
REGISTRY_APP_PATHS: list[tuple[int, str]] = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
]

# VALUES IN UNINSTALL KEYS THAT INDICATE WHETHER THE SOFTWARE IS ACTUALLY INSTALLED
# NOTE: InstallSource and DisplayIcon are intentionally excluded — they are informational
# only (installer cache / icon path) and do NOT indicate the software is uninstalled.
PATH_VALUE_NAMES = {
    "UninstallString", "QuietUninstallString", "InstallLocation", "ModifyPath",
}

# ENVIRONMENT VARIABLE REGISTRY LOCATIONS
ENV_USER_KEY = (winreg.HKEY_CURRENT_USER, r"Environment")
ENV_SYSTEM_KEY = (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")

# SHORTCUT DIRECTORIES TO SCAN
SHORTCUT_DIRS: list[tuple[str, Path]] = []

def _build_shortcut_dirs() -> list[tuple[str, Path]]:
    """Build list of shortcut directories to scan."""
    dirs: list[tuple[str, Path]] = []
    appdata = os.environ.get("APPDATA", "")
    programdata = os.environ.get("PROGRAMDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")
    public = os.environ.get("PUBLIC", "")
    if appdata:
        dirs.append(("User Startup", Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"))
        dirs.append(("User Start Menu", Path(appdata) / r"Microsoft\Windows\Start Menu\Programs"))
    if programdata:
        dirs.append(("Global Startup", Path(programdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"))
        dirs.append(("Global Start Menu", Path(programdata) / r"Microsoft\Windows\Start Menu\Programs"))
    if userprofile:
        dirs.append(("User Desktop", Path(userprofile) / "Desktop"))
    if public:
        dirs.append(("Public Desktop", Path(public) / "Desktop"))
    return dirs

HIVE_NAMES = {
    winreg.HKEY_CURRENT_USER: "HKCU",
    winreg.HKEY_LOCAL_MACHINE: "HKLM",
}

########################################## CLI ARGS ##########################################

ARGS = Console.get_args({
    "restore_path": "before",
    "restore": {"-r", "--restore"},
    "help": {"-h", "--help"},
})


########################################## HELPERS ##########################################

def hive_name(hive: int) -> str:
    """Get readable name for a registry hive."""
    return HIVE_NAMES.get(hive, str(hive))


def extract_path_from_value(value: str) -> Optional[Path]:
    """Extract a file/directory path from a registry value string.
    Handles quoted paths, paths with args, MsiExec, rundll32, etc."""
    if not value or not isinstance(value, str):
        return None
    val = value.strip()
    if not val:
        return None

    # SKIP MSIEXEC AND RUNDLL32 ENTRIES — THEY DON'T POINT TO REAL UNINSTALLERS ON DISK
    lower = val.lower()
    if lower.startswith("msiexec") or lower.startswith("rundll32"):
        return None

    # HANDLE QUOTED PATHS: "C:\path\to\file.exe" /args
    if val.startswith('"'):
        end = val.find('"', 1)
        if end != -1:
            return Path(val[1:end])

    # HANDLE PATHS WITH ARGUMENTS: C:\path\file.exe /arg
    # LOOK FOR .EXE OR OTHER EXECUTABLE EXTENSIONS
    for ext in (".exe", ".msi", ".bat", ".cmd", ".com"):
        idx = lower.find(ext)
        if idx != -1:
            return Path(val[:idx + len(ext)])

    # HANDLE DISPLAY ICON FORMAT: path.exe,0
    if "," in val:
        candidate = val.split(",")[0].strip().strip('"')
        if candidate and (candidate[1:3] == ":\\" or candidate.startswith("\\\\")):
            return Path(candidate)

    # IF IT LOOKS LIKE AN ABSOLUTE PATH, RETURN IT
    if len(val) >= 3 and val[1:3] == ":\\" or val.startswith("\\\\"):
        return Path(val)

    return None


def expand_env_in_path(value: str) -> str:
    """Expand environment variable references like %USERPROFILE% in a string."""
    return os.path.expandvars(value)


def path_exists(p: Path) -> bool:
    """Check if a path exists, handling long paths and permission issues.
    Also expands environment variable references like %USERPROFILE%."""
    try:
        expanded = Path(expand_env_in_path(str(p)))
        return expanded.exists()
    except (OSError, PermissionError, ValueError):
        return False


def looks_like_path(value: str) -> bool:
    """Check if a string value looks like it could be a filesystem path."""
    if not value or not isinstance(value, str):
        return False
    v = value.strip().strip('"')
    if not v:
        return False
    # EXPAND ENVIRONMENT VARIABLES FIRST
    expanded = os.path.expandvars(v)
    # ABSOLUTE PATHS: C:\..., \\server\...
    if len(expanded) >= 3 and expanded[1:3] == ":\\":
        return True
    if expanded.startswith("\\\\"):
        return True
    # ENVIRONMENT VARIABLE REFERENCES THAT LOOK LIKE PATHS (E.G. %SYSTEMROOT%\...)
    if "%" in v and ("\\" in v or "/" in v):
        return True
    # PATHS WITH PATH SEPARATORS AND TYPICAL EXTENSIONS/DIRECTORIES
    if "\\" in v or "/" in v:
        return any(seg in v.lower() for seg in ("program files", "windows", "users", "appdata"))
    return False


def resolve_shortcut(lnk_path: Path) -> Optional[Path]:
    """Resolve a .lnk shortcut file to its target path."""
    if not HAS_WIN32COM:
        return None
    try:
        shell = COMDispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(str(lnk_path))
        target = shortcut.TargetPath
        if target:
            return Path(target)
        return None
    except Exception:
        return None


########################################## SCANNING ##########################################

def scan_registry_uninstall() -> list[dict]:
    """Scan uninstall registry keys for entries with broken paths.
    Returns list of dicts: {hive, path, subkey, display_name, broken_values}"""
    issues: list[dict] = []

    for hive, reg_path in REGISTRY_UNINSTALL_PATHS:
        try:
            root_key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        except OSError:
            continue

        try:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(root_key, i)
                except OSError:
                    break
                i += 1

                full_path = f"{reg_path}\\{subkey_name}"
                try:
                    subkey = winreg.OpenKey(hive, full_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                except OSError:
                    continue

                # GET DISPLAY NAME
                display_name = subkey_name
                try:
                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                except OSError:
                    pass

                # CHECK ALL PATH VALUES IN THIS KEY
                broken_values: list[tuple[str, str]] = []
                has_any_valid = False

                for val_name in PATH_VALUE_NAMES:
                    try:
                        val_data, val_type = winreg.QueryValueEx(subkey, val_name)
                    except OSError:
                        continue

                    if val_type not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                        continue

                    p = extract_path_from_value(str(val_data))
                    if p is None:
                        continue

                    if path_exists(p):
                        has_any_valid = True
                    else:
                        broken_values.append((val_name, str(val_data)))

                winreg.CloseKey(subkey)

                # IF WE FOUND BROKEN PATHS AND NO VALID PATHS, FLAG THE ENTIRE ENTRY
                if broken_values and not has_any_valid:
                    issues.append({
                        "hive": hive,
                        "path": full_path,
                        "subkey": subkey_name,
                        "display_name": display_name,
                        "broken_values": broken_values,
                    })
        finally:
            winreg.CloseKey(root_key)

    return issues


def scan_registry_app_paths() -> list[dict]:
    """Scan App Paths registry keys for entries with broken paths.
    Returns list of dicts: {hive, path, subkey, broken_path}"""
    issues: list[dict] = []

    for hive, reg_path in REGISTRY_APP_PATHS:
        try:
            root_key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        except OSError:
            continue

        try:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(root_key, i)
                except OSError:
                    break
                i += 1

                full_path = f"{reg_path}\\{subkey_name}"
                try:
                    subkey = winreg.OpenKey(hive, full_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                except OSError:
                    continue

                # CHECK DEFAULT VALUE (THE APP PATH)
                try:
                    val_data, val_type = winreg.QueryValueEx(subkey, "")
                    if val_type in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) and val_data:
                        p = Path(val_data.strip('"'))
                        if not path_exists(p):
                            issues.append({
                                "hive": hive,
                                "path": full_path,
                                "subkey": subkey_name,
                                "broken_path": str(val_data),
                            })
                except OSError:
                    pass

                winreg.CloseKey(subkey)
        finally:
            winreg.CloseKey(root_key)

    return issues


def scan_env_vars() -> dict:
    """Scan environment variables for broken paths.
    Returns dict with keys 'user' and 'system', each containing a list of issues:
    {name, value_type, original_value, broken_paths, scope}"""
    result: dict[str, list[dict]] = {"user": [], "system": []}

    for scope, (hive, reg_path) in [("user", ENV_USER_KEY), ("system", ENV_SYSTEM_KEY)]:
        try:
            key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_READ)
        except OSError:
            continue

        try:
            i = 0
            while True:
                try:
                    name, value, val_type = winreg.EnumValue(key, i)
                except OSError:
                    break
                i += 1

                if val_type not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                    continue

                str_value = str(value)

                # CHECK IF THIS IS A PATH-LIST VARIABLE (LIKE PATH)
                if ";" in str_value and any(looks_like_path(p) for p in str_value.split(";")):
                    paths = [p.strip() for p in str_value.split(";") if p.strip()]
                    broken = [p for p in paths if looks_like_path(p) and not path_exists(Path(expand_env_in_path(p.strip('"'))))]
                    if broken:
                        result[scope].append({
                            "name": name,
                            "value_type": val_type,
                            "original_value": str_value,
                            "broken_paths": broken,
                            "scope": scope,
                        })
                # CHECK IF THE SINGLE VALUE LOOKS LIKE A BROKEN PATH
                elif looks_like_path(str_value):
                    p = Path(expand_env_in_path(str_value.strip().strip('"')))
                    if not path_exists(p):
                        result[scope].append({
                            "name": name,
                            "value_type": val_type,
                            "original_value": str_value,
                            "broken_paths": [str_value],
                            "scope": scope,
                        })
        finally:
            winreg.CloseKey(key)

    return result


def scan_shortcuts() -> list[dict]:
    """Scan shortcut directories for broken .lnk files.
    Returns list of dicts: {label, dir_path, broken_shortcuts}
    where broken_shortcuts is list of {lnk_path, target}"""
    if not HAS_WIN32COM:
        return []

    issues: list[dict] = []
    shortcut_dirs = _build_shortcut_dirs()

    for label, dir_path in shortcut_dirs:
        if not dir_path.exists():
            continue

        broken_shortcuts: list[dict] = []
        _scan_shortcuts_recursive(dir_path, broken_shortcuts)

        if broken_shortcuts:
            issues.append({
                "label": label,
                "dir_path": dir_path,
                "broken_shortcuts": broken_shortcuts,
            })

    return issues


def _scan_shortcuts_recursive(directory: Path, broken_list: list[dict]) -> None:
    """Recursively scan a directory for broken shortcuts."""
    try:
        entries = list(directory.iterdir())
    except (PermissionError, OSError):
        return

    for entry in entries:
        if entry.is_dir():
            _scan_shortcuts_recursive(entry, broken_list)
        elif entry.suffix.lower() == ".lnk":
            target = resolve_shortcut(entry)
            if target is not None and not path_exists(target):
                broken_list.append({
                    "lnk_path": entry,
                    "target": str(target),
                })


def scan_temp_files() -> dict:
    """Scan temp directories for cleanable files.
    Returns dict: {dirs: list of {path, file_count, size_bytes}}"""
    temp_dirs_to_check = []

    # WINDOWS TEMP
    win_temp = Path(os.environ.get("TEMP", ""))
    if win_temp.exists():
        temp_dirs_to_check.append(("User Temp", win_temp))

    # SYSTEM TEMP
    sys_temp = Path(r"C:\Windows\Temp")
    if sys_temp.exists():
        temp_dirs_to_check.append(("System Temp", sys_temp))

    # PREFETCH
    prefetch = Path(r"C:\Windows\Prefetch")
    if prefetch.exists():
        temp_dirs_to_check.append(("Prefetch", prefetch))

    result: list[dict] = []
    for label, dir_path in temp_dirs_to_check:
        file_count = 0
        total_size = 0
        try:
            for f in dir_path.rglob("*"):
                if f.is_file():
                    file_count += 1
                    try:
                        total_size += f.stat().st_size
                    except (OSError, PermissionError):
                        pass
        except (PermissionError, OSError):
            pass

        if file_count > 0:
            result.append({
                "label": label,
                "path": dir_path,
                "file_count": file_count,
                "size_bytes": total_size,
            })

    return {"dirs": result}


########################################## BACKUPS ##########################################

def create_backup_dir() -> Path:
    """Create a timestamped backup directory."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = BACKUPS_DIR / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_registry(backup_dir: Path) -> bool:
    """Export uninstall and app paths registry keys to .reg files."""
    all_locations = REGISTRY_UNINSTALL_PATHS + REGISTRY_APP_PATHS
    success = True

    for hive, reg_path in all_locations:
        full_path = f"{hive_name(hive)}\\{reg_path}"
        safe_name = reg_path.replace("\\", "_")
        filename = f"{hive_name(hive)}_{safe_name}.reg"
        export_path = backup_dir / filename

        try:
            result = subprocess.run(
                ["reg", "export", full_path, str(export_path), "/y"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                FormatCodes.print(f"  [yellow](⚠ Failed to export [dim]({full_path})[yellow]:)\n    {result.stderr.strip()}")
                success = False
            else:
                FormatCodes.print(f"  [green](✓) Exported [dim]({full_path})")
        except Exception as e:
            FormatCodes.print(f"  [red](✗ Error exporting [dim]({full_path})[red]:)\n    {e}")
            success = False

    return success


def backup_env_vars(backup_dir: Path) -> bool:
    """Backup all environment variables (user + system) to a JSON file."""
    data: dict[str, dict[str, dict]] = {"user": {}, "system": {}}

    for scope, (hive, reg_path) in [("user", ENV_USER_KEY), ("system", ENV_SYSTEM_KEY)]:
        try:
            key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_READ)
        except OSError:
            continue

        try:
            i = 0
            while True:
                try:
                    name, value, val_type = winreg.EnumValue(key, i)
                except OSError:
                    break
                i += 1
                data[scope][name] = {
                    "value": value,
                    "type": val_type,
                }
        finally:
            winreg.CloseKey(key)

    backup_file = backup_dir / "env_vars_backup.json"
    try:
        backup_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        FormatCodes.print(f"  [green](✓) Saved env vars to [dim]({backup_file})")
        return True
    except Exception as e:
        FormatCodes.print(f"  [red](✗ Failed to save env vars backup:)\n    {e}")
        return False


########################################## RESTORE ##########################################

def restore_env_vars(backup_path: Path) -> None:
    """Restore environment variables from a JSON backup file."""
    if not backup_path.exists():
        Console.fail(f"Backup file does not exist: [br:cyan]({backup_path})", start="\n", end="\n\n")
        return

    FormatCodes.print(f"\n[b](Loading backup from [br:cyan]({backup_path})[b]...)")

    try:
        data = json.loads(backup_path.read_text(encoding="utf-8"))
    except Exception as e:
        Console.fail(f"Failed to read backup file: {e}", start="\n", end="\n\n")
        return

    # SHOW WHAT WILL BE RESTORED
    for scope in ("user", "system"):
        if scope in data and data[scope]:
            FormatCodes.print(f"\n  [b]({scope.upper()} variables:) [dim]({len(data[scope])} entries)")

    if not Console.confirm("\n[b](Restore these environment variables?)", default_is_yes=False):
        Console.exit("Restore canceled.", start="\n", end="\n\n", exit_code=0)
        return

    failures: list[str] = []
    restored = 0

    for scope, (hive, reg_path) in [("user", ENV_USER_KEY), ("system", ENV_SYSTEM_KEY)]:
        if scope not in data:
            continue

        for name, var_info in data[scope].items():
            try:
                key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, name, 0, var_info["type"], var_info["value"])
                winreg.CloseKey(key)
                FormatCodes.print(f"  [green](✓) Restored [b]({scope})[green](/) [cyan]({name})")
                restored += 1
            except Exception as e:
                msg = f"Failed to restore {scope}/{name}: {e}"
                failures.append(msg)
                FormatCodes.print(f"  [red](✗) {msg}")

    FormatCodes.print(f"\n[b|green](✓ Restored {restored} variable(s).)")
    if failures:
        FormatCodes.print(f"[b|red](✗ {len(failures)} failure(s).)\n")

    # BROADCAST ENVIRONMENT CHANGE
    _broadcast_env_change()


def _broadcast_env_change() -> None:
    """Broadcast WM_SETTINGCHANGE so other processes pick up env var changes."""
    try:
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0,
            "Environment", SMTO_ABORTIFHUNG, 5000, None
        )
    except Exception:
        pass


########################################## CLEANUP EXECUTION ##########################################

def execute_registry_cleanup(issues: list[dict], app_path_issues: list[dict]) -> list[str]:
    """Delete broken registry entries. Returns list of failure messages."""
    failures: list[str] = []

    if issues:
        FormatCodes.print("\n[b](Cleaning registry uninstall entries...)")
        for issue in issues:
            hive = issue["hive"]
            reg_path = issue["path"]
            display = issue["display_name"]
            try:
                _delete_registry_tree(hive, reg_path)
                FormatCodes.print(f"  [green](✓) Deleted [magenta]({display}) [dim]({hive_name(hive)}\\{reg_path})")
            except Exception as e:
                msg = f"Failed to delete {hive_name(hive)}\\{reg_path}: {e}"
                failures.append(msg)
                FormatCodes.print(f"  [red](✗) {msg}")

    if app_path_issues:
        FormatCodes.print("\n[b](Cleaning registry App Paths entries...)")
        for issue in app_path_issues:
            hive = issue["hive"]
            reg_path = issue["path"]
            subkey = issue["subkey"]
            try:
                _delete_registry_tree(hive, reg_path)
                FormatCodes.print(f"  [green](✓) Deleted [magenta]({subkey}) [dim]({hive_name(hive)}\\{reg_path})")
            except Exception as e:
                msg = f"Failed to delete {hive_name(hive)}\\{reg_path}: {e}"
                failures.append(msg)
                FormatCodes.print(f"  [red](✗) {msg}")

    return failures


def _delete_registry_tree(hive: int, key_path: str) -> None:
    """Recursively delete a registry key and all its subkeys."""
    try:
        key = winreg.OpenKey(hive, key_path, 0,
                             winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        return

    # FIRST DELETE ALL SUBKEYS RECURSIVELY
    try:
        while True:
            try:
                subkey_name = winreg.EnumKey(key, 0)
                _delete_registry_tree(hive, f"{key_path}\\{subkey_name}")
            except OSError:
                break
    finally:
        winreg.CloseKey(key)

    # NOW DELETE THE KEY ITSELF
    parent_path = "\\".join(key_path.split("\\")[:-1])
    key_name = key_path.split("\\")[-1]
    try:
        parent = winreg.OpenKey(hive, parent_path, 0,
                                winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        winreg.DeleteKey(parent, key_name)
        winreg.CloseKey(parent)
    except OSError as e:
        raise OSError(f"Could not delete key {key_path}: {e}")


def execute_env_cleanup(env_issues: dict) -> list[str]:
    """Remove broken paths from environment variables. Returns failure messages."""
    failures: list[str] = []

    for scope, (hive, reg_path) in [("user", ENV_USER_KEY), ("system", ENV_SYSTEM_KEY)]:
        issues = env_issues.get(scope, [])
        if not issues:
            continue

        FormatCodes.print(f"\n[b](Cleaning {scope} environment variables...)")

        for issue in issues:
            name = issue["name"]
            original = issue["original_value"]
            broken = set(issue["broken_paths"])
            val_type = issue["value_type"]

            try:
                # IF THE VARIABLE CONTAINS SEMICOLONS, IT'S A PATH LIST — REMOVE ONLY BROKEN PARTS
                if ";" in original:
                    paths = [p.strip() for p in original.split(";")]
                    cleaned = [p for p in paths if p and p not in broken]
                    new_value = ";".join(cleaned)

                    if not new_value:
                        # ALL PATHS WERE BROKEN — DELETE THE ENTIRE VARIABLE
                        key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_SET_VALUE)
                        winreg.DeleteValue(key, name)
                        winreg.CloseKey(key)
                        FormatCodes.print(f"  [green](✓) Deleted empty variable [cyan]({name}) [dim](from {scope})")
                    else:
                        key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_SET_VALUE)
                        winreg.SetValueEx(key, name, 0, val_type, new_value)
                        winreg.CloseKey(key)
                        removed_count = len(broken)
                        FormatCodes.print(f"  [green](✓) Removed [b]({removed_count}) broken path(s) from [cyan]({name}) [dim](in {scope})")
                else:
                    # ENTIRE VALUE IS A BROKEN PATH — DELETE THE VARIABLE
                    key = winreg.OpenKey(hive, reg_path, 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, name)
                    winreg.CloseKey(key)
                    FormatCodes.print(f"  [green](✓) Deleted variable [cyan]({name}) [dim](from {scope})")

            except Exception as e:
                msg = f"Failed to clean {scope}/{name}: {e}"
                failures.append(msg)
                FormatCodes.print(f"  [red](✗) {msg}")

    # BROADCAST ENVIRONMENT CHANGE
    _broadcast_env_change()

    return failures


def execute_shortcut_cleanup(shortcut_issues: list[dict]) -> list[str]:
    """Delete broken shortcuts and empty directories. Returns failure messages."""
    failures: list[str] = []

    FormatCodes.print("\n[b](Cleaning broken shortcuts...)")

    for location in shortcut_issues:
        label = location["label"]
        FormatCodes.print(f"\n  [b]({label}:)")

        for shortcut_info in location["broken_shortcuts"]:
            lnk_path: Path = shortcut_info["lnk_path"]
            target = shortcut_info["target"]
            try:
                lnk_path.unlink()
                FormatCodes.print(f"    [green](✓) Deleted [dim]({lnk_path.name}) [dim](→ {target})")
            except Exception as e:
                msg = f"Failed to delete {lnk_path}: {e}"
                failures.append(msg)
                FormatCodes.print(f"    [red](✗) {msg}")

    # CLEAN UP EMPTY DIRECTORIES LEFT BEHIND
    shortcut_dirs = _build_shortcut_dirs()
    for _, dir_path in shortcut_dirs:
        if dir_path.exists():
            _remove_empty_dirs(dir_path, failures)

    return failures


def _remove_empty_dirs(directory: Path, failures: list[str]) -> bool:
    """Recursively remove empty directories. Returns True if directory was removed."""
    if not directory.is_dir():
        return False

    try:
        entries = list(directory.iterdir())
    except (PermissionError, OSError):
        return False

    # FIRST RECURSE INTO SUBDIRECTORIES
    all_removed = True
    for entry in entries:
        if entry.is_dir():
            if not _remove_empty_dirs(entry, failures):
                all_removed = False
        else:
            all_removed = False

    # DON'T REMOVE ROOT SHORTCUT DIRS, ONLY THEIR SUBDIRECTORIES
    shortcut_dirs = _build_shortcut_dirs()
    root_dirs = {d.resolve() for _, d in shortcut_dirs}
    if directory.resolve() in root_dirs:
        return False

    if all_removed:
        try:
            directory.rmdir()
            FormatCodes.print(f"    [green](✓) Removed empty folder [dim]({directory})")
            return True
        except Exception as e:
            failures.append(f"Failed to remove empty dir {directory}: {e}")
            return False

    return False


def execute_temp_cleanup(temp_info: dict) -> list[str]:
    """Clean temp directories. Returns failure messages."""
    failures: list[str] = []

    FormatCodes.print("\n[b](Cleaning temp files...)")

    for dir_info in temp_info["dirs"]:
        label = dir_info["label"]
        dir_path: Path = dir_info["path"]
        FormatCodes.print(f"\n  [b]({label}:) [dim]({dir_path})")

        deleted = 0
        failed = 0
        try:
            for item in list(dir_path.iterdir()):
                try:
                    if item.is_file():
                        item.unlink()
                        deleted += 1
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item, ignore_errors=True)
                        if not item.exists():
                            deleted += 1
                        else:
                            failed += 1
                except (PermissionError, OSError):
                    failed += 1
        except (PermissionError, OSError) as e:
            failures.append(f"Cannot access {dir_path}: {e}")

        FormatCodes.print(f"    [green](✓) Deleted [b]({deleted}) item(s)")
        if failed:
            FormatCodes.print(f"    [yellow](⚠ {failed} item(s) could not be deleted [dim]((locked/in use)))")

    return failures


########################################## DISPLAY ##########################################

def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def show_summary(
    reg_issues: list[dict],
    app_path_issues: list[dict],
    env_issues: dict,
    shortcut_issues: list[dict],
    temp_info: dict,
    selected: dict[str, bool],
) -> None:
    """Show a detailed summary of what will be cleaned."""
    FormatCodes.print("\n[b|bg:black]( CLEANUP SUMMARY )\n")

    if selected.get("registry") and (reg_issues or app_path_issues):
        FormatCodes.print("[b](Registry entries to delete:)")
        for issue in reg_issues:
            FormatCodes.print(
                f"  [red](✗) [magenta]({issue['display_name']})"
                f" [dim]({hive_name(issue['hive'])}\\...\\{issue['subkey']})"
            )
            for val_name, val_data in issue["broken_values"]:
                p = extract_path_from_value(val_data)
                FormatCodes.print(f"      [dim]({val_name} → {p or val_data})")

        for issue in app_path_issues:
            FormatCodes.print(
                f"  [red](✗) [magenta]({issue['subkey']})"
                f" [dim]({hive_name(issue['hive'])}\\...\\App Paths)"
            )
            FormatCodes.print(f"      [dim](→ {issue['broken_path']})")
        print()

    if selected.get("envvars") and (env_issues.get("user") or env_issues.get("system")):
        FormatCodes.print("[b](Environment variables to clean:)")
        for scope in ("user", "system"):
            for issue in env_issues.get(scope, []):
                name = issue["name"]
                broken = issue["broken_paths"]
                original = issue["original_value"]

                if ";" in original:
                    FormatCodes.print(f"  [cyan]({name}) [dim]({scope}) — remove [b]({len(broken)}) broken path(s):")
                    for bp in broken:
                        FormatCodes.print(f"      [red](✗) [dim]({bp})")
                else:
                    FormatCodes.print(f"  [cyan]({name}) [dim]({scope}) — [red](delete entire variable)")
                    FormatCodes.print(f"      [dim](→ {original})")
        print()

    if selected.get("shortcuts") and shortcut_issues:
        total_broken = sum(len(loc["broken_shortcuts"]) for loc in shortcut_issues)
        FormatCodes.print(f"[b](Broken shortcuts to delete:) [dim]({total_broken} total)")
        for location in shortcut_issues:
            FormatCodes.print(f"  [b]({location['label']}:)")
            for sc in location["broken_shortcuts"]:
                FormatCodes.print(f"    [red](✗) [dim]({sc['lnk_path'].name}) → {sc['target']}")
        print()

    if selected.get("temp") and temp_info.get("dirs"):
        FormatCodes.print("[b](Temp directories to clean:)")
        for d in temp_info["dirs"]:
            FormatCodes.print(
                f"  [yellow](⟳) [b]({d['label']}) — "
                f"[dim]({d['file_count']} files, {format_size(d['size_bytes'])})"
            )
        print()


def print_help():
    help_text = """
[b|in|bg:black]( System Paths Cleaner — Clean broken registry entries, env vars, shortcuts & more )

[b](Usage:) [green](x-clean) [blue]([options])

[b](Options:)
  [blue](-h), [blue](--help)       Show this help message
  [blue](-r), [blue](--restore)    Restore env vars from a backup JSON file

[b](Restore example:)
  [green](x-clean) [blue](--restore) [cyan]("path/to/env_vars_backup.json")

[b](What it cleans:)
  [magenta](1.) Registry uninstall entries with broken paths
  [magenta](2.) Registry App Paths entries pointing to missing executables
  [magenta](3.) Environment variables containing non-existent paths
  [magenta](4.) Broken shortcut (.lnk) files in Start Menu, Startup, Desktop
  [magenta](5.) Temp files (User Temp, System Temp, Prefetch)
"""
    FormatCodes.print(help_text)


########################################## MAIN ##########################################

def choose_options() -> dict[str, bool]:
    """Let the user choose which cleanup options to run."""
    FormatCodes.print("\n[b](Choose what to clean:)\n")
    options = [
        ("registry", "Registry uninstall entries + App Paths"),
        ("envvars", "Environment variables"),
        ("shortcuts", "Broken shortcut files (.lnk)"),
        ("temp", "Temp files (User Temp, System Temp, Prefetch)"),
    ]

    if not HAS_WIN32COM:
        FormatCodes.print("  [dim|yellow](⚠ pywin32 not installed — shortcut scanning disabled)\n")

    selected: dict[str, bool] = {}
    for key, label in options:
        if key == "shortcuts" and not HAS_WIN32COM:
            selected[key] = False
            continue
        answer = Console.confirm(f"  [b]({label}?)", default_is_yes=True)
        selected[key] = answer

    return selected


def main():
    if ARGS.help.exists:
        print_help()
        return

    # HANDLE RESTORE MODE
    if ARGS.restore.exists:
        restore_path_str = "".join(ARGS.restore_path.values).strip()
        if not restore_path_str:
            Console.fail("Please provide a path to the backup JSON file.\n  Usage: [green](x-clean) [blue](--restore) [cyan](path/to/backup.json)", start="\n", end="\n\n")
            return
        restore_env_vars(Path(restore_path_str))
        return

    FormatCodes.print(f"\n[b|bg:black]( Windows [in]( SYSTEM PATHS CLEANER ))")
    Console.log_box_bordered(
        "[yellow](This tool scans for and removes broken system paths.)",
        "[yellow](Backups are created before any modifications.)",
        border_style="dim|yellow",
    )

    if not System.is_elevated:
        FormatCodes.print("\n[yellow](⚠ Not running as Administrator. Some operations may fail.)")
        FormatCodes.print("[dim|yellow](  System-level registry and env var changes require elevation.)")

    # ───────── STEP 1: CHOOSE CLEANUP OPTIONS ─────────
    selected = choose_options()

    if not any(selected.values()):
        Console.exit("Nothing selected.", start="\n", end="\n\n", exit_code=0)
        return

    # ───────── STEP 2: CREATE BACKUPS ─────────
    FormatCodes.print("\n[b|bg:black]( CREATING BACKUPS )\n")

    backup_dir = create_backup_dir()
    backup_ok = True

    if selected.get("registry"):
        FormatCodes.print("[b](Backing up registry keys...)")
        if not backup_registry(backup_dir):
            backup_ok = False

    if selected.get("envvars"):
        FormatCodes.print("\n[b](Backing up environment variables...)")
        if not backup_env_vars(backup_dir):
            backup_ok = False

    if not backup_ok:
        Console.fail(
            f"Some backups failed! Aborting for safety.\n  Backup directory: [br:cyan]({backup_dir})",
            start="\n", end="\n\n",
        )
        return

    FormatCodes.print(f"\n[b|green](✓ Backups saved to:) [br:cyan]({backup_dir})")

    # ───────── STEP 3: SCAN FOR ISSUES ─────────
    reg_issues: list[dict] = []
    app_path_issues: list[dict] = []
    env_issues: dict = {"user": [], "system": []}
    shortcut_issues: list[dict] = []
    temp_info: dict = {"dirs": []}

    with Throbber().context("Scanning for issues...") as update_label:
        if selected.get("registry"):
            update_label("Scanning registry uninstall entries...")
            reg_issues = scan_registry_uninstall()
            update_label("Scanning registry App Paths...")
            app_path_issues = scan_registry_app_paths()

        if selected.get("envvars"):
            update_label("Scanning environment variables...")
            env_issues = scan_env_vars()

        if selected.get("shortcuts"):
            update_label("Scanning shortcut files...")
            shortcut_issues = scan_shortcuts()

        if selected.get("temp"):
            update_label("Scanning temp directories...")
            temp_info = scan_temp_files()

    # CHECK IF ANYTHING WAS FOUND
    total_issues = (
        len(reg_issues) + len(app_path_issues)
        + len(env_issues.get("user", [])) + len(env_issues.get("system", []))
        + sum(len(loc["broken_shortcuts"]) for loc in shortcut_issues)
        + len(temp_info.get("dirs", []))
    )

    if total_issues == 0:
        Console.done("No issues found! Your system paths look clean.", start="\n", end="\n\n")
        return

    FormatCodes.print(f"\n[b](Found [br:yellow]({total_issues}) issue(s) to address.)")

    # ───────── STEP 4: SHOW SUMMARY & CONFIRM ─────────
    show_summary(reg_issues, app_path_issues, env_issues, shortcut_issues, temp_info, selected)

    if not Console.confirm("[b](Proceed with cleanup?)", default_is_yes=False):
        Console.exit("Cleanup canceled.", start="\n", end="\n\n", exit_code=0)
        return

    # ───────── STEP 5: EXECUTE CLEANUP ─────────
    FormatCodes.print("\n[b|bg:black]( EXECUTING CLEANUP )")

    all_failures: list[str] = []

    if selected.get("registry") and (reg_issues or app_path_issues):
        all_failures.extend(execute_registry_cleanup(reg_issues, app_path_issues))

    if selected.get("envvars") and (env_issues.get("user") or env_issues.get("system")):
        all_failures.extend(execute_env_cleanup(env_issues))

    if selected.get("shortcuts") and shortcut_issues:
        all_failures.extend(execute_shortcut_cleanup(shortcut_issues))

    if selected.get("temp") and temp_info.get("dirs"):
        all_failures.extend(execute_temp_cleanup(temp_info))

    # ───────── STEP 6: FINAL REPORT ─────────
    print()
    if not all_failures:
        Console.done("Cleanup completed successfully!", end="\n")
        FormatCodes.print(f"  [dim](Backups are at: [br:cyan]({backup_dir}))\n")
    else:
        Console.warn(
            f"Cleanup completed with [b|red]({len(all_failures)}) failure(s).",
            end="\n",
        )
        FormatCodes.print("[b](Failed operations:)")
        for msg in all_failures:
            FormatCodes.print(f"  [red](✗) [dim]({msg})")
        FormatCodes.print(f"\n  [dim](Backups are at: [br:cyan]({backup_dir}))\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        FormatCodes.print("\n[b|red](✗ Canceled by user.)\n")
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
