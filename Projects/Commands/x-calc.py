#!/usr/bin/env python3
"""Do advanced calculations from the command line.
Supports a wide range of mathematical operations, functions and constants.
There's no number size limit - the only limit is your system's memory."""
from xulbux import FormatCodes, Console
from typing import Callable, Optional
import sympy
import numpy
import sys
import re


ARGS = Console.get_args({
    "calculation": "before",
    "ans": ["-a", "--ans"],
    "precision": ["-p", "--precision"],
    "format": ["-f", "--format"],
    "debug": ["-d", "--debug"],
})
DEBUG = ARGS.debug.exists

sys.set_int_max_str_digits(0)  # 0 = NO LIMIT
sanitize = lambda a: sympy.sympify(a)


def clean_number(token: str) -> str:
    """Remove underscores from numeric tokens for proper parsing."""
    if token.replace(".", "").replace("-", "").replace("_", "").isdigit():
        return token.replace("_", "")
    return token


class OPERATORS:

    # ARITHMETIC OPERATORS
    MINUS = ("o:minus", ["-", "−"])
    PLUS = ("o:plus", ["+", "＋"])
    MULTIPLY = ("o:multiply", ["*", "×", "∗", "·"])
    DIVIDE = ("o:divide", ["/", "÷"])
    FLOOR_DIVIDE = ("o:floor_divide", ["//", "⌊/⌋"])
    MODULO = ("o:modulo", ["%", "mod"])
    POWER = ("o:power", ["**", "^"])
    # LOGIC OPERATORS
    AND = ("o:and", ["and", "&&", "∧"])
    OR = ("o:or", ["or", "||", "∨"])
    NOT = ("o:not", ["not", "!", "¬"])
    XOR = ("o:xor", ["xor", "⊻"])
    # POSTFIX OPERATORS
    FACTORIAL = ("o:factorial", ["!"])
    # COMPARISON OPERATORS
    EQUALS = ("o:equals", ["eq", "=", "==", "≡"])
    NOT_EQUALS = ("o:not_equals", ["ne", "!=", "≠", "<>"])
    LESS_THAN = ("o:less_than", ["lt", "<", "＜"])
    LESS_THAN_EQUAL = ("o:less_equal_than", ["le", "<=", "≤", "⩽"])
    GREATER_THAN = ("o:greater_than", ["gt", ">", "＞"])
    GREATER_THAN_EQUAL = ("o:greater_equal_than", ["ge", ">=", "≥", "⩾"])

    ALL = (
        MINUS, PLUS, MULTIPLY, DIVIDE, FLOOR_DIVIDE, MODULO, POWER, AND, OR, NOT, XOR, FACTORIAL, EQUALS, NOT_EQUALS,
        LESS_THAN, LESS_THAN_EQUAL, GREATER_THAN, GREATER_THAN_EQUAL
    )
    ALL_TOKENS: tuple[str, ...] = tuple(token for _, tokens in ALL for token in tokens)

    PRECEDENCE: dict[str | tuple[str, ...], int] = {
        # HIGHER VALUES REPRESENT HIGHER PRECEDENCE
        FACTORIAL[0]: 5,
        POWER[0]: 4,
        (MULTIPLY[0], DIVIDE[0], FLOOR_DIVIDE[0], MODULO[0]): 3,
        (PLUS[0], MINUS[0]): 2,
        AND[0]: 1,
        OR[0]: 0,
        (EQUALS[0], NOT_EQUALS[0], LESS_THAN[0], LESS_THAN_EQUAL[0], GREATER_THAN[0], GREATER_THAN_EQUAL[0]): -1,
        NOT[0]: -2,
        XOR[0]: -3,
    }

    IMPLEMENT: dict[str, Callable] = {
        # ARITHMETIC OPERATORS
        MINUS[0]: lambda a, b: sympy.Add(sanitize(a), sympy.Mul(sanitize(b), sympy.Integer(-1))),
        PLUS[0]: lambda a, b: sympy.Add(sanitize(a), sanitize(b)),
        MULTIPLY[0]: lambda a, b: sympy.Mul(sanitize(a), sanitize(b)),
        DIVIDE[0]: lambda a, b: sympy.Mul(sanitize(a), sympy.Pow(sanitize(b), -1)),
        FLOOR_DIVIDE[0]: lambda a, b: sympy.floor(sympy.Mul(sanitize(a), sympy.Pow(sanitize(b), -1))),
        MODULO[0]: lambda a, b: sympy.Mod(sanitize(a), sanitize(b)),
        POWER[0]: lambda a, b: sympy.Pow(sanitize(a), sanitize(b)),
        # LOGIC OPERATORS
        AND[0]: lambda a, b: 1 if (bool(a) and bool(b)) else 0,
        OR[0]: lambda a, b: 1 if (bool(a) or bool(b)) else 0,
        NOT[0]: lambda a, _: 1 if not bool(a) else 0,
        XOR[0]: lambda a, b: 1 if ((bool(a) and not bool(b)) or (not bool(a) and bool(b))) else 0,
        # POSTFIX OPERATORS
        FACTORIAL[0]: lambda a, _: sympy.factorial(sanitize(a)),
        # COMPARISON OPERATORS
        EQUALS[0]: lambda a, b: 1 if a == b else 0,
        NOT_EQUALS[0]: lambda a, b: 1 if a != b else 0,
        LESS_THAN[0]: lambda a, b: 1 if a < b else 0,
        LESS_THAN_EQUAL[0]: lambda a, b: 1 if a <= b else 0,
        GREATER_THAN[0]: lambda a, b: 1 if a > b else 0,
        GREATER_THAN_EQUAL[0]: lambda a, b: 1 if a >= b else 0,
    }

    @classmethod
    def get(cls, operator_id: str):
        """Get the operator function by operator ID."""
        return cls.IMPLEMENT.get(operator_id)

    @classmethod
    def get_id(cls, token: str) -> str | None:
        """Get the operator ID for a token by searching through the token lists."""
        for op_id, symbols in cls.ALL:
            if token in symbols: return op_id
        return None

    @classmethod
    def is_operator(cls, token: str) -> bool:
        """Check if a token is an operator by searching through the token lists."""
        return cls.get_id(token) is not None

    @classmethod
    def get_precedence(cls, operator_id: str) -> int:
        """Get the operator precedence by operator ID."""
        for keys, val in cls.PRECEDENCE.items():
            if isinstance(keys, tuple):
                if operator_id in keys: return val
            else:
                if operator_id == keys: return val
        return 5  # DEFAULT


