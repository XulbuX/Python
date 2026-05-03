import tkinter.font as tkfont
import subprocess
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
    preferred = ["Cascadia Code", "Cascadia Mono", "Consolas", "JetBrains Mono", "Fira Code", "Source Code Pro", "Courier New"]
    available = set(tkfont.families())
    for name in preferred:
        if name in available:
            return (name, size)
    return ("Courier New", size)
