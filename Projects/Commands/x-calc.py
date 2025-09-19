#!/usr/bin/env python3
"""Do advanced calculations from the command line.
Supports a wide range of mathematical operations, functions and constants."""
from xulbux import FormatCodes, Console
from typing import Optional, Literal
import sympy
import numpy
import sys
import re


ARGS = Console.get_args({
    "calculation": "before",
    "ans": ["-a", "--ans"],
    "precision": ["-p", "--precision"],
    "debug": ["-d", "--debug"],
})
DEBUG = ARGS.debug.exists
LAST_ANS = ARGS.ans.value

sanitize = lambda a: sympy.sympify(a)
sys.set_int_max_str_digits(1000000000)

OPERATORS = {
    # ARITHMETIC OPERATORS
    "+": lambda a, b: sympy.Add(sanitize(a), sanitize(b)),
    "-": lambda a, b: sympy.Add(sanitize(a), sympy.Mul(sanitize(b), sympy.Integer(-1))),
    "*": lambda a, b: sympy.Mul(sanitize(a), sanitize(b)),
    "x": lambda a, b: sympy.Mul(sanitize(a), sanitize(b)),
    "/": lambda a, b: sympy.Mul(sanitize(a), sympy.Pow(sanitize(b), -1)),
    "//": lambda a, b: sympy.floor(sympy.Mul(sanitize(a), sympy.Pow(sanitize(b), -1))),
    "%": lambda a, b: sympy.Mod(sanitize(a), sanitize(b)),
    "\\": lambda a, b: sympy.floor(sympy.Pow(sanitize(a), sympy.Pow(sanitize(b), -1))),
    "**": lambda a, b: sympy.Pow(sanitize(a), sanitize(b)),
    # LOGIC OPERATORS
    "&&": lambda a, b: a and b,
    "AND": lambda a, b: a and b,
    "||": lambda a, b: a or b,
    "OR": lambda a, b: a or b,
    "!": lambda a, _: not a,
    "NOT": lambda a, _: not a,
    "^": lambda a, b: (a and not b) or (not a and b),
    "XOR": lambda a, b: (a and not b) or (not a and b),
    # COMPARISON OPERATORS
    "=": lambda a, b: 1 if a == b else 0,
    "==": lambda a, b: 1 if a == b else 0,
    "!=": lambda a, b: 1 if a != b else 0,
    "<": lambda a, b: 1 if a < b else 0,
    "<=": lambda a, b: 1 if a <= b else 0,
    ">": lambda a, b: 1 if a > b else 0,
    ">=": lambda a, b: 1 if a >= b else 0,
}

PRECEDENCE = {
    # HIGHER VALUES REPRESENT HIGHER PRECEDENCE
    "**": 4, "*": 3, "x": 3, "//": 3, "/": 3, "%": 3, "+": 2, "-": 2, "&&": 1, "AND": 1, "||": 0, "OR": 0, "=": -1, "==": -1,
    "!=": -1, "<": -1, "<=": -1, ">": -1, ">=": -1, "!": -2, "NOT": -2, "^": -3, "XOR": -3
}

CONSTANTS = {
    "ans": ARGS.ans.value,
    "pi": sympy.pi,
    "e": sympy.E,
}