class CONSTANTS:

    # MATHEMATICAL CONSTANTS
    ANS = ("c:ans", ["ans", "answer"])
    E = ("c:e", ["e", "euler"])
    INF = ("c:inf", ["inf", "infinity", "∞"])
    PI = ("c:pi", ["pi", "π"])
    TAU = ("c:tau", ["tau", "τ"])
    PHI = ("c:phi", ["phi", "φ", "golden"])

    ALL = (ANS, E, INF, PI, TAU, PHI)
    ALL_TOKENS: tuple[str, ...] = tuple(token for _, tokens in ALL for token in tokens)

    IMPLEMENT: dict[str, object] = {
        ANS[0]: ARGS.ans.value,
        E[0]: sympy.E,
        INF[0]: sympy.oo,
        PI[0]: sympy.pi,
        TAU[0]: 2 * sympy.pi,
        PHI[0]: sympy.GoldenRatio,
    }

    @classmethod
    def get(cls, constant_id: str):
        """Get the constant function by constant ID."""
        return cls.IMPLEMENT.get(constant_id)

    @classmethod
    def get_id(cls, token: str) -> str | None:
        """Get the constant ID for a token by searching through the token lists."""
        for const_id, symbols in cls.ALL:
            if token in symbols: return const_id
        return None

    @classmethod
    def is_constant(cls, token: str) -> bool:
        """Check if a token is a constant by searching through the token lists."""
        return cls.get_id(token) is not None


