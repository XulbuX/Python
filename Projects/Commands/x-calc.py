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
sys.set_int_max_str_digits(1_000_000_000)

OPERATORS = {
    # ARITHMETIC OPERATORS
    "+": lambda a, b: sympy.Add(sanitize(a), sanitize(b)),
    "-": lambda a, b: sympy.Add(sanitize(a), sympy.Mul(sanitize(b), sympy.Integer(-1))),
    ("*", "x", "×", "·"): lambda a, b: sympy.Mul(sanitize(a), sanitize(b)),
    ("/", "÷", ":"): lambda a, b: sympy.Mul(sanitize(a), sympy.Pow(sanitize(b), -1)),
    "//": lambda a, b: sympy.floor(sympy.Mul(sanitize(a), sympy.Pow(sanitize(b), -1))),
    ("%", "mod"): lambda a, b: sympy.Mod(sanitize(a), sanitize(b)),
    "\\": lambda a, b: sympy.floor(sympy.Pow(sanitize(a), sympy.Pow(sanitize(b), -1))),
    ("**", "^"): lambda a, b: sympy.Pow(sanitize(a), sanitize(b)),
    # LOGIC OPERATORS
    ("&&", "AND"): lambda a, b: a and b,
    ("||", "OR"): lambda a, b: a or b,
    ("!", "NOT"): lambda a, _: not a,
    "XOR": lambda a, b: (a and not b) or (not a and b),
    # COMPARISON OPERATORS
    ("=", "=="): lambda a, b: 1 if a == b else 0,
    ("!=", "≠"): lambda a, b: 1 if a != b else 0,
    "<": lambda a, b: 1 if a < b else 0,
    ("<=", "≤"): lambda a, b: 1 if a <= b else 0,
    ">": lambda a, b: 1 if a > b else 0,
    (">=", "≥"): lambda a, b: 1 if a >= b else 0,
}

PRECEDENCE = {
    # HIGHER VALUES REPRESENT HIGHER PRECEDENCE
    "^": 4,
    ("*", "//", "/", "%", "\\"): 3,
    ("+", "-"): 2,
    "AND": 1,
    "OR": 0,
    ("==", "!=", "<", "<=", ">", ">="): -1,
    "NOT": -2,
    "XOR": -3,
}

CONSTANTS = {
    "ans": ARGS.ans.value,
    ("pi", "π"): sympy.pi,
    "e": sympy.E,
}

FUNCTIONS = {
    # PROGRAMMING FUNCTIONS
    ("abs", "absolute"): lambda a: abs(sanitize(a)),
    "floor": lambda a: sympy.floor(sanitize(a)),
    ("ceil", "ceiling"): lambda a: sympy.ceiling(sanitize(a)),
    "round": lambda a: sympy.floor(sanitize(a) + sympy.Rational(1, 2)),
    # LOGARITHMIC FUNCTIONS
    ("log", "log10", "logarithm"): lambda a: sympy.log(sanitize(a), 10),
    ("ln", "log_e", "natural_log"): lambda a: sympy.log(sanitize(a)),
    ("log2", "log_2"): lambda a: sympy.log(sanitize(a), 2),
    ("exp", "exponential"): lambda a: sympy.exp(sanitize(a)),
    # TRIGONOMETRIC FUNCTIONS
    ("rad", "radians"): lambda a: sympy.rad(sanitize(a)),
    ("deg", "degrees"): lambda a: sympy.deg(sanitize(a)),
    ("sin", "sine"): lambda a: sympy.sin(sanitize(a)),
    ("asin", "arcsin", "arcsine"): lambda a: sympy.asin(sanitize(a)),
    ("cos", "cosine"): lambda a: sympy.cos(sanitize(a)),
    ("acos", "arccos", "arccosine"): lambda a: sympy.acos(sanitize(a)),
    ("tan", "tangent"): lambda a: sympy.tan(sanitize(a)),
    ("atan", "arctan", "arctangent"): lambda a: sympy.atan(sanitize(a)),
    # HYPERBOLIC FUNCTIONS
    ("sinh", "hyperbolic_sine"): lambda a: sympy.sinh(sanitize(a)),
    ("cosh", "hyperbolic_cosine"): lambda a: sympy.cosh(sanitize(a)),
    ("tanh", "hyperbolic_tangent"): lambda a: sympy.tanh(sanitize(a)),
    ("asinh", "arcsinh", "inverse_sinh"): lambda a: sympy.asinh(sanitize(a)),
    ("acosh", "arccosh", "inverse_cosh"): lambda a: sympy.acosh(sanitize(a)),
    ("atanh", "arctanh", "inverse_tanh"): lambda a: sympy.atanh(sanitize(a)),
    # ADDITIONAL FUNCTIONS
    ("fac", "factorial"): lambda a: sympy.factorial(sanitize(a)),
    ("sqrt", "square_root"): lambda a: sympy.sqrt(sanitize(a)),
}


def get_precedence(operator: str) -> int:
    if operator in PRECEDENCE:
        return PRECEDENCE[operator]
    for op_group in OPERATORS.keys():
        if isinstance(op_group, tuple) and operator in op_group:
            for rep in op_group:
                if rep in PRECEDENCE:
                    return PRECEDENCE[rep]
    for prec_key, prec_val in PRECEDENCE.items():
        if isinstance(prec_key, tuple) and operator in prec_key:
            return prec_val
    return 0