FUNCTIONS = {
    # PROGRAMMING FUNCTIONS
    "abs": lambda a: abs(sanitize(a)),
    "floor": lambda a: sympy.floor(sanitize(a)),
    "ceil": lambda a: sympy.ceiling(sanitize(a)),
    "round": lambda a: sympy.floor(sanitize(a) + sympy.Rational(1, 2)),
    # LOGARITHMIC FUNCTIONS
    "log": lambda a: sympy.log(sanitize(a), 10),
    "ln": lambda a: sympy.log(sanitize(a)),
    "exp": lambda a: sympy.exp(sanitize(a)),
    # TRIGONOMETRIC FUNCTIONS
    "rad": lambda a: sympy.rad(sanitize(a)),
    "deg": lambda a: sympy.deg(sanitize(a)),
    "sin": lambda a: sympy.sin(sanitize(a)),
    "asin": lambda a: sympy.asin(sanitize(a)),
    "cos": lambda a: sympy.cos(sanitize(a)),
    "acos": lambda a: sympy.acos(sanitize(a)),
    "tan": lambda a: sympy.tan(sanitize(a)),
    "atan": lambda a: sympy.atan(sanitize(a)),
    # ADDITIONAL FUNCTIONS
    "fac": lambda a: sympy.factorial(sanitize(a)),
    "exp": lambda a: sympy.exp(sanitize(a)),
    "log2": lambda a: sympy.log(sanitize(a), 2),
    "sqrt": lambda a: sympy.sqrt(sanitize(a)),
    "sinh": lambda a: sympy.sinh(sanitize(a)),
    "cosh": lambda a: sympy.cosh(sanitize(a)),
    "tanh": lambda a: sympy.tanh(sanitize(a)),
    "asinh": lambda a: sympy.asinh(sanitize(a)),
    "acosh": lambda a: sympy.acosh(sanitize(a)),
    "atanh": lambda a: sympy.atanh(sanitize(a)),
}


def print_overwrite(*values: object, sep: str = " ", end: str = "\n") -> None:
    FormatCodes.print(f"\033[2K\r{sep.join(str(val) for val in values)}", end=end)


def print_line(title: Optional[str] = None, char: str = "═", width: int = Console.w, end="\n") -> None:
    if not title:
        FormatCodes.print(f"[dim]{char * width}[_dim]", end=end)
        return
    line = char * round((width / 2) - ((len(title) + 2) / 2))
    final = FormatCodes.to_ansi(f"[dim]{line}[_dim] [b]{title}[_b] [dim]{line}")
    final_len = len(FormatCodes.remove_ansi(final))
    if not final_len == width:
        if final_len > width:
            final = final[:width + (len(final) - final_len)]
        if final_len < width:
            final = final + (width - final_len) * char
    FormatCodes.print(f"{final}[_dim]", end=end)


def clear_lines(num_lines: int = 1) -> None:
    for _ in range(num_lines):
        print("\033[F\033[K", end="", flush=True)


def generate_regex_pattern(dict: dict, direction: Literal["forward", "backward"] = "forward") -> str:
    if direction == "forward":
        return "|".join(map(re.escape, dict.keys()))
    elif direction == "backward":
        reversed_keys = list(reversed(dict.keys()))
        return "|".join(map(re.escape, reversed_keys))


def find_matches(text: str) -> list:
    operator_pattern = generate_regex_pattern(OPERATORS, "backward")
    # Updated regex to handle negative numbers: -?\d*\.\d+ matches optional minus with decimals, -?\d+ matches optional minus with integers
    matches = re.findall(r"[a-z]+|-?\d*\.\d+|-?\d+|" + operator_pattern, text)
    if DEBUG:
        print_line("FINDING MATCHES")
        print(f"input text: {text}")
        print(f"found matches: {matches}")
    return matches


def format_result(result: float, precision: int = 10) -> str:
    if DEBUG:
        print_line("FORMAT RESULT")
        print(f"result: {result}")
        print(f"precision: {precision}")
    try:
        result_str = "{:.{}f}".format(result, precision)
        result_str = (result_str.rstrip("0").rstrip(".") if "." in result_str else result_str)
    except OverflowError:
        result_str = str(result)
    if DEBUG:
        print(f"formatted result: {result_str}")
    return result_str


