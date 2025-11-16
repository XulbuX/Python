#!/usr/bin/env python3
"""Lists all Python files, executable as commands, in the current directory.
A short description and command arguments are displayed if available."""
from xulbux import FormatCodes, Console, String, Path
from typing import TypedDict, Optional, Any, cast
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
    "check_for_new_cmds": True,
    "check_for_cmd_updates": True,
}

ARGS = Console.get_args(find_args={
    "update_check": ["-u", "--update-check"],
    "download": ["-d", "--download"],
})

ARGS_VAR = re.compile(r"Console\s*.\s*get_args\(\s*(?:find_args\s*=\s*)?(\w+|{.+?})\s*(?:,\s*\w+\s*=\s*.*)*\)", re.DOTALL)
SYS_ARGV = re.compile(r"sys\s*\.\s*argv(?:.*#\s*(\[.+?\])$)?", re.MULTILINE)
DESC = re.compile(r"(?i)^(?:\s*#![\\/\w\s]+)?\s*(\"{3}|'{3})(.+?)\1", re.DOTALL)
PYTHON_SHEBANG = re.compile(r"(?i)^\s*#!.*python")


def is_python_file(filepath: str) -> bool:
    """Check if a file is a Python file by looking for shebang line."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline()
            return bool(PYTHON_SHEBANG.match(first_line))
    except Exception:
        return False


def get_python_files() -> set[str]:
    """Get all Python files in the script directory by checking shebang lines."""
    python_files = set()
    for filename in os.listdir(Path.script_dir):
        file_path = os.path.join(Path.script_dir, filename)
        if os.path.isfile(file_path) and is_python_file(file_path):
            python_files.add(filename)
    return python_files


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
    i, cmds = 0, ""

    for i, f in enumerate(sorted(python_files), 1):
        cmd_title_len = len(str(i)) + len(cmd_name := os.path.splitext(f)[0]) + 4
        cmds += f"\n[b|br:green|bg:br:green]([[black]{i}[br:green]][in|black]( {cmd_name} [bg:black]{'━' * (Console.w - cmd_title_len)}))"
        abs_path = os.path.join(Path.script_dir, f)
        sys_argv = None

        try:
            with open(abs_path, "r", encoding="utf-8") as file:
                content = file.read()
                if desc := DESC.match(content):
                    cmds += f"\n\n[i]{desc.group(2).strip("\n")}[_]"
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
                    cmds += arguments_desc(find_args)
            except Exception:
                pass
        elif sys_argv:
            find_args = {}
            for arg in sys_argv:
                arg = arg.strip()
                if arg.startswith("["):
                    find_args.update(parse_args_comment(arg))
            cmds += arguments_desc(find_args)

        cmds += "\n\n"

    return cmds


class GitHubDiffs(TypedDict):
    new_cmds: list[str]
    cmd_updates: list[str]
    download_urls: dict[str, str]


def get_github_diffs(local_files: set[str]) -> GitHubDiffs:
    """Check for new files and updated files on GitHub compared to local script-directory."""
    result: GitHubDiffs = {"new_cmds": [], "cmd_updates": [], "download_urls": {}}

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
                cmd_name = os.path.splitext(item["name"])[0]
                github_files[cmd_name] = {
                    "filename": item["name"],
                    "download_url": item["download_url"],
                    "sha": item["sha"],
                }

        local_cmd_names = {os.path.splitext(f)[0] for f in local_files}

        # CHECK FOR NEW FILES
        if GITHUB_DIFFS["check_for_new_cmds"]:
            for cmd_name in github_files.keys():
                if cmd_name not in local_cmd_names:
                    result["new_cmds"].append(cmd_name)
                    # STORE WITH FILENAME (INCLUDING EXTENSION) AS KEY
                    result["download_urls"][github_files[cmd_name]["filename"]] = github_files[cmd_name]["download_url"]

        # CHECK FOR UPDATED FILES
        if GITHUB_DIFFS["check_for_cmd_updates"]:
            # CREATE A MAPPING FROM CMD NAME TO ACTUAL FILENAME
            local_file_map = {os.path.splitext(f)[0]: f for f in local_files}

            for cmd_name in local_cmd_names:
                if cmd_name in github_files:
                    try:
                        # READ LOCAL FILE CONTENT AND COMPUTE SHA
                        local_filename = local_file_map[cmd_name]
                        local_path = os.path.join(Path.script_dir, local_filename)

                        # READ AS TEXT AND NORMALIZE TO LF (UNIX) LINE ENDINGS LIKE GITHUB
                        with open(local_path, "r", encoding="utf-8", newline="") as f:
                            local_content = f.read().replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")

                        # GITHUB USES: "blob " + FILESIZE + "\0" + CONTENT
                        # THEN SHA1 HASH OF THAT
                        local_sha = hashlib.sha1(f"blob {len(local_content)}\0".encode() + local_content).hexdigest()

                        # COMPARE WITH GITHUB'S SHA
                        if local_sha != github_files[cmd_name]["sha"]:
                            result["cmd_updates"].append(cmd_name)
                            # STORE WITH FILENAME (INCLUDING EXTENSION) AS KEY
                            result["download_urls"][github_files[cmd_name]["filename"]] = github_files[cmd_name]["download_url"]

                    except Exception:
                        pass  # SKIP FILES THAT CAN'T BE COMPARED

    except Exception as e:
        print(f"DEBUG OUTER ERROR: {e}")
        pass  # RETURN EMPTY LISTS IF GITHUB CHECK FAILS

    # FILTER DOWNLOAD URLS BASED ON SETTINGS
    files_to_download = {}
    for filename, url in result["download_urls"].items():
        cmd_name = os.path.splitext(filename)[0]
        if (GITHUB_DIFFS["check_for_new_cmds"] and cmd_name in result["new_cmds"]) or \
           (GITHUB_DIFFS["check_for_cmd_updates"] and cmd_name in result["cmd_updates"]):
            files_to_download[filename] = url
    result["download_urls"] = files_to_download

    return result


def download_files(github_diffs: GitHubDiffs) -> None:
    """Download new and updated files from GitHub."""
    downloads = github_diffs["download_urls"].items()

    if not len(downloads) > 0:
        return

    if not ARGS.download.exists and not Console.confirm("\n[b](Execute these updates?)", end="\n", default_is_yes=True):
        FormatCodes.print(f"[dim|magenta](⨯ Not updating from [b]({GITHUB_DIFFS['url']}))\n\n")
        return

    # DOWNLOAD FILES
    success_count = 0
    for filename, url in github_diffs["download_urls"].items():
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            cmd_name = os.path.splitext(filename)[0]

            # SAVE WITH OR WITHOUT EXTENSION BASED ON PLATFORM
            if sys.platform == "win32":
                file_path = os.path.join(Path.script_dir, filename)
            else:
                file_path = os.path.join(Path.script_dir, cmd_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            FormatCodes.print(f"[br:green]✓ Downloaded [b]{filename}[_]")

            # MAKE EXECUTABLE ON UNIX-LIKE SYSTEMS
            if sys.platform != "win32":
                os.chmod(file_path, 0o755)

            FormatCodes.print(f"[br:green]✓ Installed [b]({cmd_name})")
            success_count += 1
        except Exception as e:
            FormatCodes.print(f"[br:red]⨯ Failed to download [b]({filename}) [dim]/({e})[_]")

    FormatCodes.print(f"\n[br:green](Successfully downloaded & installed {success_count}/{len(downloads)} command{'s' if len(downloads) > 1 else ''}!)\n\n")


def github_diffs_str(github_diffs: GitHubDiffs) -> str:
    num_new_cmds = len(github_diffs["new_cmds"])
    num_cmd_updates = len(github_diffs["cmd_updates"])

    if not (num_new_cmds > 0 or num_cmd_updates > 0):
        return (
            "[dim|br:blue](ⓘ [i](You have all available command-files"
            f"{' and they\'re all up-to-date' if GITHUB_DIFFS['check_for_cmd_updates'] else ''}.))\n\n"
        ) if GITHUB_DIFFS["check_for_new_cmds"] else "[dim|br:blue](ⓘ [i](All your command-files are up-to-date.))\n\n"

    diffs_title_len = len(title := (
        (f"There {'is' if num_new_cmds == 1 else 'are'} {num_new_cmds} new command{'' if num_new_cmds == 1 else 's'}" if num_new_cmds else "")
        + (" and" if (num_new_cmds and num_cmd_updates) else " available." if num_new_cmds else "You have" if num_cmd_updates else "")
        + (f" {num_cmd_updates} command-update{'' if num_cmd_updates == 1 else 's'} available." if num_cmd_updates else "")
    )) + 5
    diffs = f"[b|br:blue|bg:br:blue]([[black]⇣[br:blue]][in|black]( {title} [bg:black]{'━' * (Console.w - diffs_title_len)}))"

    if num_new_cmds:
        diffs += f"\n\n[b](New Commands:)\n  " + "\n  ".join(f"[br:green]{cmd}[_]" for cmd in github_diffs["new_cmds"])
    if num_cmd_updates:
        diffs += f"\n\n[b](Command Updates:)\n  " + "\n  ".join(f"[br:green]{cmd}[_]" for cmd in github_diffs["cmd_updates"])

    return diffs


def main() -> None:
    global FETCHED_GITHUB

    python_files = get_python_files()

    FormatCodes.print(get_commands_str(python_files))

    if ARGS.update_check.exists or ARGS.download.exists:
        animation_thread = threading.Thread(target=animate)
        animation_thread.start()

        try:
            github_diffs = get_github_diffs(python_files)
        finally:
            FETCHED_GITHUB = True
            animation_thread.join()
            print("\r   \r", end="")

        FormatCodes.print(github_diffs_str(github_diffs))

        download_files(github_diffs)


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
