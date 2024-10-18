import subprocess
import sys
import os

# INITIALIZE VARIABLES
sd_message = 'PC is shutting down in {time}.'
sd_minutes = 5

# GET FINAL VARIABLE VALUES
minutes_str = f'{sd_minutes} minute' if sd_minutes == 1 else f'{sd_minutes} minutes'
sd_message = sd_message.format(time=minutes_str)
secs = sd_minutes * 60

# SET PLATFORM-SPECIFIC VARIABLES
if sys.platform == 'win32':
  autostart = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
  script_path = os.path.join(autostart, 'notSUS.bat')
  script_content = f'@echo OFF\nshutdown /s /f /t {secs} /c "{sd_message}"'
else:
  autostart = os.path.expanduser('~/.config/autostart')
  script_path = os.path.join(autostart, 'notSUS.sh')
  script_content = f'#!/bin/sh\nshutdown -h +{sd_minutes} "{sd_message}"'

# CREATE FILE IN STARTUP DIRECTORY, WITH SHUTDOWN COMMAND INSIDE
os.makedirs(autostart, exist_ok=True)
with open(script_path, 'w') as f: f.write(script_content)

# SET FILE PERMISSIONS AND RUN SHUTDOWN COMMAND
if sys.platform != 'win32': os.chmod(script_path, 0o755)
if sys.platform == 'win32': subprocess.run(['shutdown', '/s', '/f', '/t', str(secs), '/c', sd_message])
elif sys.platform == 'darwin': subprocess.run(['sudo', 'shutdown', '-h', f'+{sd_minutes}', sd_message])
else: subprocess.run(['sudo', 'shutdown', '-h', f'+{sd_minutes}', f'"{sd_message}"'])