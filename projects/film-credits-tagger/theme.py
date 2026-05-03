import tkinter.font as tkfont
import subprocess
import sys


COLORS: dict[str, dict[str, str]] = {
    "dark": {
        "background": "#09090B",
        "foreground": "#FAFAFA",
        "muted_foreground": "#A1A1AA",
        "placeholder_foreground": "#52525B",
        "border": "#27272A",
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "primary_foreground": "#FFFFFF",
        "secondary": "#09090B",
        "secondary_hover": "#27272A",
        "secondary_border": "#3F3F46",
        "secondary_foreground": "#FAFAFA",
        "card": "#FAFAFA",
        "card_hover": "#E4E4E7",
        "card_foreground": "#09090B",
        "destructive": "#290D0D",
        "destructive_border": "#7F1D1D",
        "destructive_foreground": "#FFDEDE",
        "destructive_muted": "#FCA5A5",
        "link": "#60A5FA",
    },
    "light": {
        "background": "#FFFFFF",
        "foreground": "#09090B",
        "muted_foreground": "#71717A",
        "placeholder_foreground": "#A1A1AA",
        "border": "#F0F0F2",
        "primary": "#2563EB",
        "primary_hover": "#1D4ED8",
        "primary_foreground": "#FFFFFF",
        "secondary": "#FFFFFF",
        "secondary_hover": "#F4F4F5",
        "secondary_border": "#E0E0E3",
        "secondary_foreground": "#18181B",
        "card": "#18181B",
        "card_hover": "#3F3F46",
        "card_foreground": "#FAFAFA",
        "destructive": "#FFEBEB",
        "destructive_border": "#FCA5A5",
        "destructive_foreground": "#7F1D1D",
        "destructive_muted": "#B91C1C",
        "link": "#2563EB",
    },
}


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