OPERATORS_FLAT = {key: func for keys, func in OPERATORS.items() for key in (keys if isinstance(keys, tuple) else [keys])}
PRECEDENCE_FLAT = {op: get_precedence(op) for op in OPERATORS_FLAT.keys()}
ALL_OPERATOR_SYMBOLS = [key for keys in OPERATORS.keys() for key in (keys if isinstance(keys, tuple) else [keys])]
FUNCTIONS_FLAT = {key: func for keys, func in FUNCTIONS.items() for key in (keys if isinstance(keys, tuple) else [keys])}
CONSTANTS_FLAT = {key: value for keys, value in CONSTANTS.items() for key in (keys if isinstance(keys, tuple) else [keys])}


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
    # Use pre-computed symbols for operators, or extract from dict for other cases
    if dict is OPERATORS:
        all_symbols = ALL_OPERATOR_SYMBOLS
    else:
        all_symbols = []
        for keys in dict.keys():
            if isinstance(keys, tuple):
                all_symbols.extend(keys)
            else:
                all_symbols.append(keys)

    if direction == "forward":
        return "|".join(map(re.escape, all_symbols))
    elif direction == "backward":
        reversed_symbols = list(reversed(all_symbols))
        return "|".join(map(re.escape, reversed_symbols))


def find_matches(text: str) -> list:
    operator_pattern = generate_regex_pattern(OPERATORS, "backward")
    preliminary_matches = re.findall(r"[a-z]+|-?\d*\.\d+|-?\d+|" + operator_pattern, text)

    matches = []
    for i, match in enumerate(preliminary_matches):
        if (match.startswith('-') and len(match) > 1 and match[1:].replace('.', '').isdigit() and i > 0):
            prev_match = preliminary_matches[i - 1]
            is_prev_operand = (
                prev_match.replace('.', '').replace('-', '').isdigit() or prev_match in CONSTANTS_FLAT or prev_match == ')'
            )
            is_at_end = (i == len(preliminary_matches) - 1)
            next_is_operator = (not is_at_end and preliminary_matches[i + 1] in OPERATORS_FLAT)
            if is_prev_operand and (is_at_end or next_is_operator):
                matches.append('-')
                matches.append(match[1:])
            else:
                matches.append(match)
        else:
            matches.append(match)

    if DEBUG:
        print_line("FINDING MATCHES")
        print(f"input text: {text}")
        print(f"preliminary matches: {preliminary_matches}")
        print(f"final matches: {matches}")
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
            if token in OPERATORS_FLAT:
                split_sympy.append(token)
            else:
                split_sympy.append(sympy.sympify(token))
        return split_sympy

    split_sympy = sympify(split)
    # ITERATE OVER CONSTANTS FIRST
    for constant in CONSTANTS_FLAT:
        count = split.count(constant)
        for _ in range(count):
            indices = numpy.where(array == constant)[0]
            for index in indices:
                if DEBUG:
                    print_line(f"CALCULATING CONSTANT")
                    print(f"constant: {constant}")
                constant_value = CONSTANTS_FLAT[constant]
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
    for function in FUNCTIONS_FLAT:
        count = split.count(function)
        for _ in range(count):
            indices = numpy.where(array == function)[0]
            for index in indices:
                if DEBUG:
                    print_line(f"CALCULATING FUNCTION")
                result = FUNCTIONS_FLAT[function](split_sympy[index + 1])
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
    sorted_operators = sorted(set(ALL_OPERATOR_SYMBOLS), key=lambda x: PRECEDENCE_FLAT.get(x, 5), reverse=True)
    for operator in sorted_operators:
        count = split.count(operator)
        for _ in range(count):
            indices = numpy.where(array == operator)[0]
            for index in indices:
                if DEBUG:
                    print_line(f"CALCULATING OPERATOR")
                operator_func = OPERATORS_FLAT.get(operator)
                if operator_func is None:
                    continue
                result = operator_func(split_sympy[index - 1], split_sympy[index + 1])
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
        FormatCodes.print(f"[b](Possible functions:)")
        for key in FUNCTIONS.keys():
            if isinstance(key, tuple):
                FormatCodes.print(f"[dim](•) {'[dim](,) '.join(key)}")
            else:
                FormatCodes.print(f"[dim](•) {key}")
        FormatCodes.print(f"\n[b](Possible constants:)")
        for key in CONSTANTS.keys():
            if isinstance(key, tuple):
                FormatCodes.print(f"[dim](•) {'[dim](,) '.join(key)}")
            else:
                FormatCodes.print(f"[dim](•) {key}")
        FormatCodes.print(f"\n[b](Possible operators:)")
        for key in OPERATORS.keys():
            if isinstance(key, tuple):
                FormatCodes.print(f"[dim](•) {'[dim](,) '.join(key)}")
            else:
                FormatCodes.print(f"[dim](•) {key}")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_overwrite("[b|br:red](⨯)\n")
    except Exception as e:
        Console.fail(e, start="\n\n", end="\n\n")
