#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Lists all Python files, executable as commands, in the current directory.
A short description and command arguments are displayed if available."""
from pathlib import Path
from typing import TypeAlias, TypedDict, Optional, Literal, cast
from xulbux.base.types import ArgConfigWithDefault
from xulbux.console import Spinner
from xulbux.regex import LazyRegex
from xulbux import FormatCodes, Console, FileSys, String, Regex
import requests
import hashlib
import sys
import os
import re

"""
[1] WHICH FILES ARE CONSIDERED COMMANDS?
Only files, starting with a python shebang line (e.g. `#!/usr/bin/env python3`), are considered commands.

[2] WHICH FILES WILL BE CHECKED FOR UPDATES?
Only files that include the comment `#[x-cmds]: UPDATE` at the top of the file will be checked for updates from GitHub.

[3] COMMAND DESCRIPTION
The first multi-line comment (triple quotes) at the start of the file is used as a short description.

[4] COMMAND ARGUMENTS & OPTIONS
The use of `Console.get_args()` will automatically be parsed and displayed correctly.
When getting args using `sys.argv`, add a comment to describe the arguments on the line `sys.argv` is used.
The structure of the comment is similar to how the `**find_args` kwargs are defined for `Console.get_args()`:
# [pos_arg1: before, arg2: {-a2, --arg2}, arg3: {-a3, --arg3}, pos_arg4: after]
"""


CONFIG = {
    "command_dir": FileSys.script_dir,  # MUST BE A `pathlib.Path` OBJECT
    "github_updates" : {
        "github_repo_urls": ["https://github.com/XulbuX/Python/tree/main/Projects/Commands"],
        "check_for_new_commands": True,
        "check_for_command_updates": True,
    },
}

ARGS = Console.get_args(update_check={"-u", "--update"})

PATTERNS = LazyRegex(
    python_shebang=r"(?i)^\s*#!.*python",
    update_marker=r"(?i)^\s*#\s*\[x-cmds\]\s*:\s*UPDATE\s*$",
    desc=r"(?is)^(?:\s*#!?[^\n]+)*\s*(\"{3}(?:(?!\"\"\").)+\"{3}|'{3}(?:(?!''').)+'{3})",
    sys_argv=r"(?m)sys\s*\.\s*argv(?:\[[-:0-9]+\])?(?:\s*#\s*(\[.+?\]))?",
    args_comment=r"(\w+)(?:\s*:\s*(?:\{([^\}]*)\}|(before|after)))?",
    get_args=r"(?m)Console\s*\.\s*get_args\s*" + Regex.brackets(is_group=True),
    arg=r"\s*(\w+)\s*=\s*(.*)\s*,?",
)

IS_WIN = sys.platform == "win32"

FindArgs: TypeAlias = dict[str, set[str] | ArgConfigWithDefault | Literal["before", "after"]]


def is_python_file(filepath: str) -> bool:
    """Check if a file is a Python file by looking for shebang line."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return bool(PATTERNS.python_shebang.match(file.readline()))
    except Exception:
        return False


def get_python_files() -> set[str]:
    """Get all Python files in the command directory by checking shebang lines."""
    python_files = set()
    for file_path in CONFIG["command_dir"].iterdir():
        if file_path.is_file() and is_python_file(str(file_path)):
            python_files.add(file_path.name)
    return python_files


def get_xcmds_options(filepath: str) -> dict[str, bool]:
    """Get options for `x-cmds` set using special `#[x-cmds]: …` comments."""
    options: dict[str, bool] = {}
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                if PATTERNS.python_shebang.match(line):
                    continue  # SKIP SHEBANG LINE
                elif PATTERNS.update_marker.match(line):
                    options["update_check"] = True
                else:
                    break  # STOP AT FIRST NON-MATCHING LINE
    except Exception:
        pass
    return options


def sort_flags(flags: list[str]) -> list[str]:
    return sorted(flags, key=lambda x: (len(x) - len(x.lstrip("-")), x))