def format_readability(num_str: str, max_num_len: int) -> str:
    if not DEBUG:
        print_overwrite("[dim|white](formatting...)", end="")
    num_str = str(num_str)

    # TRUNCATE REPEATING DECIMAL
    if len(num_str) > max_num_len and "." in num_str:
        num_str = num_str[:-10]
        int_part, decimal_part = num_str.split(".")
        short_decimal_part = decimal_part[:max_num_len]
        if DEBUG:
            print_line(f"TRUNCATING REPEATING DECIMAL")
            print(f"input string: {num_str}")
            print(f"decimal part: {short_decimal_part}")

        def is_recurring(string: str, max_check_loops: int = -1) -> list | bool:

            def get_rept(s):
                r = re.compile(r"(.+?)\1+")
                for match in r.finditer(s):
                    yield match.group(1)

            repts = list(get_rept(string))
            if not repts:
                return False
            repts.reverse()
            loops = (len(repts) if max_check_loops < 0 or len(repts) < max_check_loops else max_check_loops)
            for loop in range(loops):
                rept = repts[loop]
                if not string[-((len(rept)) * 2):] == rept * 2:
                    found = i = 0

                    for i in range(len(string), 1, -1):
                        if string[i - len(rept):i] == rept:
                            if found > 0:
                                break
                            else:
                                found += 1

                    if not found:
                        return False
                    else:
                        rept_i = 0
                        for char in string[i:]:
                            if char == rept[rept_i]:
                                i += 1
                            else:
                                i = 0
                                break
                            rept_i += 1
                            if rept_i == len(rept):
                                rept_i = 0

                        if i > 0:
                            return True
                        elif loop == loops - 1:
                            return False
                else:
                    return True
            return False

        if is_recurring(short_decimal_part):
            num_str = f"{int_part}.{short_decimal_part}..."
        else:
            num_str = f"{int_part}.{short_decimal_part}"
        if DEBUG:
            print(f"formatted string: {num_str}")

    # FORMAT LONG NUMBERS TO EXPONENTS
    elif len(num_str) > max_num_len:
        if DEBUG:
            print_line(f"FORMATTING LONG NUMBERS TO EXPONENTS")
            print(f"input string: {num_str}")

        def format_exponents(string: str, max_num_len: int) -> str:
            pattern = re.compile(r"(\d*\.\d+|\d+)(?![\de])")

            def replace_match(match):
                number_sequence = match.group(1)
                if len(str(number_sequence)) <= max_num_len:
                    return number_sequence
                base = number_sequence[:max_num_len]
                exponent_value = len(number_sequence) - max_num_len
                if exponent_value >= 0:
                    sign = "+"
                else:
                    sign = "-"
                exponent_form = base + "e" + sign + str(abs(exponent_value))
                return exponent_form

            formatted_str = re.sub(pattern, replace_match, string)
            return formatted_str

        num_str = format_exponents(num_str, max_num_len)
        if DEBUG:
            print(f"formatted string: {num_str}")
    return num_str


