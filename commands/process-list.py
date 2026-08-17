#!/usr/bin/env python3
# x-cmds:file[update]

"""Process a list of items and display some statistics."""

from xulbux import Console, FormatCodes

ARGS = Console.get_args({"list_items": "before", "separator": {"-s", "--sep"}, "help": {"-h", "--help"}})


def print_help() -> None:
    help_text = """
[b|in|bg:black]( Process List — Process a list of items and display statistics )

[b](Usage:) [br:green](process-list) [br:cyan](<item_1> <item_2> ...) [br:blue]([options])

[b](Arguments:)
  [br:cyan](items)          List items to process [dim]((space-separated or custom separator using [br:blue](-s)))

[b](Options:)
  [br:blue](-s), [br:blue](--sep[dim](=)S)    Separator character to split a single input string

[b](Examples:)
  [br:green](process-list) [br:cyan](1 2 3 4 5)         [dim](# [i](Process a list of numbers))
  [br:green](process-list) [br:cyan](a b c)             [dim](# [i](Process a list of strings))
  [br:green](process-list) [br:cyan]("1,2,3") [br:blue](-s[dim](=)',')    [dim](# [i](Process comma-separated values))

[b](Note:)  When all items are numbers, min, max, sum and average are also shown.
"""
    FormatCodes.print(help_text)


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    sep = ARGS.separator.get(0, "")

    if sep != "":
        input_str = input(">  ") if not ARGS.list_items.exists else " ".join(ARGS.list_items.values)
        lst = [x for x in input_str.split(sep) if x.strip() not in {"", None}]
    else:
        lst = [str(val) for val in ARGS.list_items.values]

    if len(lst) >= 1 and lst[0].strip() not in {"", None}:
        FormatCodes.print(f"\n[b|bg:black]([in]( PROCESSED ) {len(lst)} [in]( LIST ENTRIES ))\n")
        FormatCodes.print(f"[br:cyan]{'\n'.join(lst)}[_]\n")
        if all(e.isnumeric() for e in lst):
            lst = [int(e) if e.replace("_", "").isdigit() else float(e) for e in lst]

            def average(nums: list[int | float]) -> float:
                return sum(nums) / len(nums)

            Console.log_box_bordered(
                f"[b](Min)     : [br:cyan]({min(lst)})",
                f"[b](Max)     : [br:cyan]({max(lst)})",
                f"[b](Sum)     : [br:cyan]({sum(lst)})",
                f"[b](Average) : [br:cyan]({average(lst)})",
            )
        else:
            lst = [str(x) for x in lst]
            box_content = f"[b](Unique entries) : {' '.join(f'[br:cyan|bg:black]({e})' for e in sorted(set(lst)))}"
            if any(not e.replace("_", "").isdigit() for e in lst):
                upper = sum(1 for e in lst if e.isupper())
                lower = sum(1 for e in lst if e.islower())
                box_content += f"\n[b](Uppercase)      : {upper / len(lst) * 100:.1f}%"
                box_content += f"\n[b](Lowercase)      : {lower / len(lst) * 100:.1f}%"
            Console.log_box_bordered(box_content)
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        Console.fail(exc, start="\n", end="\n\n")