def arguments_desc(find_args: Optional[FindArgs]) -> str:
    if not find_args or len(find_args) < 1:
        return f"\n\n[b](Takes Options/Arguments) [dim]([[i](unknown)])"

    arg_descs: list[str | list[str]] = []
    keys = list(find_args.keys())

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
            arg_descs.append(sort_flags(list(val["flags"])))
        elif isinstance(val, (list, tuple, set, frozenset)):
            arg_descs.append(sort_flags(list(val)))
        else:
            arg_descs.append(repr(val))

    opt_descs = ["[_c], [br:blue]".join(d) for d in arg_descs if isinstance(d, (list, tuple, set, frozenset))]
    opt_keys = [keys.pop(i - j) for j, (i, _) in enumerate((i, d) for i, d in enumerate(arg_descs) if isinstance(d, (list, tuple, set, frozenset)))]

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
        f"\n  {'\n  '.join(cast(list[str], arg_descs))}") if len(arg_descs) > 0 else ""
    ) + (
        (f"\n\n[b](Has {len(opt_descs)} Option{'' if len(opt_descs) == 1 else 's'}:)"
        f"\n  {'\n  '.join(opt_descs)}") if len(opt_descs) > 0 else ""
    )


def parse_args_comment(comment_str: str) -> FindArgs:
    result: FindArgs = {}

    for match in PATTERNS.args_comment.finditer(cast(re.Match[str], re.match(r"\[(.*)\]", comment_str)).group(1)):
        key = str(match.group(1))
        if (val := match.group(3)) in {"before", "after"}:
            result[key] = cast(Literal["before", "after"], val)
        else:
            flags = {flag.strip() for flag in match.group(2).split(",")} if match.group(2) else set()
            result[key] = flags

    return result


def get_commands_str(python_files: set[str]) -> str:
    i, cmds = 0, ""

    for i, f in enumerate(sorted(python_files), 1):
        cmd_name = Path(f).stem
        cmd_title_len = len(str(i)) + len(cmd_name) + 4
        cmds += f"\n[b|br:white|bg:br:white]([[black]{i}[br:white]][in|black]( {cmd_name} [bg:black]{'━' * (Console.w - cmd_title_len)}))"

        sys_argv_comments, get_args_funcs = [], []

        with open(CONFIG["command_dir"] / f, "r", encoding="utf-8") as file:
            if desc := PATTERNS.desc.match(content := file.read()):
                cmds += f"\n\n[i]{desc.group(1).strip("\n\"'")}[_]"

            sys_argv_comments = PATTERNS.sys_argv.findall(content)
            get_args_funcs = PATTERNS.get_args.findall(content)

        find_args: FindArgs = {}

        if len(get_args_funcs) > 0:
            try:
                # GET ARGUMENTS OF FIRST NON-EMPTY Console.get_args() CALL
                func_args = ""
                if len(get_args_funcs) > 1:
                    for func_args in get_args_funcs:
                        if (func_args := func_args.strip()):
                            break
                elif len(get_args_funcs) == 1:
                    func_args = get_args_funcs[0]

                # PARSE THE FUNCTION ARGUMENTS
                for arg in PATTERNS.arg.finditer(func_args):
                    if (key := arg.group(1)) and (val := arg.group(2)) and not key.strip() == "allow_spaces":
                        find_args[key.strip()] = String.to_type(val.strip().rstrip(","))
                cmds += arguments_desc(find_args)

            except Exception:
                pass

        elif len(sys_argv_comments) > 0:
            # PARSE FIRST NON-EMPTY ARGS-DESCRIBING COMMENT
            for comment in sys_argv_comments:
                if (comment := comment.strip()).startswith("["):
                    find_args.update(parse_args_comment(comment))
            cmds += arguments_desc(find_args)

        cmds += "\n\n"

    return cmds


class GitHubDiffs(TypedDict):
    new_commands: list[str]
    updated_commands: list[str]
    deleted_commands: list[str]
    download_urls: dict[str, str]


