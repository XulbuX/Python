#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Process a list of items and display some statistics."""
from xulbux import FormatCodes, Console


ARGS = Console.get_args(
    list_items="before",
    separator={"-s", "--sep", "--separator"},
)


def main() -> None:
    sep = str(ARGS.separator.value or "")

    if sep != "":
        if not ARGS.list_items.exists:
            input_str = input(">  ")
        else:
            input_str = " ".join(ARGS.list_items.values)
        lst = [x for x in input_str.split(sep) if x.strip() not in {"", None}]
    else:
        lst = [str(val) for val in ARGS.list_items.values]

    if len(lst) >= 1 and lst[0].strip() not in {"", None}:
        FormatCodes.print(f"\n[b|bg:black]([in]( PROCESSED ) {len(lst)} [in]( LIST ENTRIES ))\n")
        FormatCodes.print(f"[bright:cyan]{'\n'.join(lst)}[_]\n")
        if all(e.isnumeric() for e in lst):
            lst = [int(e) if e.replace("_", "").isdigit() else float(e) for e in lst]
            average = lambda nums: sum(nums) / len(nums)
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
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
