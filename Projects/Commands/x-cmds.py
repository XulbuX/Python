#!/usr/bin/env python3
"""Lists all Python files, executable as commands, in the current directory.
A short description and command arguments are displayed if available."""
from xulbux import FormatCodes, Console, String, Path
from typing import Optional, Any, cast
import importlib.util
import threading
import requests
import hashlib
import time
import sys
import os
import re


GITHUB_DIFFS = {
    "url": "https://github.com/XulbuX/Python/tree/main/Projects/Commands",
    "alert_new_cmds": True,
    "alert_updated_cmds": True,
}

ARGS = Console.get_args(find_args={
    "update_check": ["-u", "--update-check"],
})

ARGS_VAR = re.compile(r"Console\s*.\s*get_args\(\s*(?:find_args\s*=\s*)?(\w+|{.+?})\s*(?:,\s*\w+\s*=\s*.*)*\)", re.DOTALL)
SYS_ARGV = re.compile(r"sys\s*\.\s*argv(?:.*#\s*(\[.+?\])$)?", re.MULTILINE)
DESC = re.compile(r"(?i)^(?:\s*#![\\/\w\s]+)?\s*(\"{3}|'{3})(.+?)\1", re.DOTALL)


def animate() -> None:
    """Display loading animation while scanning for modules."""
    frames, i = [
        "[b]·  [_b]", "[b]·· [_b]", "[b]···[_b]", "[b] ··[_b]", "[b]  ·[_b]",
        "[b]  ·[_b]", "[b] ··[_b]", "[b]···[_b]", "[b]·· [_b]", "[b]·  [_b]"
    ], 0
    max_frame_len = max(len(frame) for frame in frames)
    while not FETCHED_GITHUB:
        frame = frames[i % len(frames)]
        FormatCodes.print(f"\r{frame}{' ' * (max_frame_len - len(frame))} ", end="")
        time.sleep(0.2)
        i += 1


def parse_args_comment(s: str) -> dict:
    result, m = {}, cast(re.Match[str], re.match(r"\[(.*)\]", s))
    pattern = re.finditer(r"(\w+)(?:\s*:\s*\[([^\]]*)\])?", m[1])
    for match in pattern:
        key, values = match[1], match[2].split(",") if match[2] else []
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


def get_commands_str(python_files: set[str]) -> str:
    i, commands = 0, ""

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


def get_github_diffs(local_files: set[str]) -> dict[str, list[str]]:
    """Check for new files and updated files on GitHub compared to local script-directory."""
    result = {"new_cmds": [], "updated_cmds": []}

    try:
        # PARSE THE URL TO EXTRACT REPO INFO
        url = GITHUB_DIFFS["url"]
        url_pattern = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/(?:tree|blob)/([^/]+)(/.*)?)?", url)
        if not url_pattern:
            return result

        user, repo, branch, path = url_pattern.groups()
        branch, path = branch or "main", (path or "").strip("/")

        # USE GITHUB API TO GET DIRECTORY CONTENTS
        api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}"
        if branch: api_url += f"?ref={branch}"

        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        github_files = {}
        for item in response.json():
            if item["type"] == "file" and item["name"].endswith((".py", ".pyw")):
                github_files[item["name"]] = item["download_url"]

        # CHECK FOR NEW FILES
        for github_file in github_files.keys():
            if github_file not in local_files:
                result["new_cmds"].append(os.path.splitext(github_file)[0])

        # CHECK FOR UPDATED FILES
        for local_file in local_files:
            if local_file in github_files:
                try:
                    # DOWNLOAD GITHUB FILE CONTENT
                    gh_response = requests.get(github_files[local_file], timeout=10)
                    gh_response.raise_for_status()
                    github_content = gh_response.text

                    # READ LOCAL FILE CONTENT
                    with open(os.path.join(Path.script_dir, local_file), "r", encoding="utf-8") as f:
                        local_content = f.read()

                    # COMPARE CONTENT HASHES
                    if hashlib.md5(github_content.encode()).hexdigest() != hashlib.md5(local_content.encode()).hexdigest():
                        result["updated_cmds"].append(os.path.splitext(local_file)[0])

                except Exception:
                    pass  # SKIP FILES THAT CAN'T BE COMPARED

    except Exception:
        pass  # RETURN EMPTY LISTS IF GITHUB CHECK FAILS

    return result


def github_diffs_str(github_diffs: dict[str, list[str]]) -> str:
    num_new_cmds = len(github_diffs["new_cmds"]) if GITHUB_DIFFS["alert_new_cmds"] else 0
    num_updated_cmds = len(github_diffs["updated_cmds"]) if GITHUB_DIFFS["alert_updated_cmds"] else 0

    if not (num_new_cmds > 0 or num_updated_cmds > 0):
        return "[dim|br:blue](ⓘ [i](You have all available command-files and they're all up-to-date.))\n\n"

    diffs_title_len = len(title := (
        (f"There {'is' if num_new_cmds == 1 else 'are'} {num_new_cmds} new command{'' if num_new_cmds == 1 else 's'}" if num_new_cmds else "")
        + (" and" if (num_new_cmds and num_updated_cmds) else " available." if num_new_cmds else "You have" if num_updated_cmds else "")
        + (f" {num_updated_cmds} command-update{'' if num_updated_cmds == 1 else 's'} available." if num_updated_cmds else "")
    )) + 5
    diffs = f"[b|br:blue|bg:br:blue]([[black]⇣[br:blue]][in|black]( {title} [bg:black]{'━' * (Console.w - diffs_title_len)}))"

    if num_new_cmds:
        diffs += f"\n\n[b](New Commands:)\n  " + "\n  ".join(f"[br:green]{cmd}[_]" for cmd in github_diffs["new_cmds"])
    if num_updated_cmds:
        diffs += f"\n\n[b](Updated Commands:)\n  " + "\n  ".join(f"[br:green]{cmd}[_]" for cmd in github_diffs["updated_cmds"])

    return f"{diffs}\n\n"


def main() -> None:
    global FETCHED_GITHUB

    python_files = {f for f in os.listdir(Path.script_dir) if f.endswith((".py", ".pyw"))}

    FormatCodes.print(get_commands_str(python_files))

    if ARGS.update_check.exists:
        animation_thread = threading.Thread(target=animate)
        animation_thread.start()

        try:
            github_diffs = get_github_diffs(python_files)
        finally:
            FETCHED_GITHUB = True
            animation_thread.join()
            print("\r   \r", end="")

        FormatCodes.print(github_diffs_str(github_diffs))


if __name__ == "__main__":
    FETCHED_GITHUB = False
    try:
        main()
    except KeyboardInterrupt:
        FETCHED_GITHUB = True
        print()
    except Exception as e:
        FETCHED_GITHUB = True
        Console.fail(e, start="\n", end="\n\n")