class FUNCTIONS:

    # PROGRAMMING FUNCTIONS
    ABS = ("f:abs", ["abs", "absolute", "magnitude"])
    FLOOR = ("f:floor", ["floor"])
    CEIL = ("f:ceil", ["ceil", "ceiling"])
    ROUND = ("f:round", ["round"])
    SIGN = ("f:sign", ["sign", "sgn"])
    # LOGARITHMIC FUNCTIONS
    LOG = ("f:log", ["log", "log10", "logarithm"])
    LN = ("f:ln", ["ln", "log_e", "natural_log", "loge"])
    LOG2 = ("f:log2", ["log2", "log_2"])
    EXP = ("f:exp", ["exp", "exponential"])
    # TRIGONOMETRIC FUNCTIONS
    RAD = ("f:rad", ["rad", "radians", "to_radians"])
    DEG = ("f:deg", ["deg", "degrees", "to_degrees"])
    SIN = ("f:sin", ["sin", "sine"])
    ASIN = ("f:asin", ["asin", "arcsin", "arcsine", "sin_inv"])
    COS = ("f:cos", ["cos", "cosine"])
    ACOS = ("f:acos", ["acos", "arccos", "arccosine", "cos_inv"])
    TAN = ("f:tan", ["tan", "tangent"])
    ATAN = ("f:atan", ["atan", "arctan", "arctangent", "tan_inv"])
    # HYPERBOLIC FUNCTIONS
    SINH = ("f:sinh", ["sinh", "hyperbolic_sine"])
    COSH = ("f:cosh", ["cosh", "hyperbolic_cosine"])
    TANH = ("f:tanh", ["tanh", "hyperbolic_tangent"])
    ASINH = ("f:asinh", ["asinh", "arcsinh", "inverse_sinh"])
    ACOSH = ("f:acosh", ["acosh", "arccosh", "inverse_cosh"])
    ATANH = ("f:atanh", ["atanh", "arctanh", "inverse_tanh"])
    # ADDITIONAL FUNCTIONS
    FAC = ("f:fac", ["fac", "factorial", "fact"])
    SQRT = ("f:sqrt", ["sqrt", "square_root", "√"])
    CBRT = ("f:cbrt", ["cbrt", "cube_root", "∛"])
    # STATISTICAL FUNCTIONS
    MIN = ("f:min", ["min", "minimum"])
    MAX = ("f:max", ["max", "maximum"])

    ALL = (
        ABS, FLOOR, CEIL, ROUND, SIGN, LOG, LN, LOG2, EXP, RAD, DEG, SIN, ASIN, COS, ACOS, TAN, ATAN, SINH, COSH, TANH, ASINH,
        ACOSH, ATANH, FAC, SQRT, CBRT, MIN, MAX
    )
    ALL_TOKENS: tuple[str, ...] = tuple(token for _, tokens in ALL for token in tokens)

    IMPLEMENT: dict[str, Callable[[object], object]] = {
        # PROGRAMMING FUNCTIONS
        ABS[0]: lambda a: abs(sanitize(a)),
        FLOOR[0]: lambda a: sympy.floor(sanitize(a)),
        CEIL[0]: lambda a: sympy.ceiling(sanitize(a)),
        ROUND[0]: lambda a: sympy.floor(sanitize(a) + sympy.Rational(1, 2)),
        SIGN[0]: lambda a: sympy.sign(sanitize(a)),
        # LOGARITHMIC FUNCTIONS
        LOG[0]: lambda a: sympy.log(sanitize(a), 10),
        LN[0]: lambda a: sympy.log(sanitize(a)),
        LOG2[0]: lambda a: sympy.log(sanitize(a), 2),
        EXP[0]: lambda a: sympy.exp(sanitize(a)),
        # TRIGONOMETRIC FUNCTIONS
        RAD[0]: lambda a: sympy.rad(sanitize(a)),
        DEG[0]: lambda a: sympy.deg(sanitize(a)),
        SIN[0]: lambda a: sympy.sin(sanitize(a)),
        ASIN[0]: lambda a: sympy.asin(sanitize(a)),
        COS[0]: lambda a: sympy.cos(sanitize(a)),
        ACOS[0]: lambda a: sympy.acos(sanitize(a)),
        TAN[0]: lambda a: sympy.tan(sanitize(a)),
        ATAN[0]: lambda a: sympy.atan(sanitize(a)),
        # HYPERBOLIC FUNCTIONS
        SINH[0]: lambda a: sympy.sinh(sanitize(a)),
        COSH[0]: lambda a: sympy.cosh(sanitize(a)),
        TANH[0]: lambda a: sympy.tanh(sanitize(a)),
        ASINH[0]: lambda a: sympy.asinh(sanitize(a)),
        ACOSH[0]: lambda a: sympy.acosh(sanitize(a)),
        ATANH[0]: lambda a: sympy.atanh(sanitize(a)),
        # ADDITIONAL FUNCTIONS
        FAC[0]: lambda a: sympy.factorial(sanitize(a)),
        SQRT[0]: lambda a: sympy.sqrt(sanitize(a)),
        CBRT[0]: lambda a: sympy.Pow(sanitize(a), sympy.Rational(1, 3)),
        # STATISTICAL FUNCTIONS
        MIN[0]: lambda a: sanitize(a),
        MAX[0]: lambda a: sanitize(a),
    }

    @classmethod
    def get(cls, function_id: str):
        """Get the function lambda by function ID."""
        return cls.IMPLEMENT.get(function_id)

    @classmethod
    def get_id(cls, token: str) -> str | None:
        """Get the function ID for a token by searching through the token lists."""
        for func_id, symbols in cls.ALL:
            if token in symbols: return func_id
        return None

    @classmethod
    def is_function(cls, token: str) -> bool:
        """Check if a token is a function by searching through the token lists."""
        return cls.get_id(token) is not None


