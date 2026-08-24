import os
import subprocess
import sys
from pathlib import Path

# INITIALIZE VARIABLES
SD_MESSAGE: str = "PC is shutting down in {time}."
SD_MINUTES: int = 5


def main() -> None:
    global SD_MESSAGE, SD_MINUTES

    # GET FINAL VARIABLE VALUES
    minutes_str = f"{SD_MINUTES} minute" if SD_MINUTES == 1 else f"{SD_MINUTES} minutes"  # type:ignore[reportUnnecessaryComparison]
    SD_MESSAGE = SD_MESSAGE.format(time=minutes_str)  # type:ignore[reportConstantRedefinition]
    secs = SD_MINUTES * 60

    # SET PLATFORM-SPECIFIC VARIABLES
    if sys.platform == "win32":
        autostart = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        script_path = autostart / "notSUS.bat"
        script_content = f"@echo OFF\nshutdown /s /f /t {secs} /c '{SD_MESSAGE}'"
    else:
        autostart = Path("~/.config/autostart").expanduser()
        script_path = autostart / "notSUS.sh"
        script_content = f"#!/bin/sh\nshutdown -h +{SD_MINUTES} '{SD_MESSAGE}'"

    # CREATE FILE IN STARTUP DIRECTORY, WITH SHUTDOWN COMMAND INSIDE
    autostart.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script_content)

    # SET FILE PERMISSIONS AND RUN SHUTDOWN COMMAND
    if sys.platform != "win32":
        script_path.chmod(0o755)
    if sys.platform == "win32":
        subprocess.run(["shutdown", "/s", "/f", "/t", str(secs), "/c", SD_MESSAGE])
    elif sys.platform == "darwin":
        subprocess.run(["sudo", "shutdown", "-h", f"+{SD_MINUTES}", SD_MESSAGE])
    else:
        subprocess.run(["sudo", "shutdown", "-h", f"+{SD_MINUTES}", f"'{SD_MESSAGE}'"])


if __name__ == "__main__":
    main()
