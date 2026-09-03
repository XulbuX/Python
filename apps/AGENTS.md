# Agent Guidelines for Desktop Apps (`apps/`)

When modifying or adding desktop apps under `apps/`, all agents must strictly follow these rules in addition to the root `AGENTS.md`.

---

## 1. Shared-Code First & Cross-App Propagation

*   **Move Reusable Code to `_shared`:** Any fix, utility function, external tool helper, or custom UI widget that is relevant to more than one desktop app **MUST** be placed in `apps/src/_shared/` (such as `_shared/helpers.py`, `_shared/widgets.py`, `_shared/consts.py`), rather than kept isolated inside a single app.
*   **Audit All Other Apps:** Whenever a bug is resolved, an external tool flag is updated, or an improvement is implemented in one app or in shared code, you **MUST immediately inspect all other apps** in `apps/src/` to verify whether the same fix or improvement applies there.
*   **Fix Directly:** If any other app is affected or can benefit from the improvement, apply the changes to all affected apps directly in the same editing turn. Never leave other apps with known defects, obsolete CLI parameters, or duplicated code.

---

## 2. Architecture & Module Separation

Every app in `apps/src/<app_name>/` must maintain strict separation of concerns:

*   **`app.pyw`:** Main application entry point (`.pyw` for silent execution on Windows). Handles UI structure, event wiring, and state coordination only.
*   **`consts.py`:** Pure declarations for constants, asset paths, type definitions (`TypedDict`, `IntEnum`), file dialog filters, and static lookup tables.
*   **`helpers.py`:** Pure, non-GUI helper functions (validation, data/string/time parsing and formatting). Must be testable without Tkinter.
*   **`widgets.py`:** (Optional) Custom Canvas or composite UI widgets specific to the app.
*   **`exporter.py` / `worker.py`:** (Optional) Subprocess management or background processing logic. Communicates with UI exclusively through thread-safe callbacks.
*   **`assets/img/`:** Houses vector sources (`.ai`, `.svg`) and a 512×512 high-resolution app icon PNG (`<app-name>.png`, named in kebab-case matching the shared icons).
*   **Launchers:** Each app must provide a silent Windows launcher (`apps/<app-name>.vbs`) and a Unix launcher (`apps/<app-name>.sh`).

---

## 3. Imports & `sys.path` Standards

Always insert `apps/src` at index 0 of `sys.path` at the top of each `app.pyw`, and use dual imports (runtime absolute, type-checking relative) for `_shared`:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

## 4. Subprocesses & Binary Resolution

*   **Binary Resolution:** Always use `resolve_binary()` from `_shared.helpers` to locate CLI binaries (`ffmpeg`, `ffprobe`, `exiftool`). Never use bare `shutil.which()`.
*   **Non-blocking Verification:** Verify external binaries in background daemon threads on startup (`_verify_<tool>`), keeping UI launch instantaneous.
*   **No Flashing Consoles:** Pass `**POPEN_FLAGS` to all `subprocess.run` and `subprocess.Popen` calls to ensure `CREATE_NO_WINDOW` is set on Windows.
*   **Thread Safety:** Never block the main Tkinter thread with heavy I/O or subprocess polling. Dispatch updates onto the main loop using `self.after(0, ...)`.
*   **Process Cleanup:** Retain references to in-flight `subprocess.Popen` instances and kill them (`proc.kill()`) when switching files or closing the window.

---

## 5. UI Design & Component Consistency

*   **Centered Fixed Window:** Compute centered window coordinates upon initialization (`(sw - ww) // 2`, `(sh - wh) // 2`).
*   **Window Icon:** Always call `setup_window_icon(self, APP_ICON_PNG)` from `_shared.helpers` in `__init__`.
*   **Dynamic Theme Polling:** Use the semantic `COLORS` palette and poll system appearance periodically via `self.after(1000, self._poll_theme)` using `get_system_theme()`.
*   **Standard Widgets:**
    *   Use `SingleLineEntry` and `MultilineEntry` from `_shared.widgets` instead of bare `CTkEntry` / `CTkTextbox` for reliable placeholder management and newline-cleaned clipboard pasting.
    *   Use `SpinnerButton` for asynchronous action buttons.
    *   Use `render_svg_icon(name, size, color)` for SVG icon rendering at 4× logical size for crisp HiDPI displays.