PATTERN = re.compile(
    r"[a-z]+|" + "|".join(map(re.escape, OPERATORS.MINUS[1])) + r"\d+(?:_\d+)*\.\d+(?:_\d+)*|" + "|".join(map(re.escape, OPERATORS.MINUS[1]))
    + r"\d+(?:_\d+)*|" + r"\d+(?:_\d+)*\.\d+(?:_\d+)*|\d+(?:_\d+)*|" + r"\(|\)|" + "|"
    .join(map(re.escape, sorted(OPERATORS.ALL_TOKENS + CONSTANTS.ALL_TOKENS + FUNCTIONS.ALL_TOKENS, key=len, reverse=True)))
)


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


class Calc:

    def __init__(self, calc_str: str, last_ans: Optional[str] = None, precision: int = 110, max_num_len: int = 100):
        self.calc_str = calc_str
        self.last_ans = last_ans
        self.precision = precision
        self.max_num_len = max_num_len
        self.inf_precision = (precision == -1)

    def __str__(self) -> str:
        return self.calc_str

    def __repr__(self) -> str:
        return f"Calc(calc_str={self.calc_str!r}, last_ans={self.last_ans!r}, precision={self.precision}, max_num_len={self.max_num_len})"

    def eval(self) -> str:
        if DEBUG:
            clear_lines()
            print()
            print_line(f"NEW CALCULATION")
            print(f"raw calculation string:\n>>> {self.calc_str}")
        else:
            print_overwrite("[dim|white](calculating...)", end="")

        # SKIP PRECISION ADJUSTMENTS FOR INFINITE PRECISION (-1)
        if not self.inf_precision and self.precision <= self.max_num_len:
            self.max_num_len = self.precision
            self.precision += 10
        norm_calc_str = str(self.calc_str.strip()).replace(" ", "").lower()

        if DEBUG:
            print(f"normalized calculation string:\n>>> {norm_calc_str}")
            print(f"precision: {self.precision}")
            print(f"max number length: {self.max_num_len}")

        self.last_ans = self._perform_eval(norm_calc_str)
        return self.format_readability(self.last_ans)

    def format_result(self, result: object) -> str:
        if DEBUG:
            print_line("FORMAT RESULT")
            print(f"result: {result}")
            print(f"precision: {self.precision} (infinite: {self.inf_precision})")

        # FOR INFINITE PRECISION, JUST CONVERT TO STRING WITHOUT FORMATTING
        if self.inf_precision:
            result_str = str(result)
            if DEBUG:
                print(f"infinite precision result: {result_str}")
            return result_str

        # CHECK IF RESULT IS AN EXACT INTEGER TO AVOID FLOAT PRECISION ERRORS
        is_exact_integer = False
        try:
            if hasattr(result, 'is_integer') and getattr(result, 'is_integer', False):
                is_exact_integer = True
            elif isinstance(result, sympy.Integer):
                is_exact_integer = True
            elif hasattr(result, 'is_Integer') and getattr(result, 'is_Integer', False):
                is_exact_integer = True
            elif isinstance(result, int):
                is_exact_integer = True
        except:
            pass

        if is_exact_integer:
            result_str = str(result)
            if DEBUG:
                print(f"exact integer result (preserving for formatting): {result_str}")
        else:
            try:
                result_str = "{:.{}f}".format(result, self.precision)
                result_str = (result_str.rstrip("0").rstrip(".") if "." in result_str else result_str)
            except OverflowError:
                result_str = str(result)
            if DEBUG:
                print(f"formatted decimal result: {result_str}")

        return result_str

    def format_readability(self, num_str: str) -> str:
        if not DEBUG:
            print_overwrite("[dim|white](formatting...)", end="")
        num_str = str(num_str)
        
        # FORMAT WITH THOUSANDS SEPARATORS IF REQUESTED
        if ARGS.format.exists:
            if DEBUG:
                print_line("FORMATTING WITH SEPARATORS")
                print(f"should format: {ARGS.format.exists}")
            if ARGS.format.value is None:
                sep = ","
            else:
                sep = str(ARGS.format.value)
            if DEBUG:
                print(f"separator: '{sep}'")
                print(f"input num_str: '{num_str}'")
            if "." in num_str:
                int_part, decimal_part = num_str.split(".", 1)
                if int_part.lstrip("-").isdigit() and len(int_part.lstrip("-")) > 3:
                    formatted_int = ""
                    sign = "-" if int_part.startswith("-") else ""
                    digits = int_part.lstrip("-")
                    for i, digit in enumerate(reversed(digits)):
                        if i > 0 and i % 3 == 0:
                            formatted_int = sep + formatted_int
                        formatted_int = digit + formatted_int
                    num_str = sign + formatted_int + "." + decimal_part
                    if DEBUG:
                        print(f"formatted decimal number: '{num_str}'")
            else:
                if num_str.lstrip("-").isdigit() and len(num_str.lstrip("-")) > 3:
                    formatted_num = ""
                    sign = "-" if num_str.startswith("-") else ""
                    digits = num_str.lstrip("-")
                    for i, digit in enumerate(reversed(digits)):
                        if i > 0 and i % 3 == 0:
                            formatted_num = sep + formatted_num
                        formatted_num = digit + formatted_num
                    num_str = sign + formatted_num
                    if DEBUG:
                        print(f"formatted whole number: '{num_str}'")

        # TRUNCATE REPEATING DECIMAL (skip for infinite precision)
        if not self.inf_precision and len(num_str) > self.max_num_len and "." in num_str:
            num_str = num_str[:-10]
            int_part, decimal_part = num_str.split(".")
            short_decimal_part = decimal_part[:self.max_num_len]
            if DEBUG:
                print_line(f"TRUNCATING REPEATING DECIMAL")
                print(f"input string: {num_str}")
                print(f"decimal part: {short_decimal_part}")

            if self._is_recurring(short_decimal_part):
                num_str = f"{int_part}.{short_decimal_part}..."
            else:
                num_str = f"{int_part}.{short_decimal_part}"
            if DEBUG:
                print(f"formatted string: {num_str}")

        # FORMAT LONG NUMBERS TO EXPONENTS (skip for infinite precision)
        elif not self.inf_precision and len(num_str) > self.max_num_len:
            if DEBUG:
                print_line(f"FORMATTING LONG NUMBERS TO EXPONENTS")
                print(f"input string: {num_str}")
            num_str = self._format_exponents(num_str)
            if DEBUG:
                print(f"formatted string: {num_str}")
        return num_str

    def _format_exponents(self, string: str) -> str:
        pattern = re.compile(r"(\d*\.\d+|\d+)(?![\de])")

        def replace_match(match):
            number_sequence = match.group(1)
            if len(str(number_sequence)) <= self.max_num_len:
                return number_sequence
            base = number_sequence[:self.max_num_len]
            exponent_value = len(number_sequence) - self.max_num_len
            if exponent_value >= 0:
                sign = "+"
            else:
                sign = "-"
            exponent_form = base + "e" + sign + str(abs(exponent_value))
            return exponent_form

        formatted_str = re.sub(pattern, replace_match, string)
        return formatted_str

    def _is_recurring(self, string: str, max_check_loops: int = -1) -> list | bool:
        repts = list(self._get_rept(string))
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

    @staticmethod
    def _get_rept(string: str):
        r = re.compile(r"(.+?)\1+")
        for match in r.finditer(string):
            yield match.group(1)

    def _convert_ids_to_symbols(self, tokens: list) -> str:
        """Convert operator/constant/function IDs back to symbols for sympy evaluation."""
        result = []
        for token in tokens:
            if isinstance(token, str):
                if token.startswith("o:"):
                    for op_id, symbols in OPERATORS.ALL:
                        if op_id == token:
                            result.append(symbols[0])
                            break
                    else:
                        result.append(token)
                elif token.startswith("c:"):
                    for const_id, symbols in CONSTANTS.ALL:
                        if const_id == token:
                            result.append(symbols[0])
                            break
                    else:
                        result.append(token)
                elif token.startswith("f:"):
                    for func_id, symbols in FUNCTIONS.ALL:
                        if func_id == token:
                            result.append(symbols[0])
                            break
                    else:
                        result.append(token)
                else:
                    result.append(token)
            else:
                result.append(str(token))
        return "".join(result)

    def _find_matches(self, text: str) -> list:
        preliminary_matches = [match for match in PATTERN.findall(text) if match]  # FILTER OUT EMPTY STRINGS
        matches = []
        i = 0
        while i < len(preliminary_matches):
            match = preliminary_matches[i]
            # CHECK IF THIS IS A MINUS SIGN THAT SHOULD BE COMBINED WITH THE NEXT NUMBER
            if (match in OPERATORS.MINUS[1] and i + 1 < len(preliminary_matches)
                    and preliminary_matches[i + 1].replace(".", "").replace("_", "").isdigit()):
                # CHECK IF THIS SHOULD BE TREATED AS A NEGATIVE NUMBER (NOT SUBTRACTION)
                should_be_negative = False
                if i == 0:  # AT THE BEGINNING
                    should_be_negative = True
                else:
                    prev_match = preliminary_matches[i - 1]
                    # IF PREVIOUS TOKEN IS AN OPERATOR OR OPEN PARENTHESIS, TREAT AS NEGATIVE NUMBER
                    if (OPERATORS.is_operator(prev_match) or prev_match == "(" or FUNCTIONS.is_function(prev_match)):
                        should_be_negative = True

                if should_be_negative:
                    # COMBINE MINUS WITH NEXT NUMBER AND CLEAN UNDERSCORES
                    matches.append(clean_number(match + preliminary_matches[i + 1]))
                    i += 2  # SKIP THE NEXT TOKEN SINCE WE CONSUMED IT
                else:
                    # KEEP AS SEPARATE SUBTRACTION OPERATOR
                    matches.append(match)
                    i += 1
            # DISTINGUISH BETWEEN 'FACTORIAL' AND 'NOT'
            elif match == "!":
                should_be_factorial = False
                if i > 0:
                    prev_match = preliminary_matches[i - 1]
                    # IF PREVIOUS TOKEN IS A NUMBER, CLOSING PARENTHESIS, OR CONSTANT, TREAT AS FACTORIAL
                    if (prev_match.replace(".", "").replace("-", "").replace("_", "").isdigit() or prev_match == ")"
                            or CONSTANTS.is_constant(prev_match)):
                        should_be_factorial = True
                if should_be_factorial:
                    matches.append(OPERATORS.FACTORIAL[0])
                else:
                    matches.append(OPERATORS.NOT[0])
                i += 1
            else:
                # CONVERT TOKENS TO IDS FOR OPERATORS, CONSTANTS AND FUNCTIONS
                if OPERATORS.is_operator(match):
                    matches.append(OPERATORS.get_id(match))
                elif CONSTANTS.is_constant(match):
                    matches.append(CONSTANTS.get_id(match))
                elif FUNCTIONS.is_function(match):
                    matches.append(FUNCTIONS.get_id(match))
                else:
                    # CLEAN UNDERSCORES FROM NUMERIC TOKENS
                    matches.append(clean_number(match))
                i += 1

        if DEBUG:
            print_line("FINDING MATCHES")
            print(f"input text: {text}")
            print(f"preliminary matches: {preliminary_matches}")
            print(f"final matches: {matches}")
        return matches

    def _perform_eval(self, calc_str: str) -> str:
        """Internal recursive calculation function that doesn't do preprocessing."""
        SAVE_CALC_STR = calc_str

        # HANDLE PARENTHESES - SKIP FUNCTION CALLS
        for _ in range(calc_str.count("(")):
            start = calc_str.rfind("(") + 1
            end = calc_str.find(")", start)
            if start == 0 or end == -1:
                break

            before_paren = calc_str[:start - 1].strip()
            is_function_call = any(before_paren.endswith(token) for _, symbols in FUNCTIONS.ALL for token in symbols)
            if is_function_call:
                break

            formatted_result = calc_str[start:end]
            before_paren_pos = start - 2
            should_add_mult = (before_paren_pos >= 0 and calc_str[before_paren_pos].isdigit())
            calc_str = calc_str.replace(
                "(" + formatted_result + ")",
                (OPERATORS.MULTIPLY[1][0] if should_add_mult else "") + str(self._perform_eval(formatted_result)),
            )

        numpy.set_printoptions(floatmode="fixed", formatter={"float_kind": "{:f}".format})  # HANDLE SCIENTIFIC NOTATION
        split = self._find_matches(calc_str)

        # CONVERT ALL OPERANDS TO 'SymPy' EXPRESSIONS
        def sympify(split_matches: list) -> list:
            split_sympy = []
            for token in split_matches:
                if isinstance(token, str) and (token.startswith(("o:", "c:", "f:"))):
                    split_sympy.append(token)
                else:
                    try:
                        split_sympy.append(sympy.sympify(token))
                    except:
                        split_sympy.append(token)
            return split_sympy

        split_sympy = sympify(split)

        # ITERATE OVER CONSTANTS FIRST
        for c_id, _ in CONSTANTS.ALL:
            while c_id in split:
                index = split.index(c_id)
                if DEBUG:
                    print_line(f"CALCULATING CONSTANT")
                    print(f"constant ID: {c_id}")
                constant_value = CONSTANTS.get(c_id)
                if c_id == CONSTANTS.ANS[0] and constant_value is None:
                    raise Exception("Answer constant was not specified")
                if DEBUG:
                    print(f"value: {constant_value}")
                formatted_result = str(self.format_result(constant_value))
                new_split = split[:index] + [formatted_result] + split[index + 1:]
                split = new_split
                split_sympy = sympify(split)

        # ITERATE OVER FUNCTIONS AVAILABLE
        for f_id, _ in FUNCTIONS.ALL:
            while f_id in split:
                index = split.index(f_id)

                if (index + 1 < len(split) and split[index + 1] == "("):
                    paren_count = 0
                    end_paren_index = -1
                    for i in range(index + 1, len(split)):
                        if split[i] == "(":
                            paren_count += 1
                        elif split[i] == ")":
                            paren_count -= 1
                            if paren_count == 0:
                                end_paren_index = i
                                break

                    if end_paren_index == -1:
                        break
                    arg_tokens = split[index + 2:end_paren_index]

                    if DEBUG:
                        print_line(f"CALCULATING FUNCTION")
                        print(f"function ID: {f_id}")
                        print(f"arg_tokens: {arg_tokens}")

                    if len(arg_tokens) == 1:
                        arg_value = split_sympy[index + 2]
                    else:
                        arg_str = self._convert_ids_to_symbols(arg_tokens)
                        if DEBUG:
                            print(f"evaluating arg expression: {arg_str}")
                        arg_value = sympy.sympify(arg_str)

                    function_impl = FUNCTIONS.get(f_id)
                    if function_impl is None:
                        break
                    result = function_impl(arg_value)
                    if DEBUG:
                        print(f"argument value: {arg_value}")
                        print(f"result: {result}")
                    formatted_result = str(self.format_result(result))
                    new_split = split[:index] + [formatted_result] + split[end_paren_index + 1:]
                    split = new_split
                    split_sympy = sympify(split)

                elif index + 1 < len(split):
                    function_impl = FUNCTIONS.get(f_id)
                    if function_impl is None:
                        break
                    result = function_impl(split_sympy[index + 1])
                    if DEBUG:
                        print_line(f"CALCULATING FUNCTION")
                        print(f"function ID: {f_id}")
                        print(f"argument: {split_sympy[index + 1]}")
                        print(f"result: {result}")
                    formatted_result = str(self.format_result(result))
                    new_split = split[:index] + [formatted_result] + split[index + 2:]
                    split = new_split
                    split_sympy = sympify(split)
                else:
                    break

        # ITERATE OVER OPERATORS BASED ON PRECEDENCE
        while len(split) > 1:
            operator_positions = []
            for i, token in enumerate(split):
                if isinstance(token, str) and token.startswith("o:"):
                    precedence = OPERATORS.get_precedence(token)
                    # GIVE PREFIX 'NOT' HIGHER PRECEDENCE THAN BINARY OPERATORS
                    if (token == OPERATORS.NOT[0] and (i == 0 or isinstance(split[i - 1], str) and
                                                       (split[i - 1].startswith("o:") or split[i - 1] in ["("]))):
                        precedence = 3  # HIGHER THAN BINARY ARITHMETIC OPERATORS
                    operator_positions.append((i, token, precedence))

            if not operator_positions:
                break

            highest_precedence = max(op[2] for op in operator_positions)
            highest_ops = [op for op in operator_positions if op[2] == highest_precedence]
            index, operator_id, _ = highest_ops[-1]

            if DEBUG:
                print_line(f"CALCULATING OPERATOR")
                print(f"operator ID: {operator_id}")

            operator_func = OPERATORS.get(operator_id)
            if operator_func is None:
                break

            if operator_id == OPERATORS.FACTORIAL[0]:
                # POSTFIX FACTORIAL OPERATOR
                if index == 0:
                    break
                result = operator_func(split_sympy[index - 1], None)
                if DEBUG:
                    print(f"argument: {split_sympy[index - 1]}")
                    print(f"operator: {operator_id} (postfix factorial)")
                    print(f"result: {result}")
                new_split = split[:index - 1] + [str(self.format_result(result))] + split[index + 1:]
            elif operator_id == OPERATORS.MINUS[0] and (index == 0 or isinstance(split[index - 1], str)
                                                        and split[index - 1].startswith("o:")):
                # UNARY MINUS
                if index + 1 >= len(split):
                    break
                result = operator_func(0, split_sympy[index + 1])
                if DEBUG:
                    print(f"argument: 0")
                    print(f"operator: {operator_id} (unary minus)")
                    print(f"argument: {split_sympy[index + 1]}")
                    print(f"result: {result}")
                new_split = split[:index] + [str(self.format_result(result))] + split[index + 2:]
            elif operator_id == OPERATORS.NOT[0] and (index == 0 or isinstance(split[index - 1], str) and
                                                      (split[index - 1].startswith("o:") or split[index - 1] in ["("])):
                # PREFIX NOT OPERATOR
                if index + 1 >= len(split):
                    break
                result = operator_func(split_sympy[index + 1], None)
                if DEBUG:
                    print(f"operator: {operator_id} (prefix NOT)")
                    print(f"argument: {split_sympy[index + 1]}")
                    print(f"result: {result}")
                new_split = split[:index] + [str(self.format_result(result))] + split[index + 2:]
            else:
                # BINARY OPERATOR
                if index == 0 or index + 1 >= len(split):
                    break
                result = operator_func(split_sympy[index - 1], split_sympy[index + 1])
                if DEBUG:
                    print(f"argument: {split_sympy[index - 1]}")
                    print(f"operator: {operator_id}")
                    print(f"argument: {split_sympy[index + 1]}")
                    print(f"result: {result}")
                new_split = split[:index - 1] + [str(self.format_result(result))] + split[index + 2:]

            split = new_split
            split_sympy = sympify(split)

        if len(split) == 1:
            calc_str = split[0]
        else:
            calc_str = " ".join(split)
            try:
                result = sympy.sympify(calc_str)
                calc_str = str(self.format_result(result))
            except:
                raise Exception(f"Could not perform calculation on: '{SAVE_CALC_STR}'")

        if calc_str == SAVE_CALC_STR:
            try:
                sympy.sympify(calc_str)
            except:
                raise Exception(f"Could not perform calculation on: '{SAVE_CALC_STR}'")
        return calc_str


