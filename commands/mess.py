#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Displays an animated, random text character mess.
The mess can be made faster and displayed in color."""
from xulbux import FormatCodes, Console
import random
import time


ARGS = Console.get_args({
    "fast_mode": {"-f", "--fast"},
    "color_mode": {"-c", "--color"},
    "help": {"-h", "--help"},
})

rand_choice = random.choice
rand_bits = random.getrandbits
fc_print = FormatCodes.print
sleep = time.sleep


def print_help():
    help_text = """
[b|in|bg:black]( Mess — Display an animated random text character mess )

[b](Usage:) [br:green](mess) [br:blue]([options])

[b](Controls:)
  [br:red](CTRL+C)         Stop the animation

[b](Options:)
  [br:blue](-f), [br:blue](--fast)     Display the mess at maximum speed
  [br:blue](-c), [br:blue](--color)    Color the mess in random colors

[b](Examples:)
  [br:green](mess)            [dim](# [i](Show binary mess at normal speed))
  [br:green](mess) [br:blue](--fast)     [dim](# [i](Show binary mess at maximum speed))
  [br:green](mess) [br:blue](--color)    [dim](# [i](Show colorful binary mess))
  [br:green](mess) [br:blue](-f -c)      [dim](# [i](Show colorful binary mess at maximum speed))
"""
    FormatCodes.print(help_text)


x = ["0", "1"]
f = ["dim", "bold", "inverse", "underline", "strikethrough", "double-underline"]
if ARGS.color_mode.exists:
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


def rand_binary_line() -> str:
    return "".join(
        (f"[{rand_choice(f)}]" if rand_bits(1) else "") \
        + (rand_choice(x) if rand_bits(1) else " ")
        + "[_]"
        for _ in range(Console.width)
    )


def rand_color_binary_line() -> str:
    return "".join(
        (f"[{replace_special(rand_choice(f))}]" if rand_bits(1) else "") \
        + (rand_choice(x) if rand_bits(1) else " ")
        + "[_]"
        for _ in range(Console.width)
    )


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    if ARGS.color_mode.exists:
        if ARGS.fast_mode.exists:
            while True:
                fc_print(rand_color_binary_line())
        else:
            while True:
                fc_print(rand_color_binary_line())
                sleep(0.025)

    else:
        if ARGS.fast_mode.exists:
            while True:
                fc_print(rand_binary_line())
        else:
            while True:
                fc_print(rand_binary_line())
                sleep(0.025)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
