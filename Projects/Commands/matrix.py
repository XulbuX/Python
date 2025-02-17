from xulbux import FormatCodes, Console
import random
import time


FIND_ARGS = {
    "fast": ["-f", "--fast", "-s", "--speed"],
    "color": ["-c", "--color"],
}
ARGS = Console.get_args(FIND_ARGS)

x = ["0", "1"]
f = ["dim", "bold", "inverse", "underline", "strikethrough", "double-underline"]
if ARGS["color"]["exists"]:
    f.extend([
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "BR:black", "BR:red", "BR:green", "BR:yellow",
        "BR:blue", "BR:magenta", "BR:cyan", "BR:white", "BG:black", "BG:red", "BG:green", "BG:yellow", "BG:blue", "BG:magenta",
        "BG:cyan", "BG:white", "BG:BR:black", "BG:BR:red", "BG:BR:green", "BG:BR:yellow", "BG:BR:blue", "BG:BR:magenta",
        "BG:BR:cyan", "BG:BR:white", "randomCL", "randomBG"
    ])


def random_hexa() -> str:
    return f"#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}"


def replace_special(text: str) -> str:
    return text.replace("randomCL", random_hexa()).replace("randomBG", f"BG:{random_hexa()}")


try:
    while True:
        line = "".join((f"[{replace_special(random.choice(f))}]" if random.randint(0, 1) == 1 else "")
                       + (random.choice(x) if random.randint(0, 1) == 1 else " ") + "[_]" for _ in range(Console.w))
        FormatCodes.print(line)
        if not ARGS["fast"]["exists"]:
            time.sleep(0.025)
except KeyboardInterrupt:
    print()