def get_github_diffs(local_files: set[str]) -> GitHubDiffs:
    """Check for new files, updated files, and deleted files on GitHub compared to local command-directory."""
    result: GitHubDiffs = {"new_commands": [], "updated_commands": [], "deleted_commands": [], "download_urls": {}}

    try:
        # MERGE FILES FROM ALL GITHUB REPO URLS
        github_files: dict[str, dict[str, str]] = {}

        for repo_url in CONFIG["github_updates"]["github_repo_urls"]:
            try:
                # PARSE THE URL TO EXTRACT REPO INFO
                url_pattern = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/(?:tree|blob)/([^/]+)(/.*)?)?", repo_url)
                if not url_pattern:
                    continue

                user, repo, branch, path = url_pattern.groups()
                branch, path = branch or "main", (path or "").strip("/")

                # USE GITHUB API TO GET DIRECTORY CONTENTS
                api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}"
                if branch: api_url += f"?ref={branch}"

                response = requests.get(api_url, timeout=10)
                response.raise_for_status()

                # MERGE FILES FROM THIS REPO (LATER URLS OVERRIDE EARLIER ONES IF SAME NAME)
                for item in response.json():
                    if item["type"] == "file" and item["name"].endswith((".py", ".pyw")):
                        cmd_name = Path(item["name"]).stem
                        github_files[cmd_name] = {
                            "filename": item["name"],
                            "download_url": item["download_url"],
                            "sha": item["sha"],
                        }
            except Exception:
                pass  # SKIP REPOS THAT CAN'T BE ACCESSED

        # CREATE MAPPING FROM CMD NAME TO ACTUAL FILENAME FOR LOCAL FILES
        local_file_map = {Path(f).stem: f for f in local_files}
        local_cmd_names = set(local_file_map.keys())

        # GET LOCAL FILES THAT HAVE UPDATE MARKER
        local_updateable_files = set()
        for filename in local_files:
            filepath = CONFIG["command_dir"] / filename
            options = get_xcmds_options(str(filepath))
            if options.get("update_check"):
                local_updateable_files.add(Path(filename).stem)

        # CHECK FOR NEW FILES
        if CONFIG["github_updates"]["check_for_new_commands"]:
            for cmd_name in github_files.keys():
                if cmd_name not in local_cmd_names:
                    result["new_commands"].append(cmd_name)
                    result["download_urls"][github_files[cmd_name]["filename"]] = github_files[cmd_name]["download_url"]

        # CHECK FOR UPDATED FILES (ONLY THOSE WITH UPDATE MARKER)
        if CONFIG["github_updates"]["check_for_command_updates"]:
            for cmd_name in local_updateable_files:
                if cmd_name in github_files:
                    try:
                        local_filename = local_file_map[cmd_name]
                        local_path = CONFIG["command_dir"] / local_filename

                        # READ AS TEXT AND NORMALIZE TO LF (UNIX) LINE ENDINGS LIKE GITHUB
                        with open(local_path, "r", encoding="utf-8", newline="") as f:
                            local_content = f.read().replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")

                        # GITHUB USES: "blob " + FILESIZE + "\0" + CONTENT THEN SHA1 HASH
                        local_sha = hashlib.sha1(f"blob {len(local_content)}\0".encode() + local_content).hexdigest()

                        # COMPARE WITH GITHUB'S SHA
                        if local_sha != github_files[cmd_name]["sha"]:
                            result["updated_commands"].append(cmd_name)
                            result["download_urls"][github_files[cmd_name]["filename"]] = github_files[cmd_name]["download_url"]
                    except Exception:
                        pass  # SKIP FILES THAT CAN'T BE COMPARED

        # CHECK FOR DELETED FILES (LOCAL FILES WITH UPDATE MARKER NOT IN GITHUB)
        if CONFIG["github_updates"]["check_for_new_commands"]:
            for cmd_name in local_updateable_files:
                if cmd_name not in github_files and cmd_name not in result["updated_commands"]:
                    result["deleted_commands"].append(cmd_name)

    except Exception:
        pass  # RETURN EMPTY LISTS IF GITHUB CHECK FAILS

    return result


