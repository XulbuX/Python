"""Generate QR codes in the terminal using ASCII characters.
Outputs QR codes directly to console using block characters."""
# pip install qrcode xulbux
from xulbux import FormatCodes, Console
from xulbux.xx_console import Args
from typing import Optional, cast
import qrcode


FIND_ARGS = {
    "text": "before",
    "invert": ["-i", "--invert"],
    "scale": ["-s", "--scale"],
    "error_correction": ["-e", "--error"],
    "contact": ["-c", "--contact"],
}


def print_help():
    help_text = """
[b|in]( QR Code Generator - Quickly Generate QR codes directly within the terminal )

[b](Usage:) [br:green](x-qr) [br:cyan](<text>) [br:blue]([options])

[b](Arguments:)
  [br:cyan](text)                 Text to encode in QR code

[b](Options:)
  [br:blue](-i), [br:blue](--invert)         Invert colors [dim]((swap filled/empty blocks))
  [br:blue](-s), [br:blue](--scale N)        Scale factor for output size [dim]((default: 1))
  [br:blue](-e), [br:blue](--error LEVEL)    Error correction level [dim]((L, M, Q, H - default: M))
  [br:blue](-c), [br:blue](--contact)        Generate contact QR code [dim]((vCard format))

[b](Examples:)
  [br:green](x-qr) [br:cyan]("Hello World")
  [br:green](x-qr) [br:cyan]("https://example.com") [br:blue](--scale 2)\
"""
    FormatCodes.print(help_text)


def get_vcard_details(input_text: str) -> dict:
    lines = input_text.strip().split('\n')
    details = {"name": "", "phone": "", "email": ""}

    if input_text.strip().startswith("BEGIN:VCARD") and input_text.strip().endswith("END:VCARD"):
        for line in lines:
            line = line.strip()
            if line.startswith("FN:"):
                details["name"] = line[3:]
            elif line.startswith("TEL:"):
                details["phone"] = line[4:]
            elif line.startswith("EMAIL:"):
                details["email"] = line[6:]
    else:
        details["name"] = input_text.strip()

    if not details["name"]:
        details["name"] = input("Name (required): ").strip()
        if not details["name"]:
            raise ValueError("Name is required for contact QR code.")
    if not details["phone"]:
        details["phone"] = input("Phone number: ").strip()
    if not details["email"]:
        details["email"] = input("Email: ").strip()

    return details


def format_contact_qr(name: str, phone: str = "", email: str = ""):
    """Format text for contact QR code (basic vCard)."""
    vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\n"
    if phone: vcard += f"TEL:{phone}\n"
    if email: vcard += f"EMAIL:{email}\n"
    vcard += "END:VCARD"
    return vcard


def ascii_qr(text: str, args: Args) -> Optional[str]:
    """Generate and display QR code in terminal."""
    try:
        scale = int(args.scale.value) if args.scale.value else 1
        invert = args.invert.exists
        error_level = {
            'L': qrcode.constants.ERROR_CORRECT_L,  # type: ignore[name-defined]
            'M': qrcode.constants.ERROR_CORRECT_M,  # type: ignore[name-defined]
            'Q': qrcode.constants.ERROR_CORRECT_Q,  # type: ignore[name-defined]
            'H': qrcode.constants.ERROR_CORRECT_H,  # type: ignore[name-defined]
        }.get((args.error_correction.value or "M").upper(), qrcode.constants.ERROR_CORRECT_M)  # type: ignore[name-defined]

        qr = qrcode.QRCode(version=1, error_correction=error_level, box_size=1, border=0)
        qr.add_data(text)
        qr.make(fit=True)

        matrix = qr.get_matrix()
        lines = []

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

    except ValueError as e:
        Console.fail(f"Invalid argument: {e}")


def main(args: Args) -> None:
    text = cast(str, " ".join(args.text.value))

    if args.contact.exists:
        details = get_vcard_details(text)
        text = format_contact_qr(details["name"], details["phone"], details["email"])

    elif not text:
        print_help()
        return

    print(f"\n{ascii_qr(text, args)}\n")
    Console.info(f"[b](Encoded Text:)\n[white]{text}[_c]")


if __name__ == "__main__":
    try:
        main(Console.get_args(FIND_ARGS))
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
