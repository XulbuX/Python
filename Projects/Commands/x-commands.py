#!/usr/bin/env python3
"""Wrapper script that runs [b|u](x-cmds.py)"""
from xulbux import Console, Path
import subprocess
import sys
import os


TARGET_SCRIPT = os.path.join(Path.script_dir, "x-cmds.py")

if __name__ == "__main__":

    if not os.path.exists(TARGET_SCRIPT):
        Console.fail(
            "The [b|white](x-cmds.py) file wasn't found in "
            "the script's directory, but [b](is required).",
            start="\n",
            end="\n\n",
        )

    try:
        result = subprocess.run([sys.executable, TARGET_SCRIPT])
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
