#!/usr/bin/env python3
"""Lists all Python files, executable as commands, in the current directory.
A short description and command arguments are displayed if available."""
from xulbux import FormatCodes, Console, String, Path
from typing import Optional, Any, cast
import importlib.util
import sys
import os
import re


ARGS_VAR = re.compile(r"Console\s*.\s*get_args\(\s*(?:find_args\s*=\s*)?(\w+|{.+?})\s*(?:,\s*\w+\s*=\s*.*)*\)", re.DOTALL)
SYS_ARGV = re.compile(r"sys\s*\.\s*argv(?:.*#\s*(\[.+?\])$)?", re.MULTILINE)
DESC = re.compile(r"(?i)^(?:\s*#![\\/\w\s]+)?\s*(\"{3}|'{3})(.+?)\1", re.DOTALL)


def parse_args_comment(s: str) -> dict:
    result, m = {}, cast(re.Match[str], re.match(r'\[(.*)\]', s))
    pattern = re.finditer(r'(\w+)(?:\s*:\s*\[([^\]]*)\])?', m[1])
    for match in pattern:
        key, values = match[1], match[2].split(',') if match[2] else []
        result[key] = [v.strip() for v in values]
    return result


def get_var_val(file_path: str, var_name: str) -> Optional[Any]:
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
    spec = importlib.util.spec_from_file_location(os.path.basename(file_path), file_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[call-arg]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    var_val = getattr(module, var_name, None)
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    return var_val


def arguments_desc(find_args: Optional[dict[str, list[str]]]) -> str:
    if not find_args or len(find_args) < 1:
        return f"\n[b](Takes Options/Arguments) [dim]([[i](unknown)])"

    arg_descs, keys = [], list(find_args.keys())

    for key, val in find_args.items():
        if len(val) < 1:
            arg_descs.append(f"non-flagged argument at position {keys.index(key) + 1}")
        elif isinstance(val, str):
            if val.lower() == "before":
                arg_descs.append("all non flagged arguments before first flag")
            elif val.lower() == "after":
                arg_descs.append("all non flagged arguments after last flag's value")
            else:
                arg_descs.append(val)
        elif isinstance(val, dict) and "flags" in val.keys():
            arg_descs.append(cast(dict, val)["flags"])
        else:
            arg_descs.append(val)

    opt_descs = ["[_c], [br:blue]".join(d) for d in arg_descs if isinstance(d, list)]
    opt_keys = [keys.pop(i - j) for j, (i, _) in enumerate((i, d) for i, d in enumerate(arg_descs) if isinstance(d, list))]

    arg_descs = [d for d in arg_descs if isinstance(d, str)]
    arg_keys = [f"<{keys[i]}>" for i, _ in enumerate(arg_descs)]

    left_part_len = max(len(FormatCodes.remove(x)) for x in opt_descs + arg_keys)

    opt_len_diff = [len(d) - len(FormatCodes.remove(d)) for d in opt_descs]
    opt_descs = [
        f"[br:blue]({d:<{left_part_len + opt_len_diff[i]}})"
        f"    [blue]({FormatCodes.escape(f'[{opt_keys[i]}]')})"
        for i, d in enumerate(opt_descs)
    ]

    arg_descs = [
        f"[br:cyan]({arg_keys[i]:<{left_part_len}})"
        f"    [cyan]({d})"
        for i, d in enumerate(arg_descs)
    ]

    return (
        (f"\n\n[b](Takes {len(arg_descs)} Argument{'' if len(arg_descs) == 1 else 's'}:)"
        f"\n  {'\n  '.join(arg_descs)}") if len(arg_descs) > 0 else ""
    ) + (
        (f"\n\n[b](Has {len(opt_descs)} Option{'' if len(opt_descs) == 1 else 's'}:)"
        f"\n  {'\n  '.join(opt_descs)}") if len(opt_descs) > 0 else ""
    )


def get_commands_str() -> str:
    i, commands, all_files = 0, "", os.listdir(Path.script_dir)
    python_files = [f for f in all_files if os.path.splitext(f)[1] in (".py", ".pyw")]

    for i, f in enumerate(sorted(python_files), 1):
        filename, _ = os.path.splitext(f)
        abs_path = os.path.join(Path.script_dir, f)
        cmd_title_len = len(str(i)) + len(filename) + 4
        commands += f"\n[b|br:green|bg:br:green]([[black]{i}[br:green]][in|black]( {filename} [bg:black]{'━' * (Console.w - cmd_title_len)}))"
        sys_argv = None

        try:
            with open(abs_path, "r", encoding="utf-8") as file:
                content = file.read()
                if desc := DESC.match(content):
                    commands += f"\n\n[i]{desc.group(2).strip("\n")}[_]"
                args_var = m.group(1).strip() if (m := ARGS_VAR.search(content)) else None
                sys_argv = SYS_ARGV.findall(content)
        except Exception:
            args_var = None

        if args_var:
            try:
                if args_var.startswith("{"):
                    find_args = String.to_type(args_var)
                else:
                    find_args = get_var_val(abs_path, args_var)
                if find_args and isinstance(find_args, dict):
                    commands += arguments_desc(find_args)
            except Exception:
                pass
        elif sys_argv:
            find_args = {}
            for arg in sys_argv:
                arg = arg.strip()
                if arg.startswith("["):
                    find_args.update(parse_args_comment(arg))
            commands += arguments_desc(find_args)

        commands += "\n\n"

    return commands


if __name__ == "__main__":
    try:
        FormatCodes.print(get_commands_str())
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
