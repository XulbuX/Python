---
name: apps
description: Architecture, guidelines, design conventions, and shared-code standards for desktop apps in the apps/ directory.
---

# apps

Guidelines, architecture conventions, and quality standards for all desktop applications in `apps/`.

---

## 1. Shared-Code First & Cross-App Propagation

*   **Move to Shared Code:** If a fix, helper function, utility, UI widget, or constant is created or modified that could apply to more than one app, it **MUST** be placed in `apps/src/_shared/` (e.g., `_shared/helpers.py`, `_shared/widgets.py`, `_shared/consts.py`), rather than kept inside an app-specific module.
*   **Audit All Other Apps:** Whenever a bug is fixed, an external tool option is adjusted, or an improvement is made in shared code or in one app, you **MUST immediately inspect all other apps** in `apps/src/` to determine whether the exact same issue, outdated pattern, or opportunity for improvement applies there.
*   **Fix Directly:** If any other app is affected or can benefit from the improvement, apply the fix to all affected apps directly in the same edit session. Never leave another app with known bugs, outdated tool options, or duplicated code.

---

## 2. Directory Layout & App Structure

Every desktop app in `apps/src/<app_name>/` must follow this standardized layout:

```text
apps/
├── <app-name>.sh                     # Unix shell launcher
├── <app-name>.vbs                    # Windows silent VBScript launcher
└── src/
    ├── _shared/                      # Shared widgets, helpers, constants, and icons
    │   ├── assets/icons/*.svg        # Shared SVG icons
    │   ├── consts.py                 # Palette (COLORS), POPEN_FLAGS, ICONS lookup
    │   ├── helpers.py                # get_system_theme, resolve_binary, resolve_mono_font, setup_window_icon
    │   └── widgets.py                # SingleLineEntry, MultilineEntry, SpinnerButton, render_svg_icon
    └── <app_name>/
        ├── app.pyw                   # Main application entry point (uses .pyw for no-console launch)
        ├── consts.py                 # App-specific constants, asset paths, TypedDicts, Enums, file filters
        ├── helpers.py                # Pure non-GUI helper functions (validation, parsing, formatting)
        ├── widgets.py                # (Optional) App-specific custom Canvas / UI widgets
        ├── exporter.py / worker.py   # (Optional) Background thread worker or process manager
        └── assets/img/
            ├── <app-name>.ai         # Vector master (kebab-case)
            ├── <app-name>.svg        # Vector icon (kebab-case)
            └── <app-name>.png        # 512×512 high-resolution icon PNG (kebab-case)
```

### Launchers

*   **Windows (`<app-name>.vbs`):** Must silently invoke the app via `py` without opening a command prompt window:

    ```vbscript
    Dim shell, fso, dir
    Set shell = CreateObject("WScript.Shell")
    Set fso = CreateObject("Scripting.FileSystemObject")
    dir = fso.GetParentFolderName(WScript.ScriptFullName)
    shell.Run "py """ & dir & "\src\<app_name>\app.pyw""", 0, False
    ```

*   **Unix (`<app-name>.sh`):** Must launch in background and disown:

    ```bash
    #!/bin/bash
    DIR="$(cd "$(dirname "$0")" && pwd)"
    python3 "$DIR/src/<app_name>/app.pyw" &
    disown
    ```

---

## 3. Module Roles & Separation of Concerns

*   **`app.pyw`:** Responsible strictly for GUI layout, event wiring, state management, and UI orchestration.
*   **`consts.py`:** Holds all constants, asset paths, type definitions (`TypedDict`, `IntEnum`), file dialog filters, and static mappings. No runtime business logic.
*   **`helpers.py`:** Pure, non-GUI helper functions (date parsing, time conversions, validation). Easily unit-testable without importing GUI toolkits.
*   **`widgets.py`:** Dedicated custom Canvas or Composite widgets.
*   **`exporter.py` / `worker.py`:** Heavy file operations or CLI invocations run in background threads. Communicates status and progress via callbacks.

