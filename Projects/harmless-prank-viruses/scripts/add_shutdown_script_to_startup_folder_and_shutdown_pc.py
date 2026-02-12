import subprocess
import sys
import os

# INITIALIZE VARIABLES
SD_MESSAGE = "PC is shutting down in {time}."
SD_MINUTES = 5


def main():
    global SD_MESSAGE, SD_MINUTES

    # GET FINAL VARIABLE VALUES
    minutes_str = f"{SD_MINUTES} minute" if SD_MINUTES == 1 else f"{SD_MINUTES} minutes"
    SD_MESSAGE = SD_MESSAGE.format(time=minutes_str)
    secs = SD_MINUTES * 60

    # SET PLATFORM-SPECIFIC VARIABLES
    if sys.platform == "win32":
        autostart = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        script_path = os.path.join(autostart, "notSUS.bat")
        script_content = f"@echo OFF\nshutdown /s /f /t {secs} /c '{SD_MESSAGE}'"
    else:
        autostart = os.path.expanduser("~/.config/autostart")
        script_path = os.path.join(autostart, "notSUS.sh")
        script_content = f"#!/bin/sh\nshutdown -h +{SD_MINUTES} '{SD_MESSAGE}'"

    # CREATE FILE IN STARTUP DIRECTORY, WITH SHUTDOWN COMMAND INSIDE
    os.makedirs(autostart, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script_content)

    # SET FILE PERMISSIONS AND RUN SHUTDOWN COMMAND
    if sys.platform != "win32":
        os.chmod(script_path, 0o755)
    if sys.platform == "win32":
        subprocess.run(["shutdown", "/s", "/f", "/t", str(secs), "/c", SD_MESSAGE])
    elif sys.platform == "darwin":
        subprocess.run(["sudo", "shutdown", "-h", f"+{SD_MINUTES}", SD_MESSAGE])
    else:
        subprocess.run(["sudo", "shutdown", "-h", f"+{SD_MINUTES}", f"'{SD_MESSAGE}'"])


if __name__ == "__main__":
    main()
