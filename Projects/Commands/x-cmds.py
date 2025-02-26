"""Lists all Python files, executable as commands, in the current directory.
A short description and command arguments are displayed if available."""
from xulbux import FormatCodes, Console, String, Path
from typing import Optional
import importlib.util
import sys
import os
import re


ARGS_VAR = re.compile(r"Console\s*.\s*get_args\(\s*(?:find_args\s*=\s*)?(\w+|{.+?})\s*\)", re.DOTALL)
SYS_ARGV = re.compile(r"sys\s*\.\s*argv(?:.*#\s*(\[.+?\])$)?", re.MULTILINE)
DESC = re.compile(r"^\s*(\"{3}|'{3})(.+?)\1", re.DOTALL)

TAB_SIZE = 2
TAB3 = " " * (TAB_SIZE * 3 + 1)
TAB4 = " " * (TAB_SIZE * 4 + 1)


def parse_args_comment(s: str) -> dict:
    result, m = {}, re.match(r'\[(.*)\]', s)
    pattern = re.finditer(r'(\w+)(?:\s*:\s*\[([^\]]*)\])?', m[1])
    for match in pattern:
        key, values = match[1], match[2].split(',') if match[2] else []
        result[key] = [v.strip() for v in values]
    return result


def get_var_val(file_path: str, var_name: str) -> str:
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
    spec = importlib.util.spec_from_file_location(os.path.basename(file_path), file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    var_val = getattr(module, var_name, None)
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    return var_val


def arguments_desc(find_args: Optional[dict[str, list[str]]] = None) -> str:
    if not find_args or len(find_args) < 1:
        return f"\n{TAB3}[#78F](TAKES ARGUMENTS [dim]([[i](unknown)]))"
    arg_descs, keys = [], list(find_args.keys())
    for key, val in find_args.items():
        if len(val) < 1:
            arg_descs.append(f"[#56B](arg with no prefix at position {keys.index(key) + 1})")
        else:
            arg_descs.append(val)
    arg_descs = (f"[#99A]({'[dim](,) '.join(arg_desc)})" if isinstance(arg_desc, list) else arg_desc for arg_desc in arg_descs)
    arg_descs = (f"[#9AF]([i]({keys[i]}):) {arg_desc}" for i, arg_desc in enumerate(arg_descs))
    return f"\n{TAB3}[#78F]([u](TAKES ARGUMENTS) [dim]([{len(find_args)}]))\n{TAB4}" + f"\n{TAB4}".join(arg_descs)


def get_commands() -> str:
    commands, files = "", os.listdir(Path.script_dir)
    for i, f in enumerate(sorted(files)):
        filename, file_ext = os.path.splitext(f)
        if file_ext in (".py", ".pyw"):
            abs_path = os.path.join(Path.script_dir, f)
            commands += f"\n [i|dim|#6F9]({i}){' ' * ((TAB_SIZE * 2) - len(str(i)))}[b|#6F9]({filename})"
            try:
                with open(abs_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    if desc := DESC.match(content):
                        desc = desc.group(2).strip("\n")
                        commands += f"[i|#7FD]\n{TAB3}" + f"\n{TAB3}".join(desc.split("\n")) + "[_]"
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
            commands += "\n"
    return commands


if __name__ == "__main__":
    try:
        FormatCodes.print(get_commands())
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
