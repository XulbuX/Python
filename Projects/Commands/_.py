"""Clears the console and also resets all the ANSI formatting."""
print("\x1bc\x1b[0m", end="", flush=True)