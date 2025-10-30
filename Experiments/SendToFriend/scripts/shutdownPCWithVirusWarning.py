import subprocess
import time
import os


def shutdown(message="WARNING: Virus detected. Starting system cleanup process...", delay=5):
    os_type = os.name
    if os_type == "nt":
        subprocess.run(["shutdown", "/s", "/f", "/t", str(delay), "/c", message])
    elif os_type == "posix":
        if "darwin" in os.uname().sysname.lower():
            subprocess.run(["sudo", "shutdown", "-h", f"+{delay//60}", message])
        else:
            subprocess.run(["sudo", "shutdown", "-h", f"+{delay//60}", message])
    else:
        print(f"Shutdown not supported on this OS: {os_type}")
    time.sleep(delay)


if __name__ == "__main__":
    shutdown()
