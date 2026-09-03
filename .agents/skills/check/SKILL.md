---
name: check
description: Strict guidelines and commands for running formatters, linters, type checkers, and resolving all code quality issues.
---

# check

Use this skill to format, lint, type check, and validate code in this repository. All code must pass all checks with zero errors and zero warnings.

---

## 1. Mandatory Validation After Every Edit

After making any changes across the repository (in `apps`, `commands`, `projects`, or scripts), you MUST validate your changes by running the full suite of formatters, linters, and type checkers. Fix all problems until they are completely resolved. Never assume code is correct without running the checks.

---

## 2. Running Formatters, Linters & Type Checkers

### On Unix (Linux / macOS)

CD into the project root, activate `.venv`, and run:

```bash
ruff format . && ruff check . --fix && pyright
```

### On Windows

CD into the project root and run:

```powershell
ruff format . ; if ($?) { ruff check . --fix } ; if ($?) { pyright }
```

---

## 3. Resolving Errors & Fixing Bugs

-   **Zero Issues Policy:** Every edit session must end with 0 errors, 0 warnings, and 0 lint issues.
-   **Fix Real Bugs in Code:** If a check fails due to an issue or typing mismatch, **fix the code**. Do not suppress or work around real bugs.
-   **No `# type:ignore` Comments:** `# type:ignore` comments are completely forbidden. Only MyPy requires `# type:ignore`, but this repository does not use MyPy. When suppression is fundamentally unavoidable, only use specific `# pyright:ignore[…]` comments for Pyright or `# ruff:ignore[…]` comments for Ruff.
-   **Ignore Comment Formatting:** When using `# pyright:ignore[…]` or `# ruff:ignore[…]` (only when fundamentally unavoidable), **NEVER** put spaces after commas between rule names (e.g., `# pyright:ignore[reportUnknownMemberType,reportAttributeAccessIssue]`). Always specify explicit rule IDs.

---

## 4. Cross-Platform Reliability (Windows & Unix)

All code must be reliable across platforms without platform-dependent crashes:

1.  **Safely Guard Windows-Only Modules (`ctypes.windll`, `msvcrt`, `winreg`):**
    *   On Linux/macOS, `ctypes` has no `windll` attribute, and `msvcrt` and `winreg` do not exist.
    *   Always place imports for OS-specific libraries inside platform-specific branches (`if sys.platform == "win32":`).
2.  **`pathlib.Path` on Unix:**
    *   Python 3.14+ prevents instantiating `WindowsPath` on POSIX systems.
    *   Do NOT instantiate Windows paths or monkeypatch `os.name = "nt"` when running on POSIX systems.
3.  **Cover Both Platform Branches:**
    *   Ensure both Windows (`nt`, `win32`, drive letters) and POSIX (`posix`, `linux`, `darwin`, root slashes) paths and behaviors are properly handled.

---

## 5. Coding Standards & Best Practices

-   **Strict Typing:** All functions, methods, and helpers must be fully and strictly type-hinted.
-   **No Generator Expressions in Iteration Builtins:** Avoid passing generator expressions to `any()`, `all()`, `sum()`, `max()`, `min()`, `join()`, `tuple()`. Use list comprehensions `[…]` or unrolled loops.
-   **Descriptive Variable Names:** No single-letter variable names (except `i`, `j` for loop indices and `n` for counts/math).
-   **Walrus Operator & Single-Use Variables:** Follow the repository guidelines for walrus operators and single-use variable inlining.