def calc(calc_str: str, precision: int = 110, max_num_len: int = 100) -> str:
    global LAST_ANS
    if DEBUG:
        clear_lines()
        print()
        print_line(f"NEW CALCULATION")
        print(f"raw calculation string: {calc_str}")
    else:
        print_overwrite("[dim|white](calculating...)", end="")
    value_validation = False
    if precision <= max_num_len:
        max_num_len = precision
        precision += 10
        value_validation = True
    calc_str = str(calc_str.strip()).replace(" ", "")
    SAVE_CALC_STR = calc_str
    for _ in range(calc_str.count("(")):
        start = calc_str.rfind("(") + 1
        end = calc_str.find(")", start)
        formatted_result = calc_str[start:end]
        before_paren_pos = start - 2
        should_add_mult = (before_paren_pos >= 0 and calc_str[before_paren_pos].isdigit())
        calc_str = calc_str.replace(
            "(" + formatted_result + ")",
            ("*" if should_add_mult else "") + str(calc(formatted_result)),
        )
    if DEBUG:
        print(f"adjusted calculation string: {calc_str}")
        if value_validation:
            print("FOLLOWING VALUES WERE RESIZED FOR VALIDATION:")
        (print(f" > precision: {precision}") if value_validation else print(f"precision: {precision}"))
        (print(f" > max number length: {max_num_len}") if value_validation else print(f"max number length: {max_num_len}"))
    numpy.set_printoptions(floatmode="fixed", formatter={"float_kind": "{:f}".format})  # HANDLE SCIENTIFIC NOTATION
    split = find_matches(calc_str)
    array = numpy.array(split)

    # CONVERT ALL OPERANDS TO 'SymPy' EXPRESSIONS
    def sympify(split_matches: list) -> list:
        split_sympy = []
        for token in split_matches:
            if token in OPERATORS:
                split_sympy.append(token)
            else:
                split_sympy.append(sympy.sympify(token))
        return split_sympy

    split_sympy = sympify(split)
    # ITERATE OVER CONSTANTS FIRST
    for constant in CONSTANTS:
        count = split.count(constant)
        for _ in range(count):
            indices = numpy.where(array == constant)[0]
            for index in indices:
                if DEBUG:
                    print_line(f"CALCULATING CONSTANT")
                    print(f"constant: {constant}")
                constant_value = CONSTANTS[constant]
                if constant == "ans" and constant_value is None:
                    raise Exception("'ans' was not specified")
                if DEBUG:
                    print(f"value: {constant_value}")
                formatted_result = format_result(constant_value, precision)
                calc_str = calc_str.replace(constant, str(formatted_result))
        split = find_matches(calc_str)
        array = numpy.array(split)
        split_sympy = sympify(split)
    # ITERATE OVER FUNCTIONS AVAILABLE
    for function in FUNCTIONS:
        count = split.count(function)
        for _ in range(count):
            indices = numpy.where(array == function)[0]
            for index in indices:
                if DEBUG:
                    print_line(f"CALCULATING FUNCTION")
                result = FUNCTIONS[function](split_sympy[index + 1])
                if DEBUG:
                    print(f"argument: {split_sympy[index - 1]}")
                    print(f"function: {function}")
                    print(f"argument: {split_sympy[index + 1]}")
                    print(f"result: {result}")

                formatted_result = format_result(result, precision)
                calc_str = calc_str.replace(function + " " + split[index + 1],
                                            str(formatted_result)).replace(function + split[index + 1], str(formatted_result))
            split = find_matches(calc_str)
            array = numpy.array(split)
            split_sympy = sympify(split)
    # ITERATE OVER OTHER SYMBOLS BASED ON PRECEDENCE
    sorted_operators = sorted(set(OPERATORS.keys()), key=lambda x: PRECEDENCE.get(x, 5), reverse=True)
    for operator in sorted_operators:
        count = split.count(operator)
        for _ in range(count):
            indices = numpy.where(array == operator)[0]
            for index in indices:
                if DEBUG:
                    print_line(f"CALCULATING OPERATOR")
                result = OPERATORS[operator](split_sympy[index - 1], split_sympy[index + 1])
                if DEBUG:
                    print(f"argument: {split_sympy[index - 1]}")
                    print(f"operator: {operator}")
                    print(f"argument: {split_sympy[index + 1]}")
                    print(f"result: {result}")

                formatted_result = format_result(result, precision)
                calc_str = calc_str.replace(
                    split[index - 1] + " " + operator + " " + split[index + 1],
                    formatted_result,
                ).replace(split[index - 1] + operator + split[index + 1], formatted_result)
            split = find_matches(calc_str)
            array = numpy.array(split)
            split_sympy = sympify(split)
    if calc_str == SAVE_CALC_STR:
        try:
            sympy.sympify(calc_str)
        except:
            raise Exception(f"Could not perform calculation on: '{SAVE_CALC_STR}'")
    LAST_ANS = calc_str
    formatted_ans = format_readability(calc_str, max_num_len)
    return formatted_ans


def main():
    print()
    if len(calc_strs := list(ARGS.calculation.value)) > 0:
        ans = calc(
            " ".join(str(v) for v in calc_strs),
            precision=(ARGS.precision.value or 100) + 10,
            max_num_len=(ARGS.precision.value or 100),
        )
        if DEBUG:
            print_line("FINAL RESULT")
            print(f"answer: {ans}")
            print_line()
            print()
        else:
            print_overwrite(f"[dim|br:green][b](=) [_dim]{ans}[_]")
    else:
        FormatCodes.print(f"[b](Possible funcs/vars:)\n[dim](•) {'\n[dim](•) '.join(FUNCTIONS.keys())}\n")
        FormatCodes.print(f"[b](Possible constants:)\n[dim](•) {'\n[dim](•) '.join(CONSTANTS.keys())}\n")
        FormatCodes.print(f"[b](Possible operators:)\n[dim](•) {'\n[dim](•) '.join(OPERATORS.keys())}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_overwrite("[b|br:red](⨯)\n")
    except Exception as e:
        Console.fail(e, start="\n\n", end="\n\n")
