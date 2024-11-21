import xulbux as xx
import sys


ARGS = sys.argv[1:]


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


if __name__ == "__main__":
    sep = get_sep(ARGS)
    prt_sep = f"{sep} " if sep != " " else sep
    lst = [x for x in input(">  ").split(sep) if x.strip() not in (None, "")]

    if len(lst) >= 1 and lst[0].strip() not in (None, ""):
        xx.FormatCodes.print(f'\n[bright:cyan]{'\n'.join(lst)}[_]')
        print()  # BLANK LINE
        if lst not in (None, "") and all(is_num(x) for x in lst):
            lst = [int(x) if x.isdigit() else float(x) for x in lst]
            average = lambda nums: sum(nums) / len(nums)
            print(f"Min: {min(lst)}")
            print(f"Max: {max(lst)}")
            print(f"Sum: {sum(lst)}")
            print(f"Average: {average(lst)}")
        else:
            lst = [str(x) for x in lst]
            print(f"Items count: {len(lst)}")
            print(f"Unique entries: {prt_sep.join(sorted(set(lst)))}")
            if any(x.isalpha() for x in lst):
                upper = sum(1 for x in lst if x.isupper())
                lower = sum(1 for x in lst if x.islower())
                print(f"Uppercase: {upper / len(lst) * 100:.1f}%")
                print(f"Lowercase: {lower / len(lst) * 100:.1f}%")
        print()  # BLANK LINE
