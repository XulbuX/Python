# Agent Guidelines for Python Repository

When working on this repository, any AI agent or automated assistant must adhere strictly to the following rules to maintain the codebase's integrity, performance, and correctness.

## 1. Strict Typing

All Python code across this repository must be meticulously and strictly type-hinted to pass Pyright strict type checking. Do not ever use `Any` unless it is fundamentally impossible to type-hint otherwise. All changes must be fully statically analyzable.

## 2. Validation & Testing

After making any changes, you must validate them by running the full suite of formatters, linters, type checkers, and tests. Fix all problems until they are completely resolved.
*   **Format & Lint:** Run `ruff format .` and `ruff check . --fix`.
*   **Type Check:** Run `pyright`.
*   **Tests:** If tests are present in the project or directory being modified, run `pytest`.
*   Use the `test` skill for testing guidelines and commands, and the `docs` skill for documentation standards.

## 3. Ask, Don't Assume

If you run into anything you are not sure about (ambiguous requirements, complex architectural decisions, edge cases), **ask first**. Do not make assumptions about the desired behavior.

## 4. Performance & Python Idioms

*   **Performance First:** Prioritize speed and modernity. Avoid eager imports for heavy operations. Utilize lazy loading where appropriate.
*   **Optimization Guidelines:**
    *   **Generators:** Avoid passing generator expressions to functions like `any()`, `all()`, `sum()`, `max()`, `min()`, `join()`, `tuple()`, etc.
        *   For full iterations (`join`, `sum`, `tuple`, `max`), ALWAYS wrap them in brackets `[]` to force an optimized list comprehension.
        *   For short-circuiting functions (`any`, `all`, `next`), write explicit unrolled native `for`-loops with `break` or `return`.
    *   **Membership Testing:** Always use `set`s for `in` checks instead of lists or tuples (e.g., `if x in {"a", "b"}:` instead of `if x in ("a", "b"):`).
    *   **String Concatenation:** Avoid using `+=` for string concatenation inside loops; prefer `.join()` with list comprehensions.
    *   **Map & Filter:** Do not use the `map()` or `filter()` builtins. List comprehensions are strictly faster and type-safer.
*   **DRY Principle (Don't Repeat Yourself):** Always strive to prevent redundant code and duplicate logic. Abstract repeated patterns into reusable helper functions or classes.
*   **Internal Module Aliasing:** When importing internal modules, use the `_module` suffix pattern (e.g., `from . import data as _data_module`). This prevents naming collisions and variable shadowing, and keeps the namespace clean of internal clutter.

## 5. Code Structure & Readability

*   **Logical Placement:** Do not mindlessly append new code (variables, constants, functions, classes, etc.) to the end of a file. Always insert new code in a logical location that groups related functionality together.
*   **Private Constants Placement:** Private constants and module-level variables (e.g., `_PATTERNS`, caches, lookup tables) should always be defined directly below the imports at the very top of the file.
*   **Spacing & Formatting:** Keep the code "spacy" and readable, matching the current formatting conventions of the repository.
*   **Imports Placement:** Always place imports at the top of the file. The only exception is OS-specific libraries (such as `winreg`, `msvcrt`, `termios`, or `tty`) that do not exist on other operating systems and therefore must be imported inside platform-specific code branches.
*   **Explicit Import Styles:** For libraries like `typing`, `typing_extensions`, `collections.abc`, and `pathlib`, always use explicit `from <module> import ...` statements (e.g., `from typing import overload, Any`, `from pathlib import Path`). Never import the entire module as `import typing` or `import pathlib`.
*   **Naming Conventions:**
    *   **Descriptive Variable Names:** Single-letter variables (e.g., `x`, `c`, `r`) are strictly banned. The ONLY exceptions are `i` (and rarely `j`) for loop indices, and `n` for mathematical counts/parameters. Always use fully descriptive variable names (e.g., `ch` or `channel`, `red`, `modifier`).
    *   **Instance Conversions & Representations:** Instance methods that convert or represent the object in another format or representation must always use the **`as_…()`** prefix (e.g., `.as_dict()`, `.as_tuple()`, `.as_list()`). Never use `.to_…()` or bare data structure names like `.dict()` or `.values()`.
    *   **Standalone Conversions & Transformations:** Standalone functions should use **`to_…`** (or `…_to_…`) when actively transforming data from one format/casing/type to another (e.g., `to_camel_case()`, `to_delimited_case()`, `to_type()`), and **`as_…`** (or `…_as_…`) when casting or interpreting an arbitrary input object as a target concept or model. Choose whichever sounds most natural and logical in context.
    *   **Extraction vs. Conversion:** Functions that search/parse values out of arbitrary text or unstructured data must use the **`extract_…`** prefix (e.g., `extract_urls()`, `extract_tokens()`), reserving direct `to_…` / `as_…` naming strictly for direct conversions.
    *   **Verb-First for Actions & Getters:** Functions performing actions or fetching data should start with an active verb (e.g., `count_chars()`, `get_paths()`, `remove_duplicates()`).
    *   **Path Resolution:** Always use standard filesystem terminology like **`resolve_path`** and **`resolve_or_create_path`** instead of non-standard terms like `extend_path`.
    *   **Predicates & Booleans:** Predicate functions and boolean properties/methods must always start with `is_` or `has_` (e.g., `is_valid()`, `has_permission()`, `is_tty()`).
*   **Walrus Operator (`:=`):** Use the walrus operator (`:=`) wherever applicable and where it does not hurt readability. Specifically, when assigning a variable that is immediately evaluated in an `if` (or `while`) condition and reused, inline the assignment directly into the condition (e.g., `if (result := process_whatever(input_val)) is None:` instead of assigning `result` on the preceding line). Ensure that when used with compound short-circuiting operators (`and` / `or`), the assignment is guaranteed to evaluate before any subsequent access.
*   **Single-Use Variables & Inlining:** Avoid assigning values to temporary variables that are only accessed once. Pass expressions directly into the consuming function, return statement, or assertion (e.g., `print(process_whatever(arg))` instead of `result = process_whatever(arg); print(result)`).
    *   **Exceptions:** Assigning a single-use variable is acceptable and encouraged when inlining would cause an expression to become overly convoluted, hurt readability, or force an otherwise clean call across four or more lines (e.g., complex multi-branch ternaries or calculations), or when caching a costly property or calculation outside a loop to avoid redundant re-evaluations during iteration.
*   **Organization:** When introducing large data structures (like hardcoded iterables or dictionaries), keep them strictly organized and structured. Default to sorting elements alphabetically unless a specific logical order is required.

## 6. Documentation & Markdown Formatting

*   **Markdown Linting:** All Markdown files (`.md`) must strictly adhere to the formatting and linting rules defined in `.markdownlint.json`.
*   **Docstrings & Comments:** Follow the `docs` skill for all docstring structure, styling, `<br>` line wraps, horizontal rules, and comment conventions. Numbered step comments must always use square brackets like `# [1]`, `# [2]` (never `1.`, `2.`). Always provide at least a one-line docstring for private variables, functions, and classes explaining their purpose.
