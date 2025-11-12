#!/usr/bin/env python3
"""Generate a truly random number with a specific number of digits or within a range.
Provide either the number of digits or a min and max range."""
from xulbux import FormatCodes, ProgressBar, Console
from typing import Optional
import secrets
import sys


sys.set_int_max_str_digits(0)  # 0 = NO LIMIT

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


def main():
    print()
    batch = int(ARGS.batch_gen.value) if ARGS.batch_gen.value and (ARGS.batch_gen.value or "").isdigit() else 1
    update_progress_at = 1 if batch <= 100 else 99 if batch <= 10_000 else 999
    match len(ARGS.digits_or_min_max.values):

        case 0:
            Console.exit(
                "[b](Too few arguments:) Provide either the number of decimal places or a min and max range",
                start="\n",
                end="\n\n",
                exit_code=1,
            )

        case 1:
            digits = int(ARGS.digits_or_min_max.values[0])
            FormatCodes.print("[dim](generating...)", end="")
            if batch > 1:
                random_ints = []
                with ProgressBar().progress_context(batch, "generating...") as update_progress:
                    update_progress(0)
                    for i in range(batch):
                        random_int = gen_random_int(digits=digits)
                        random_ints.append(f"{random_int:{',' if ARGS.format.exists else ''}}\n")
                        if i % update_progress_at == 0: update_progress(i + 1)
                FormatCodes.print("\x1b[2K\r[dim](formatting...)", end="")
                FormatCodes.print(f"\x1b[2K\r[br:blue]{'\n'.join(random_ints)}[_]")
            else:
                random_int = gen_random_int(digits=digits)
                FormatCodes.print(f"\x1b[2K\r[br:blue]({random_int:{',' if ARGS.format.exists else ''}})\n")

        case 2:
            min_val = int(ARGS.digits_or_min_max.values[0])
            max_val = int(ARGS.digits_or_min_max.values[1])
            if min_val >= max_val:
                Console.exit(
                    "[b](Invalid range:) The minimum value must be less than the maximum value",
                    start="\n",
                    end="\n\n",
                    exit_code=1,
                )
            FormatCodes.print("[dim](generating...)", end="")
            if batch > 1:
                random_ints, lowest_int, highest_int = [], max_val + 1, min_val - 1
                with ProgressBar().progress_context(batch, "generating...") as update_progress:
                    for i in range(batch):
                        random_int = gen_random_int(min_val=min_val, max_val=max_val)
                        random_ints.append(f"{random_int:{',' if ARGS.format.exists else ''}}\n")
                        if random_int < lowest_int: lowest_int = random_int
                        if random_int > highest_int: highest_int = random_int
                        if i % update_progress_at == 0: update_progress(i + 1)
                FormatCodes.print("\x1b[2K\r[dim](formatting...)", end="")
                FormatCodes.print(f"\x1b[2K\r[br:blue]{'\n'.join(random_ints)}")
                FormatCodes.print(
                    f"[b|dim](lowest:)  {'' if lowest_int < 0 else ' '}[dim]({lowest_int:{',' if ARGS.format.exists else ''}})\n"
                    f"[b|dim](highest:) {'' if highest_int < 0 else ' '}[dim]{highest_int:{',' if ARGS.format.exists else ''}}[_]\n"
                )
            else:
                random_int = gen_random_int(min_val=min_val, max_val=max_val)
                FormatCodes.print(f"\x1b[2K\r[br:blue]({random_int:{',' if ARGS.format.exists else ''}})\n")

        case _:
            Console.exit(
                "[b](Too many arguments:) Provide either the number of decimal places or a min and max range",
                start="\n",
                end="\n\n",
                exit_code=1,
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        FormatCodes.print("\x1b[2K\r[b|br:red](⨯)\n")
    except MemoryError:
        Console.fail("[b](MemoryError:) The operation ran out of memory", start="\x1b[2K\r", end="\n\n")
    except OverflowError as e:
        Console.fail(f"[b](OverflowError:) {e}", start="\x1b[2K\r", end="\n\n")
    except Exception as e:
        Console.fail(e, start="\x1b[2K\r", end="\n\n")