def main():
    print()
    if len(calc_str_parts := list(ARGS.calculation.value)) > 0:
        if (precision_value := ARGS.precision.value) is None:
            precision_value = 100
        if precision_value <= 0 and precision_value != -1:
            Console.fail(f"[b](ValueError:) Precision must be positive or -1 for infinite precision, got {precision_value}", end="\n\n")
            return

        if precision_value == -1:
            precision = -1
            max_num_len = -1
        else:
            precision = precision_value + 10
            max_num_len = precision_value
        
        calculation = Calc(
            calc_str=" ".join(str(v) for v in calc_str_parts),
            last_ans=ARGS.ans.value,
            precision=precision,
            max_num_len=max_num_len,
        )
        result = calculation.eval()
        if DEBUG:
            print_line("FINAL RESULT")
            print(f"answer: {result}")
            print_line()
            print()
        else:
            print_overwrite(f"[dim|br:green][b](=) [_dim]{result}[_]")
    else:
        FormatCodes.print(f"[b](Possible operators:)")
        for o_id, symbols in OPERATORS.ALL:
            FormatCodes.print(f"[i|dim]({o_id.split(":")[1]:<22}){'[dim](,) '.join(symbols)}")
        FormatCodes.print(f"\n[b](Possible constants:)")
        for c_id, symbols in CONSTANTS.ALL:
            FormatCodes.print(f"[i|dim]({c_id.split(":")[1]:<22}){'[dim](,) '.join(symbols)}")
        FormatCodes.print(f"\n[b](Possible functions:)")
        for f_id, symbols in FUNCTIONS.ALL:
            FormatCodes.print(f"[i|dim]({f_id.split(":")[1]:<22}){'[dim](,) '.join(symbols)}")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_overwrite("[b|br:red](⨯)\n")
    except RecursionError:
        Console.fail("[b](RecursionError:) Maximum recursion depth exceeded [dim]((possible infinite loop in calculation))", start="\n\n", end="\n\n")
    except MemoryError:
        Console.fail("[b](MemoryError:) The operation ran out of memory", start="\n\n", end="\n\n")
    except OverflowError as e:
        Console.fail(f"[b](OverflowError:) {e}", start="\n\n", end="\n\n")
    except Exception as e:
        Console.fail(e, start="\n\n", end="\n\n")