def github_diffs_str(github_diffs: GitHubDiffs) -> str:
    num_new_cmds = len(github_diffs["new_commands"])
    num_cmd_updates = len(github_diffs["updated_commands"])
    num_deleted_cmds = len(github_diffs["deleted_commands"])
    total_changes = num_new_cmds + num_cmd_updates + num_deleted_cmds

    if total_changes == 0:
        return (
            "[magenta](ⓘ [i](You have all available command-files"
            f"{' and they\'re all up-to-date' if CONFIG['github_updates']['check_for_command_updates'] else ''}.))\n\n"
        ) if CONFIG["github_updates"]["check_for_new_commands"] else "[magenta](ⓘ [i](All your command-files are up-to-date.))\n\n"

    # BUILD TITLE
    title_parts = []
    if num_new_cmds:
        title_parts.append(f"{num_new_cmds} new command{'' if num_new_cmds == 1 else 's'}")
    if num_cmd_updates:
        title_parts.append(f"{num_cmd_updates} command update{'' if num_cmd_updates == 1 else 's'}")

    if len(title_parts) == 1:
        title = f"There {'is' if total_changes == 1 else 'are'} {title_parts[0]} available."
    elif len(title_parts) == 2:
        title = f"There are {title_parts[0]} and {title_parts[1]} available."
    else:
        title = f"There are {title_parts[0]}, {title_parts[1]}, and {title_parts[2]} available."

    diffs_title_len = len(title) + 5
    diffs = f"[b|magenta|bg:magenta]([[black]⇣[magenta]][in|black]( {title} [bg:black]{'━' * (Console.w - diffs_title_len)}))"

    if num_new_cmds:
        diffs += f"\n\n[b](New Commands:)\n  " + "\n  ".join(f"[br:green]{cmd}[_]" for cmd in sorted(github_diffs["new_commands"]))
    if num_cmd_updates:
        diffs += f"\n\n[b](Updated Commands:)\n  " + "\n  ".join(f"[br:blue]{cmd}[_]" for cmd in sorted(github_diffs["updated_commands"]))
    if num_deleted_cmds:
        diffs += f"\n\n[b](Deleted Commands:)\n  " + "\n  ".join(f"[br:red]{cmd}[_]" for cmd in sorted(github_diffs["deleted_commands"]))

    return diffs


def download_files(github_diffs: GitHubDiffs) -> None:
    """Download new and updated files from GitHub, and delete removed files."""
    downloads = github_diffs["download_urls"].items()
    deletions = github_diffs["deleted_commands"]
    total_operations = len(downloads) + len(deletions)

    if total_operations == 0:
        return

    if not Console.confirm("\n[b](Execute these updates?)", end="\n", default_is_yes=True):
        FormatCodes.print(f"[dim|magenta](⨯ Not updating commands from GitHub)\n\n")
        return

    success_count = 0

    # DOWNLOAD NEW AND UPDATED FILES
    for filename, url in downloads:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # SAVE WITH OR WITHOUT EXTENSION BASED ON PLATFORM
            cmd_name = Path(filename).stem
            file_path = CONFIG["command_dir"] / (filename if IS_WIN else cmd_name)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            # MAKE EXECUTABLE ON UNIX-LIKE SYSTEMS
            if not IS_WIN:
                os.chmod(file_path, 0o755)

            action = "Added" if cmd_name in github_diffs["new_commands"] else "Updated"
            FormatCodes.print(f"[br:green](✓ {action} [b]({cmd_name}))")
            success_count += 1
        except Exception as e:
            FormatCodes.print(f"[br:red](⨯ Failed to download [b]({filename}) [dim]/({e})[_])")

    # DELETE REMOVED FILES
    for cmd_name in deletions:
        try:
            # TRY BOTH WITH AND WITHOUT EXTENSION
            deleted = False
            for ext in [".py", ".pyw", ""]:
                file_path = CONFIG["command_dir"] / f"{cmd_name}{ext}"
                if file_path.exists():
                    file_path.unlink()
                    deleted = True
                    break

            if deleted:
                FormatCodes.print(f"[br:green](✓ Deleted [b]({cmd_name}))")
                success_count += 1
            else:
                FormatCodes.print(f"[dim|br:yellow](⚠ Could not find [b]({cmd_name}) to delete)")
        except Exception as e:
            FormatCodes.print(f"[br:red](⨯ Failed to delete [b]({cmd_name}) [dim]/({e})[_])")

    color = 'br:green' if success_count == total_operations else 'br:red' if success_count == 0 else 'br:yellow'
    FormatCodes.print(f"\nSuccessfully completed [{color}]([b]({success_count})/{total_operations}) operation{'s' if total_operations > 1 else ''}!\n\n")


def main() -> None:
    python_files = get_python_files()

    FormatCodes.print(get_commands_str(python_files))

    if ARGS.update_check.exists:
        spinner = Spinner("⟳ Checking for updates")
        spinner.set_format(["[magenta]({l})", "[b|magenta]({a})"])

        with spinner.context():
            github_diffs = get_github_diffs(python_files)

        FormatCodes.print(github_diffs_str(github_diffs))

        download_files(github_diffs)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