---

## 4. Shared Imports & `sys.path` Convention

Because apps can be executed directly as scripts (`py src/<app_name>/app.pyw`) or imported during testing, each `app.pyw` must dynamically add `apps/src` to `sys.path` at the very top:

```python
# Make the `_shared` package (apps/src/_shared) importable when running this script directly:
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Shared; absolute imports during runtime, relative ones during development so the types are linked correctly in the IDE:
from _shared.consts import COLORS, POPEN_FLAGS
from _shared.helpers import get_system_theme, resolve_binary, resolve_mono_font, setup_window_icon
from _shared.widgets import SingleLineEntry, SpinnerButton, render_svg_icon

if TYPE_CHECKING:
    from .._shared.consts import COLORS, POPEN_FLAGS  # ruff:ignore[runtime-import-in-type-checking-block]
    from .._shared.helpers import (  # ruff:ignore[runtime-import-in-type-checking-block]
        get_system_theme,
        resolve_binary,
        resolve_mono_font,
        setup_window_icon,
    )
    from .._shared.widgets import (  # ruff:ignore[runtime-import-in-type-checking-block]
        SingleLineEntry,
        SpinnerButton,
        render_svg_icon,
    )
```

---

## 5. Subprocess Execution & Binary Resolution

*   **Binary Resolution:** Always resolve external CLI binaries (`ffmpeg`, `ffprobe`, `exiftool`) using `resolve_binary()` from `_shared.helpers`. Never use bare `shutil.which()`. `resolve_binary()` checks standard `PATH`, WinGet links (`%LOCALAPPDATA%\Microsoft\WinGet\Links`), Local AppData programs, Program Files, and standard Unix paths (`/usr/local/bin`, `/opt/homebrew/bin`).
*   **Startup Verification:** Verify tool availability in a background daemon thread (`_verify_<tool>`) during initialization. Never block the UI thread during startup. Update button states or display informative banners when tools are missing.
*   **No Flashing Consoles:** All subprocess calls (`subprocess.run`, `subprocess.Popen`) **MUST** pass `**POPEN_FLAGS` imported from `_shared.consts` to set `CREATE_NO_WINDOW` on Windows.
*   **Thread Safety:** Never run blocking operations or subprocesses on the main Tkinter thread. Subprocess monitoring must run in daemon threads, marshalling UI updates back to Tkinter via `self.after(0, ...)`.
*   **Clean Cancellation:** Keep reference to running `subprocess.Popen` processes (e.g., `self._proc`) and kill them (`proc.kill()`) when switching files or closing the application.

---

## 6. UI & Design Language Standards

*   **Window Geometry:** Center fixed-size windows on startup:

    ```python
    ww, wh = 820, 520
    self.update_idletasks()
    sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
    self.geometry(f"{ww}x{wh}+{(sw - ww) // 2}+{(sh - wh) // 2}")
    ```

*   **Window & Taskbar Icon:** Always call `self._temp_ico_path = setup_window_icon(self, APP_ICON_PNG)` from `_shared.helpers` during `__init__`.
*   **Dynamic Theme Polling:** Use the semantic `COLORS` palette from `_shared.consts`. Implement periodic theme checking:

    ```python
    self.after(1000, self._poll_theme)
    ```

    Call `apply_colors()` or refresh UI elements when `get_system_theme()` differs from `self._current_theme`.
*   **Shared UI Widgets:**
    *   Use `SingleLineEntry` and `MultilineEntry` from `_shared.widgets` instead of bare `CTkEntry` / `CTkTextbox` for reliable placeholder management and newline-cleaned clipboard pasting.
    *   Use `SpinnerButton` for async action buttons.
    *   Use `render_svg_icon(name, size, color)` to render SVG icons at 4× resolution for crisp HiDPI displays.
