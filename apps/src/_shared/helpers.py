from pathlib import Path
from typing import Any, Optional
from PIL import Image, ImageTk
import tkinter.font as tkfont
import subprocess
import tempfile
import ctypes
import sys


def get_system_theme() -> str:
    """Get the system appearance as `"light"` or `"dark"`, falling back to dark."""
    try:
        if sys.platform == "win32":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value == 1 else "dark"

        elif sys.platform == "darwin":
            result = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True, text=True)
            return "dark" if result.stdout.strip().lower() == "dark" else "light"

        else:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True,
                text=True,
            )
            return "dark" if "dark" in result.stdout.lower() else "light"

    except Exception:
        return "dark"


def resolve_mono_font(size: int) -> tuple[str, int]:
    """Return the first available modern monospace font, falling back to Courier New."""
    for name in ["Cascadia Code", "Cascadia Mono", "Consolas", "JetBrains Mono", "Fira Code", "Source Code Pro",
                 "Courier New"]:
        if name in set(tkfont.families()):
            return (name, size)

    return ("Courier New", size)


def setup_window_icon(window: Any, icon_png: Path) -> Optional[Path]:
    """Set the window and taskbar icon from a PNG file."""
    if not icon_png.is_file():
        return None

    pil_icon: Image.Image = Image.open(str(icon_png))

    if sys.platform == "win32":
        ico_tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
        ico_tmp.close()
        pil_icon.save(ico_tmp.name, format="ICO", sizes=[(512, 512), (256, 256), (128, 128), (64, 64)])
        ico_path: Path = Path(ico_tmp.name)

        try:
            window.iconbitmap(str(ico_path))
        except Exception:
            pass

        # ALSO PUSH VIA WIN32 API AFTER RENDERING, COVERING ANY TASKBAR REFRESH EDGE CASES
        def _apply_win32() -> None:
            if not ico_path.exists():
                return
            try:
                GA_ROOT = 2
                LR_LOADFROMFILE = 0x10
                IMAGE_ICON = 1
                WM_SETICON = 0x80
                ICON_SMALL = 0
                ICON_BIG = 1
                user32 = ctypes.windll.user32
                inner_hwnd = window.winfo_id()
                hwnd = user32.GetAncestor(inner_hwnd, GA_ROOT) or inner_hwnd
                sm_cx_icon = user32.GetSystemMetrics(11)  # SM_CXICON
                sm_cy_icon = user32.GetSystemMetrics(12)  # SM_CYICON
                sm_cx_small = user32.GetSystemMetrics(49)  # SM_CXSMICON
                sm_cy_small = user32.GetSystemMetrics(50)  # SM_CYSMICON
                hicon_big = user32.LoadImageW(None, str(ico_path), IMAGE_ICON, sm_cx_icon, sm_cy_icon, LR_LOADFROMFILE)
                hicon_small = user32.LoadImageW(None, str(ico_path), IMAGE_ICON, sm_cx_small, sm_cy_small, LR_LOADFROMFILE)
                if hicon_big:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                if hicon_small:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
            except Exception:
                pass

        _apply_win32()
        window.after(201, _apply_win32)
        return ico_path

    else:
        icon_photo: ImageTk.PhotoImage = ImageTk.PhotoImage(pil_icon)
        window._icon_photo = icon_photo  # PREVENT GARBAGE COLLECTION
        window.after(201, lambda: window.wm_iconphoto(True, icon_photo))

    return None
