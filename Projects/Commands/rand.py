#!/usr/bin/env python3
"""Generate a truly random number with a specific number of digits or within a range.
Provide either the number of digits or a min and max range."""
from xulbux import FormatCodes, Console
from typing import Optional
import secrets
import sys


sys.set_int_max_str_digits(1_000_000_000)

ARGS = Console.get_args({
    "digits_or_min_max": "before",
    "batch_gen": ["-b", "--batch", "--batch-gen"],
    "format": ["-f", "--format"],
})


def gen_random_int(digits: Optional[int] = None, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    # RANDOM NUMBER WITH SPECIFIC AMOUNT OF DIGITS
    if digits is not None:
        if digits <= 0:
            raise ValueError("The number of decimal places must be a positive integer.")
        random_int = secrets.randbelow((10**digits - 1) - (min_value := 10**(digits - 1)) + 1) + min_value

    # RANDOM NUMBER WITHIN A SPECIFIED RANGE
    elif min_val is not None and max_val is not None:
        if min_val >= max_val:
            raise ValueError("The minimum value must be less than the maximum value.")
        random_int = secrets.randbelow(max_val - min_val + 1) + min_val

    # INVALID USAGE
    else:
        raise ValueError("Either 'digits' or both 'min_val' and 'max_val' must be provided.")
    return random_int


if __name__ == "__main__":
    try:
        print()
        match len(ARGS.digits_or_min_max.value):
            case 0:
                Console.exit(
                    "[b](Too few arguments:) Provide either the number of decimal places or a min and max range",
                    start="\n",
                    end="\n\n",
                    exit_code=1,
                )
            case 1:
                digits = int(ARGS.digits_or_min_max.value[0])
                if digits > 1_000_000_000:
                    Console.exit(
                        "The number of decimal places must not exceed [white](1,000,000,000)",
                        start="\n",
                        end="\n\n",
                        exit_code=1,
                    )
                FormatCodes.print("[dim](generating...)", end="")
                random_int = gen_random_int(digits=digits)
                FormatCodes.print(f"\033[2K\r[br:blue]({random_int:{',' if ARGS.format.exists else ''}})\n")
            case 2:
                min_val = int(ARGS.digits_or_min_max.value[0])
                max_val = int(ARGS.digits_or_min_max.value[1])
                if min_val >= max_val:
                    Console.exit(
                        "[b](Invalid range:) The minimum value must be less than the maximum value",
                        start="\n",
                        end="\n\n",
                        exit_code=1,
                    )
                FormatCodes.print("[dim](generating...)", end="")
                if (batch := int(ARGS.batch_gen.value) if str(ARGS.batch_gen.value).isdigit() else 1) > 1:
                    random_ints, lowest_int, highest_int = [], max_val + 1, min_val - 1
                    for _ in range(batch):
                        random_int = gen_random_int(min_val=min_val, max_val=max_val)
                        random_ints.append(f"{random_int:{',' if ARGS.format.exists else ''}}")
                        if random_int < lowest_int: lowest_int = random_int
                        if random_int > highest_int: highest_int = random_int
                    FormatCodes.print(f"\033[2K\r[br:blue]{'\n'.join(random_ints)}\n")
                    FormatCodes.print(
                        f"[b|dim](lowest:)  {'' if lowest_int < 0 else ' '}[dim]({lowest_int:{',' if ARGS.format.exists else ''}})\n"
                        f"[b|dim](highest:) {'' if highest_int < 0 else ' '}[dim]{highest_int:{',' if ARGS.format.exists else ''}}[_]\n"
                    )
                else:
                    random_int = gen_random_int(min_val=min_val, max_val=max_val)
                    FormatCodes.print(f"\033[2K\r[br:blue]({random_int:{',' if ARGS.format.exists else ''}})\n")
            case _:
                Console.exit(
                    "[b](Too many arguments:) Provide either the number of decimal places or a min and max range",
                    start="\n",
                    end="\n\n",
                    exit_code=1,
                )
    except KeyboardInterrupt:
        FormatCodes.print("\033[2K\r[b|br:red](⨯)\n")
    except Exception as e:
        Console.fail(e, start="\033[2K\r", end="\n\n")
