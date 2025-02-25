"""Process a list of items and display some statistics."""
from xulbux import FormatCodes, Console
import sys


ARGS = sys.argv[1:]  # [list_separator: [-s, --sep]]


def get_sep(args: list, default: str = " ") -> str:
    if args and args[0] in ("-s", "--sep"):
        return args[1]
    return default


def is_num(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def main()->None:
    sep = get_sep(ARGS)
    prt_sep = f"{sep} " if sep != " " else sep
    lst = [x for x in input(">  ").split(sep) if x.strip() not in (None, "")]

    if len(lst) >= 1 and lst[0].strip() not in (None, ""):
        FormatCodes.print(f'\n[bright:cyan]{'\n'.join(lst)}[_]\n')
        if lst not in (None, "") and all(is_num(x) for x in lst):
            lst = [int(x) if x.isdigit() else float(x) for x in lst]
            average = lambda nums: sum(nums) / len(nums)
            FormatCodes.print(f"[b](Min:) {min(lst)}")
            FormatCodes.print(f"[b](Max:) {max(lst)}")
            FormatCodes.print(f"[b](Sum:) {sum(lst)}")
            FormatCodes.print(f"[b](Average:) {average(lst)}")
        else:
            lst = [str(x) for x in lst]
            FormatCodes.print(f"[b](Items count:) {len(lst)}")
            FormatCodes.print(f"[b](Unique entries:) {prt_sep.join(sorted(set(lst)))}")
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
