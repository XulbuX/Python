#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""Lets you quickly generate QR codes directly within the terminal."""

import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import qrcode
from xulbux import Console, FormatCodes
from xulbux.base.consts import COLOR
from xulbux.console import ParsedArgs, Throbber

ARGS = Console.get_args(
    {
        "text": "before",
        "invert": {"-i", "--invert"},
        "scale": {"-s", "--scale"},
        "error_correction": {"-e", "--error"},
        "contact": {"-c", "--contact"},
        "wifi": {"-w", "--wifi"},
        "help": {"-h", "--help"},
    }
)


def print_help() -> None:
    help_text = """
[b|in|bg:black]( QR Code Generator — Quickly generate QR codes directly within the terminal )

[b](Usage:) [br:green](x-qr) [br:cyan](<text>) [br:blue]([options])

[b](Arguments:)
  [br:cyan](text)                 Text to encode in QR code

[b](Options:)
  [br:blue](-i), [br:blue](--invert)         Invert colors [dim]((swap filled/empty blocks))
  [br:blue](-s), [br:blue](--scale[dim](=)N)        Scale factor for output size [dim]((default: 1))
  [br:blue](-e), [br:blue](--error[dim](=)LEVEL)    Error correction level [dim]((L, M, Q, H — default: M))
  [br:blue](-c), [br:blue](--contact)        Generate contact QR code [dim]((vCard format))
  [br:blue](-w), [br:blue](--wifi)           Generate WiFi QR code [dim]((auto-detect or manual))

[b](Examples:)
  [br:green](x-qr) [br:cyan]("Hello World")                      [dim](# [i](QR code which contains simple text))
  [br:green](x-qr) [br:cyan]("https://example.com") [br:blue](--scale[dim](=)2)    [dim](# [i](Larger QR code))
  [br:green](x-qr) [br:cyan]("John Doe") [br:blue](--contact)               [dim](# [i](Contact QR code))
  [br:green](x-qr) [br:cyan]("MyNetwork") [br:blue](--wifi)                 [dim](# [i](WiFi QR code))
  [br:green](x-qr) [br:blue](--wifi)                             [dim](# [i](WiFi QR code for detected networks))
"""
    FormatCodes.print(help_text)


def phone_validator(user_input: str) -> str | None:
    """Validate phone number format."""

    if user_input and not re.match(r"[\d\s+()-./x]+", user_input):
        return "Enter a valid phone number (+99123456789)"


