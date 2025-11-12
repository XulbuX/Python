#!/usr/bin/env python3
"""Process a list of items and display some statistics."""
from xulbux import FormatCodes, Console

ARGS = Console.get_args({
    "list_elements": "before",
    "separator": ["-s", "--sep"],
})


def main()->None:
    sep = str(ARGS.separator.value or "")

    if sep != "":
        if not ARGS.list_elements.exists:
            input_str = input(">  ")
        else:
            input_str = " ".join(ARGS.list_elements.values)
        lst = [x for x in input_str.split(sep) if x.strip() not in (None, "")]
    else:
        lst = [str(val) for val in ARGS.list_elements.values]

    if len(lst) >= 1 and lst[0].strip() not in (None, ""):
        FormatCodes.print(f'\n[bright:cyan]{'\n'.join(lst)}[_]\n')
        if lst not in (None, "") and all(x.isnumeric() for x in lst):
            lst = [int(x) if x.isdigit() else float(x) for x in lst]
            average = lambda nums: sum(nums) / len(nums)
            FormatCodes.print(f"[b](Min:) {min(lst)}")
            FormatCodes.print(f"[b](Max:) {max(lst)}")
            FormatCodes.print(f"[b](Sum:) {sum(lst)}")
            FormatCodes.print(f"[b](Average:) {average(lst)}")
        else:
            lst = [str(x) for x in lst]
            FormatCodes.print(f"[b](Items count:) {len(lst)}")
            FormatCodes.print(f"[b](Unique entries:) {", ".join(sorted(set(lst)))}")
            if any(x.isalpha() for x in lst):
                upper = sum(1 for x in lst if x.isupper())
                lower = sum(1 for x in lst if x.islower())
                FormatCodes.print(f"[b](Uppercase:) {upper / len(lst) * 100:.1f}%")
                FormatCodes.print(f"[b](Lowercase:) {lower / len(lst) * 100:.1f}%")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
