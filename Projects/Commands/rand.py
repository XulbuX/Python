#!/usr/bin/env python3
"""Generate a truly random number with a specified number of decimal places."""
from xulbux import FormatCodes, Console
import secrets
import sys


sys.set_int_max_str_digits(1_000_000_000)

ARGS = Console.get_args({
    "digits": "before",
})


def gen_rand_num(digits: int) -> str:
    if digits <= 0:
        raise ValueError("The number of decimal places must be a positive integer.")
    # GENERATE A RANDOM NUMBER WITH EXACTLY 'digits' DIGITS
    # RANGE: 10^(digits-1) TO 10^digits - 1 TO ENSURE EXACT DIGIT COUNT
    min_val = 10**(digits - 1)
    max_val = 10**digits - 1
    random_int = secrets.randbelow(max_val - min_val + 1) + min_val
    return random_int


if __name__ == "__main__":
    try:
        if len(ARGS.digits.value) == 0:
            Console.exit("The number of decimal places is required.", start="\n", end="\n\n", exit_code=1)
        else:
            FormatCodes.print("\n[dim](generating...)", end="")
            random_number = gen_rand_num(int(ARGS.digits.value[0]))
            FormatCodes.print(f"\033[2K\r[br:cyan]({random_number})\n")
    except KeyboardInterrupt:
        FormatCodes.print("\033[2K\r[b|br:red](⨯)\n")
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