def email_validator(user_input: str) -> str | None:
    """Validate email address format."""

    if not re.match(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", user_input):
        return "Enter a valid E-Mail address (example@domain.com)"


class VCard:
    def __init__(self, vcard_str: str) -> None:
        self.vcard_str = vcard_str
        self.details = self.get_vcard_details()

    def get_vcard_details(self) -> dict[str, str]:
        """Parse vCard string and extract details."""

        lines = self.vcard_str.strip().split("\n")
        details = {"name": "", "phone": "", "email": ""}

        if self.vcard_str.strip().startswith("BEGIN:VCARD") and self.vcard_str.strip().endswith("END:VCARD"):
            for line in lines:
                line = line.strip()
                if line.startswith("FN:"):
                    details["name"] = line[3:]
                elif line.startswith("TEL:"):
                    details["phone"] = line[4:]
                elif line.startswith("EMAIL:"):
                    details["email"] = line[6:]
        else:
            details["name"] = self.vcard_str.strip()

        if not details["name"]:
            details["name"] = Console.input("Name (required): ").strip()
            if not details["name"]:
                raise ValueError("Name is required for contact QR code.")
        if not details["phone"]:
            details["phone"] = Console.input("Phone number: ", validator=phone_validator).strip()
        if not details["email"]:
            details["email"] = Console.input("Email: ", validator=email_validator).strip()

        return details

    def get_vcard_str(self) -> str:
        """Generate vCard string from details."""

        vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{self.details['name']}\n"

        if self.details["phone"]:
            vcard += f"TEL:{self.details['phone']}\n"
        if self.details["email"]:
            vcard += f"EMAIL:{self.details['email']}\n"
        vcard += "END:VCARD"

        return vcard

    def get_display_info(self) -> str:
        """Get formatted display information."""

        info = self.details
        display = f"Name: {info['name']}\n"

        if info["phone"]:
            display += f"Phone: {info['phone']}\n"
        if info["email"]:
            display += f"Email: {info['email']}\n"

        return display.strip()


class WiFi:
    def __init__(self, network_name: str = "") -> None:
        self.network_name = network_name.strip()
        self.wifi_info = self._get_wifi_info()

    def _get_saved_profiles(self) -> list[str]:
        """Get list of saved WiFi profiles."""

        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "profiles"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=10,
            )

            profiles: list[str] = []
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "All User Profile" in line:
                        ssid = line.split(":", 1)[1].strip()
                        profiles.append(ssid)
            return profiles

        except Exception:
            return []

    def _get_current_network(self) -> str | None:
        """Try to detect current WiFi network."""

        for method in [
            'netsh wlan show interfaces | findstr /i "SSID"',
            '(Get-NetConnectionProfile | Where-Object {$_.NetworkCategory -ne "DomainAuthenticated"}).Name',
        ]:
            try:
                if method.startswith("netsh"):
                    result = subprocess.run(
                        method, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=10
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split("\n"):
                            if "SSID" in line and "BSSID" not in line:
                                return line.split(":", 1)[1].strip()

                else:
                    result = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", method],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
                        timeout=10,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()

            except Exception:
                continue

        return None

    def _try_get_password(self, ssid: str) -> str | None:
        """Try multiple methods to get WiFi password."""

        # XML export
        password = self._export_xml_method(ssid)
        if password:
            Console.done("Retrieved password using XML export method")
            return password
        # Direct netsh variations
        password = self._netsh_variations(ssid)
        if password:
            Console.done("Retrieved password using netsh method")
            return password
        return None

    def _export_xml_method(self, ssid: str) -> str | None:
        """Try to get password by exporting profile to XML."""

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                result = subprocess.run(
                    ["netsh", "wlan", "export", "profile", f"name={ssid}", f"folder={temp_dir}", "key=clear"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=15,
                )

                if result.returncode == 0:
                    for file_item in Path(temp_dir).iterdir():
                        if file_item.suffix == ".xml":
                            try:
                                for elem in ET.parse(file_item).getroot().iter():
                                    if elem.tag.endswith("keyMaterial") and elem.text:
                                        return elem.text
                            except ET.ParseError:
                                continue

        except Exception:
            pass

        return None

    def _netsh_variations(self, ssid: str) -> str | None:
        """Try different netsh command variations."""

        for cmd in [
            f'netsh wlan show profile "{ssid}" key=clear',
            f'netsh wlan show profile name="{ssid}" key=clear',
            f"netsh wlan show profile {ssid} key=clear",
        ]:
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if any(keyword in line for keyword in ["Key Content", "Schlüsselinhalt"]):
                            password = line.split(":", 1)[1].strip()
                            if password:
                                return password

            except Exception:
                continue

        return None

    def _get_security_type(self, ssid: str) -> str:
        """Determine the security type of the network."""

        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "profile", ssid],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Authentication" in line:
                        auth = line.split(":", 1)[1].strip().upper()
                        if any(wpa in auth for wpa in ["WPA2", "WPA3", "WPA"]):
                            return "WPA"
                        elif "WEP" in auth:
                            return "WEP"
                        elif "OPEN" in auth:
                            return "nopass"

        except Exception:
            pass

        return "WPA"

    def _prompt_for_details(self) -> dict[str, str | bool]:
        """Prompt user for WiFi details, trying to auto-detect if possible."""

        with Throbber().context():
            profiles = self._get_saved_profiles()
            current = (self._get_current_network() or "").replace("\n", " ").strip()

        if profiles:
            FormatCodes.print(f"[b](Found {len(profiles)} saved networks:)")
            for i, profile in enumerate(profiles, 1):
                current_marker = " [br:yellow](current)" if profile == current else ""
                FormatCodes.print(f" [white]({i:2d}) {profile}{current_marker}")

        if not self.network_name:
            if current and Console.confirm(f"\nUse current network [br:cyan]({current})?"):
                self.network_name = current

            if not self.network_name:
                if profiles:
                    choice = Console.input(
                        f"Enter network number (1-{len(profiles)}) or network name: ", min_len=1, max_len=32
                    ).strip()

                    if choice.replace("_", "").isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(profiles):
                            self.network_name = profiles[idx]
                        else:
                            Console.warn(f"Invalid number. Please choose between 1 and {len(profiles)}.")
                            self.network_name = Console.input(
                                "Enter WiFi network name (SSID): ", min_len=1, max_len=32
                            ).strip()
                    else:
                        self.network_name = choice
                else:
                    self.network_name = Console.input("Enter WiFi network name (SSID): ", min_len=1, max_len=32).strip()

        if not self.network_name:
            raise ValueError("Network name is required for WiFi QR code.")

        Console.info(f"Attempting to retrieve password for '{self.network_name}'...", start="\n")
        password = self._try_get_password(self.network_name)

        if not password:
            Console.warn("Could not retrieve password automatically.", end="\n\n")
            Console.log_box_bordered(
                "[b](Antivirus alert? Safe to ignore:)",
                "It's likely because we tried to",
                "read a saved WiFi password.",
                border_style=f"dim|{COLOR.ORANGE}",
                default_color=COLOR.ORANGE,
                indent=2,
            )
            password = Console.input(
                f"Enter password for '{self.network_name}': ", start="\n", mask_char="*", min_len=8, max_len=64
            ).strip()
            if not password:
                raise ValueError("Password is required for WiFi QR code.")

        security = self._get_security_type(self.network_name)

        hidden = Console.confirm("Is this a hidden network?", start=("\n" if password else ""), default_is_yes=False)

        return {"ssid": self.network_name, "password": password, "security": security, "hidden": hidden}

    def _get_wifi_info(self) -> dict[str, str | bool]:
        """Get WiFi information either from input or by detection."""

        try:
            return self._prompt_for_details()

        except (KeyboardInterrupt, ValueError) as exc:
            if isinstance(exc, ValueError):
                raise exc
            else:
                raise KeyboardInterrupt() from exc

    def get_wifi_string(self) -> str:
        """Generate WiFi QR code string."""

        info = self.wifi_info
        return f"WIFI:T:{info['security']};S:{info['ssid']};P:{info['password']};H:{'true' if info['hidden'] else 'false'};;"

    def get_display_info(self) -> str:
        """Get formatted display information."""

        info = self.wifi_info
        display = f"Network: {info['ssid']}\n"
        display += "Password: **********\n"
        display += f"Security: {info['security']}\n"
        display += f"Hidden: {'Yes' if info['hidden'] else 'No'}"

        return display


def ascii_qr(text: str, args: ParsedArgs) -> str | None:  # noqa: C901
    """Generate and display QR code in terminal."""

    try:
        scale = int(v) if (v := args.scale.get(0)) and v.replace("_", "").isdigit() else 1
        invert = args.invert.exists
        error_level = int(
            {
                "L": qrcode.constants.ERROR_CORRECT_L,  # type: ignore[name-defined]
                "M": qrcode.constants.ERROR_CORRECT_M,  # type: ignore[name-defined]
                "Q": qrcode.constants.ERROR_CORRECT_Q,  # type: ignore[name-defined]
                "H": qrcode.constants.ERROR_CORRECT_H,  # type: ignore[name-defined]
            }.get(
                ((args.error_correction.values or [None])[0] or "M").upper(),
                qrcode.constants.ERROR_CORRECT_M,  # type: ignore[name-defined]
            )
        )

        qr = qrcode.QRCode(version=1, error_correction=error_level, box_size=1, border=0)
        qr.add_data(text)

        try:
            qr.make(fit=True)
        except ValueError as exc:
            if "Invalid version" in (err_str := str(exc)) or "expected 1 to 40" in err_str:
                raise ValueError(
                    f"Cannot fit {len(text)} characters into a QR code.\n"
                    f"Please reduce the amount of data or try a lower error correction level ([br:blue](-e L))."
                ) from exc
            raise

        matrix = qr.get_matrix()
        lines: list[str] = []

        if scale == 1:
            for i in range(0, len(matrix), 2):
                line = ""
                upper_row = matrix[i]
                lower_row = matrix[i + 1] if i + 1 < len(matrix) else None
                for j in range(len(upper_row)):
                    upper_filled = upper_row[j]
                    lower_filled = lower_row[j] if lower_row is not None else False
                    if invert:
                        upper_filled = not upper_filled
                        lower_filled = (not lower_filled) if lower_row is not None else False
                    if upper_filled and lower_filled:
                        char = "█"
                    elif upper_filled:
                        char = "▀"
                    elif lower_filled:
                        char = "▄"
                    else:
                        char = " "
                    line += char
                lines.append(line)

        else:
            chars = ("  ", "██") if invert else ("██", "  ")
            for row in matrix:
                line = ""
                for cell in row:
                    char = chars[0] if cell else chars[1]
                    line += char * (scale - 1)
                for _ in range(scale - 1):
                    lines.append(line)

        return "  " + "\n  ".join(lines)

    except ValueError as exc:
        Console.fail(exc)


def main() -> None:
    if ARGS.help.exists or not (ARGS.text.exists or ARGS.wifi.exists or ARGS.contact.exists):
        print_help()
        return

    print()
    text = " ".join(ARGS.text.values)

    if ARGS.wifi.exists:
        wifi = WiFi(text)
        text = wifi.get_wifi_string()

        print(f"\n\n{ascii_qr(text, ARGS)}\n")
        Console.info(f"[b](WiFi Details:)\n[white]{wifi.get_display_info()}[_c]", end="\n\n")

    elif ARGS.contact.exists:
        vcard = VCard(text)
        text = vcard.get_vcard_str()

        print(f"\n\n{ascii_qr(text, ARGS)}\n")
        Console.info(f"[b](Contact Details:)\n[white]{vcard.get_display_info()}[_c]", end="\n\n")

    else:
        print(f"\n\n{ascii_qr(text, ARGS)}\n")
        Console.info(f"[b](Encoded Text:)\n[white]{text}[_c]", end="\n\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
