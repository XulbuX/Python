#!/usr/bin/env python3
"""Generate a truly random number with a specific number of digits or within a range.
Provide either the number of digits or a min and max range."""
from xulbux.console import ProgressBar
from xulbux import FormatCodes, Console
from typing import Optional
import secrets
import sys


sys.set_int_max_str_digits(0)  # 0 = NO LIMIT

ARGS = Console.get_args({
    "digits_or_min_max": "before",
    "batch_gen": {"-b", "--batch", "--batch-gen"},
    "format": {"-f", "--format"},
    "help": {"-h", "--help"},
})


def print_help():
    help_text = """
[b|in|bg:black]( Random - Generate truly random numbers )

[b](Usage:) [br:green](rand) [br:cyan](<num> <num_2>) [br:blue]([options])

[b](Arguments:)
  [br:cyan](num)                  Number of digits or start of range
  [br:cyan](num_2)                End of range [dim]((optional))

[b](Options:)
  [br:blue](-b), [br:blue](--batch-gen N)    Generate multiple random numbers
  [br:blue](-f), [br:blue](--format)         Format numbers with commas as thousand separators

[b](Examples:)
  [br:green](rand) [br:cyan](10)                 [dim](# [i](Generate a random number with 10 digits))
  [br:green](rand) [br:cyan](-100 100)           [dim](# [i](Generate a random number between -100 and 100))
  [br:green](rand) [br:cyan](5) [br:blue](--batch-gen 3)    [dim](# [i](Generate 3 random numbers with 5 digits))
  [br:green](rand) [br:cyan](10) [br:blue](--format)        [dim](# [i](Generate a comma-formatted random number with 10 digits))
"""
    FormatCodes.print(help_text)


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
    if ARGS.help.exists or len(ARGS.digits_or_min_max.values) == 0:
        print_help()
        return

    print()

    batch = int(ARGS.batch_gen.value) if ARGS.batch_gen.value and ARGS.batch_gen.value.replace("_", "").isdigit() else 1

    match len(ARGS.digits_or_min_max.values):

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
                        update_progress(i + 1)
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
                        update_progress(i + 1)
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
                "[b](Too many arguments:) Provide either the number of digits or a min and max range",
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
