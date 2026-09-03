import os
import subprocess
import time


def shutdown(message: str = "WARNING: Virus detected. Starting system cleanup process...", delay: int = 5) -> None:
    """Trigger a system shutdown with an alarming warning message across supported operating systems."""

    if (os_type := os.name) == "nt":
        subprocess.run(["shutdown", "/s", "/f", "/t", str(delay), "/c", message])
    elif os_type == "posix":
        if "darwin" in os.uname().sysname.lower():  # pyright:ignore[reportAttributeAccessIssue,reportUnknownMemberType]
            subprocess.run(["sudo", "shutdown", "-h", f"+{delay // 60}", message])
        else:
            subprocess.run(["sudo", "shutdown", "-h", f"+{delay // 60}", message])
    else:
        print(f"Shutdown not supported on this OS: {os_type}")
    time.sleep(delay)


if __name__ == "__main__":
    shutdown()
