from pathlib import Path
from typing import Optional, cast
from xulbux import FormatCodes, EnvPath, FileSys, String, Regex, Code, Data, File, Json
from xulbux.console import Console, Args
import regex as rx
import os
import re


VERSION = "1.4.26"
COMMAND = "x-convert"
JSON_FILE = "config.json"
FIND_ARGS = {
    "filepath": {"-f", "--file", "-p", "--path", "-fp", "--filepath", "--file-path"},
    "indent": {"-i", "--indent", "-is", "--indent-spaces"},
    "blade_vue": {"-bv", "--blade-vue", "--blade-to-vue"},
    "help": {"-h", "--help"},
    "debug": {"-d", "--debug"},
}
DEFAULT_JSON = {
    "component_replacements": {
        ">> OLD COMPONENT-NAME": [
            ">> NEW COMPONENT-NAME (`:filename` WILL BE REPLACED WITH THE FILENAME FROM THE IMPORT-PATH)",
            ">> COMPONENTS IMPORT-PATH",
        ],
        "iconify-icon": "i",
        "information-button": [":filename", "@@/Components/InformationButton.vue"],
        "race-locations-map": ["RaceLocationsMap", "@@/Components/Race/LocationsMap.vue"],
        "vue-back-button": [":filename", "@@/Components/SupButton.vue"],
        "vue-checkbox": [":filename", "@@/Components/SupCheckbox.vue"],
        "vue-form": "form",
        "x-app.card": [":filename", "@@/Components/Card.vue"],
        "x-base.back": [":filename", "@@/Components/Base/SupBack.vue"],
        "x-base.button": [":filename", "@@/Components/SupButton.vue"],
        "x-base.checkbox": [":filename", "@@/Components/SupCheckbox.vue"],
        "x-base.input": [":filename", "@@/Components/SupInput.vue"],
        "x-base.link": [":filename", "@@/Components/SupLink.vue"],
        "x-base.select": [":filename", "@@/Components/SupSelect.vue"],
        "x-download.app": ["RaceDownload", "@@/Components/Race/Download.vue"],
        "x-downloads": [":filename", "@@/Components/SupDownloads.vue"],
        "x-guest.app": [":filename", "@@/Layouts/GuestLayout.vue"],
        "x-guest.footer": [":filename", "@@/Layouts/Partials/Footer.vue"],
        "x-guest.submenu": [":filename", "@@/Layouts/Partials/GuestSubmenu.vue"],
        "x-guest.tab": [":filename", "@@/Layouts/Partials/Tab.vue"],
        "x-public-app.signup-card": [":filename", "@@/Components/SignupCard.vue"],
        "x-race.current-attendees": ["RaceCurrentAttendees", "@@/Components/Race/CurrentAttendees.vue"],
        "x-race.sidebar-information": ["RaceSidebarInformation", "@@/Components/Race/SidebarInformation.vue"],
        "x-race.responsible-person": ["RaceResponsiblePerson", "@@/Components/Race/ResponsiblePerson.vue"],
    },
    "php_as_js_functions": {
        ">> PHP-FUNCTION NAME": [
            ">> JS-FUNCTION",
            [
                ">> IMPORT UNDER NAME (OPTIONAL IF LIBRARY IS NEEDED IN JS-FUNCTION)",
                ">> LIBRARY IMPORT-PATH (SEPARATE WITH `\n` IF MULTIPLE NEEDED LIBRARIES - OPTIONAL IF LIBRARY IS NEEDED IN JS-FUNCTION)",
            ],
        ],
        "date": [
            "const date = (str:string) => dayjs(str, 'DD.MM.YYYY').format('DD.MM.YYYY')",
            ["dayjs", "dayjs"],
        ],
        "dateFormat": [
            "const dateFormat = (date:string, format:string = 'dd. DD.MM.YYYY') => dayjs(date).format(format);",
            ["dayjs", "dayjs"],
        ],
        "strtotime": [
            "const strtotime = (str: string) => dayjs(str).unix()",
            ["dayjs", "dayjs"],
        ],
        "ucfirst": "const ucfirst = (str:string) => str.charAt(0).toUpperCase() + str.slice(1)",
        "lcfirst": "const lcfirst = (str:string) => str.charAt(0).toLowerCase() + str.slice(1)",
        "strtoupper": "const strtoupper = (str:string) => str.toUpperCase()",
        "strtolower": "const strtolower = (str:string) => str.toLowerCase()",
        "trim": "const trim = (str:string) => str.trim()",
        "ltrim": "const ltrim = (str:string) => str.trimStart()",
        "rtrim": "const rtrim = (str:string) => str.trimEnd()",
        "str_replace": "const str_replace = (str:string, search: string, replace: string) => str.replace(search, replace)",
        "nl2br": "const nl2br = (str:string) => str.replace(/\n/g, '<br>')",
        "strip_tags": "const strip_tags = (str:string) => str.replace(/<[^>]*>/g, '')",
        "addslashes": "const addslashes = (str:string) => str.replace(/[\\\"']/g, '\\$&')",
    },
    "function_replacements": {
        ">> PHP-FUNCTION NAME": ">> JS-FUNCTION NAME",
        "rawurlencode": "encodeURIComponent",
        "urlencode": "encodeURIComponent",
        "e": "encodeURIComponent",
        "json_encode": "JSON.stringify",
        "strtolower": "toLowerCase",
        "strtoupper": "toUpperCase",
        "str_replace": "replace",
        "preg_replace": "replace",  # WITH A REGULAR EXPRESSION IN JAVASCRIPT
        "explode": "split",
        "implode": "join",
        "number_format": "toLocaleString",  # APPROXIMATION, MIGHT NEED ADDITIONAL OPTIONS
        "str_pad": "padStart",  # ... OR `padEnd` -> DEPENDS ON THE PADDING DIRECTION
        "strpos": "indexOf",
        "str_contains": "includes",
        "substr": "substring",
        "mb_substr": "substring",  # JS STRINGS ARE UNICODE BY DEFAULT
        "round": "Math.round",
        "ceil": "Math.ceil",
        "floor": "Math.floor",
        "max": "Math.max",
        "min": "Math.min",
        "abs": "Math.abs",
        "rand": "Math.random",  # BEHAVIOR IS DIFFERENT, `Math.random()` RETURNS 0-1
        "intval": "parseInt",
        "floatval": "parseFloat",
        "strtotime": "Date.parse",
        "in_array": "includes",  # FOR ARRAYS IN JAVASCRIPT
        "array_push": "push",
        "array_pop": "pop",
        "array_shift": "shift",
        "array_unshift": "unshift",
        "array_slice": "slice",
        "array_splice": "splice",
        "array_filter": "filter",
        "array_map": "map",
        "array_reduce": "reduce",
        "array_key_exists": "hasOwnProperty",
        "array_keys": "Object.keys",
        "array_values": "Object.values",
    },
    ">> IGNORE <<  is_in_env_vars": "",
}
L_FN = r"\$lang|__"
TAB = " " * 17
ADD_JS = []
JS_IMPORTS = {}
QUOTES = Regex.quotes()
R_BR = Regex.brackets("(", ")", is_group=True)
S_BR = Regex.brackets("[", "]", is_group=True)
C_BR = Regex.brackets("{", "}", is_group=True)
A_BR = Regex.brackets("<", ">", is_group=True)


def show_help():
    FormatCodes.print(
        rf"""  [_|b|#7075FF]        [#FF9E6A]                                      __
  [b|#7075FF]  _  __ [#FF9E6A]  _________  ____  _   _____  _______/ /_
  [b|#7075FF] | |/ / [#FF9E6A] / ___/ __ \/ __ \| | / / _ \/ ___/_  __/
  [b|#7075FF] > , <  [#FF9E6A]/ /__/ /_/ / / / /| |/ / ___/ /    / /_
  [b|#7075FF]/_/|_|  [#FF9E6A]\___/\____/_/ /_/ |___/\___/_/     \__/  [*|BG:#7B7C8F|#000] v[b]{VERSION} [*]

  [i|#FF806A]         CONVERT ONE TYPE OF CODE INTO ANOTHER[*]

  [b|#7090FF]Usage:[*]
    [#FF9E6A]x-convert [#77EFEF]<options>[*]

  [b|#7090FF]Arguments:[*]
    (Command executable without arguments ➜ will ask for them if not given)
    [#77EFEF]-f[dim](,) --file[dim](,) -p[dim](,) --path[dim](,) -fp[dim](,) --filepath[dim](,) --file-path    [#AA90FF]Path to the file containing the code to be formatted[*]
    [#77EFEF]-i[dim](,) --indent[dim](,) -is[dim](,) --indent-spaces                      [#AA90FF]Number of spaces to use for indentation in the formatted file[*]
    [#77EFEF][dim](<)conversion type: args under supported conversions ↓ [dim](>)  [#AA90FF]What type of code to convert into another type of code[*]

  [b|#7090FF]Examples [_b]((Blade ➜ Vue)):[*]
    Full path with 2 spaces indentation:
      [_]C:\Users\{Console.user}> [#FF9E6A]x-convert [#7B7C8F]-f [#4DF1C2]D:\full\path\to\file.blade.php [#7B7C8F]-i [#77EFEF]2 [#7B7C8F]-bv[*]

    Relative path with 4 spaces indentation:
      [_]C:\Users\{Console.user}> [#FF9E6A]cd [#4DF1C2]D:\full\path[*]
      [_]D:\full\path> [#FF9E6A]x-convert [#7B7C8F]--file-path [#4DF1C2].\to\file.blade.php [#7B7C8F]--indent-spaces [#77EFEF]4 [#7B7C8F]--blade-to-vue[*]

  [b|#7090FF]Supported conversion:[*]
    [b|#FF5252]Laravel Blade [dim]((.blade.php))[*] to [b|#41B883]Vue.js [dim]((.vue))[*]             [*|#AA90FF]-bv[dim](,) --blade-vue[dim](,) --blade-to-vue[*]
  [_]"""
    )


def get_json(args: Args) -> None:
    try:
        global JSON, _JSON
        JSON, _JSON = Json.read(
            JSON_FILE, comment_start=">>", comment_end="<<", return_original=True
        )
    except FileNotFoundError:
        Console.fail(f"File not found: [white]{JSON_FILE}", exit=False, start="\n")
        if Console.confirm(f"{TAB}Create [+|b]{JSON_FILE}[*] with default values in program directory?", default_color="#3EE6DE", end=""):
            Json.create(JSON_FILE, DEFAULT_JSON, indent=4, force=True)
            Console.info(f"[white]{JSON_FILE}[*] created successfully.", start="\n", end="\n\n")
            FormatCodes.print(f"{TAB}[dim]Restarting program...[_]")
            main(args)
            Console.pause_exit(exit=True)
        else:
            Console.exit(start="\n", end="\n\n")


def get_missing_args(args: Args) -> Args:
    if not args.filepath.value or not args.blade_vue.exists:
        print()
    if not args.filepath.value:
        args.filepath.value = FormatCodes.input("Path to your file[_|dim] >  [_]", default_color="#3EE6DE").strip()
    if not args.blade_vue.exists:
        FormatCodes.print("What conversion to do?[_]", default_color="#3EE6DE")
        FormatCodes.print("[+|b]  1  [*]Blade to Vue[_]", default_color="#3EE6DE")
        result = Console.input(
            "             [_] ([i](1)) >  ",
            default_color="#3EE6DE",
            max_len=1,
            allowed_chars="1",
            default_val=1,
            output_type=int,
        )
        args.blade_vue.exists = result == 1
    return args


def add_to_env_vars() -> None:
    base_dir = FileSys.script_dir
    try:
        if JSON["is_in_env_vars"] != base_dir:
            if not EnvPath.has_path(base_dir=True):
                Console.warn(
                    "Path to program-directory doesn't exist in your environment variables.\n"
                    f"[#7090FF]If existent, you can execute the program with the command [#FF9E6A]{COMMAND}[#7090FF].[_]",
                    exit=False,
                    start="\n"
                )
                if Console.confirm(
                    f"{TAB}Add the [+|b]program directory[*] to your environment variables?",
                    default_color="#3EE6DE",
                ):
                    EnvPath.add_path(base_dir=True)
                    Console.info(
                        f"Successfully added [white]{base_dir}[_] to your environment variables.\n"
                        f"[#7090FF]If the command [#FF9E6A]{COMMAND}[#7090FF] doesn't work, you might need to restart the console.[_]",
                        start="\n", end="\n\n"
                    )
                    FormatCodes.print("        \t[dim]Continuing program...[_]")
            Json.update(JSON_FILE, { "is_in_env_vars": base_dir })
    except KeyError:
        Console.fail(
            f"Not all required keys were found in JSON file:  [white]{JSON_FILE}",
            pause=DEBUG,
            start="\n",
            end="\n\n",
        )


class blade_to_vue:
    @staticmethod
    def transform_slots(code: str) -> Optional[str]:
        pattern_one_line = (
            r"<x-slot\s*name\s*=\s*"
            + QUOTES
            + r"\s*>\s*\n?\s*([^\n>]+)?\s*\n?\s*</x-slot>"
        )
        pattern_multiline = r"<x-slot\s*name\s*=\s*" + QUOTES + r"\s*>(.*?)</x-slot>"

        def replace_slot(match: re.Match) -> Optional[str]:
            name = match.group(2)
            content = match.group(3).strip()
            if not content:
                return None
            content = rx.sub(
                r"\{\{\s*(" + L_FN + r"\(\s*" + QUOTES + r"\s*\))\s*\}\}",
                r"\1",
                content,
            )
            slots[name] = content

        slots = {}
        code = rx.sub(pattern_one_line, replace_slot, code, flags=re.DOTALL)  # type: ignore[overloads]

        def add_slot_attributes(match: re.Match) -> str:
            tag = match.group(1)
            attributes = match.group(2).strip()
            for name, value in slots.items():
                val = value.strip()
                attributes += f'{f' {':' if Code.is_js(val) else ''}{name}="{val}"' if val and not('\n' in val or '>' in val) else ''}'
            return f"<{tag} {attributes.strip()}>{match.group(3)}"

        code = rx.sub(
            pattern_multiline, r"<template #\2>\3</template>", code, flags=re.DOTALL
        )
        code = re.sub(r"<(/)?x-slot(.*?)>", r"<\1slot\2>", code)
        return re.sub(
            r"<([\w.-]+)(.*?)>(\s*(?:\n|<[\w.-]+\s+|$))",
            add_slot_attributes,
            code,
            count=1,
        )

    @staticmethod
    def add_php_funcs(code: str, php_as_js_functions: dict) -> None:
        for php_func in Data.remove_duplicates(
            [func[0] for func in Code.get_func_calls(code)]
        ):
            if php_func in php_as_js_functions.keys():
                js_func = php_as_js_functions[php_func]
                if (
                    isinstance(js_func, list)
                    and js_func[1]
                    and js_func[1] not in ("", [], None)
                    and len(js_func[1]) == 2
                    and js_func[1][0] not in JS_IMPORTS
                ):
                    JS_IMPORTS[js_func[1][0]] = js_func[1][1]
                js_func = js_func if not isinstance(js_func, list) else js_func[0]
                if js_func and js_func not in (None, "") and js_func not in ADD_JS:
                    ADD_JS.append(js_func)

    @staticmethod
    def transform_script_lang_funcs(code: str) -> str:
        pattern = (
            r"(<script(?:\s+[\s\S]*)?>)"
            + Regex.all_except(r"<|>", is_group=True)
            + r"(<\/script\s*>)"
        )

        def replace_script_lang_func(match: re.Match) -> str:
            script = match.group(2)
            funcs = re.findall(r"lang\s*\(", script)
            if funcs:
                script = re.sub(r"lang\s*\(", "trans(", script)
                script = rx.sub(
                    r"import\s*{\s*lang\s*}\s*from\s*" + QUOTES + r";\s*",
                    "",
                    script,
                    flags=re.DOTALL,
                )
                JS_IMPORTS["{ trans }"] = "laravel-vue-i18n"
            return f"{match.group(1)}{script}{match.group(3)}"

        return re.sub(pattern, replace_script_lang_func, code, flags=re.DOTALL)

    @staticmethod
    def transform_tag_names(code: str, component_replacements: dict) -> str:
        pattern = r"<(/?)([\w.-]+)\s*([^>]*?)(\s*/?)>"

        def replace_tag_name(match: re.Match) -> str:
            tag_parts = [match.group(1), match.group(2), match.group(3)]
            if tag_parts[1] in component_replacements.keys():
                value = component_replacements[tag_parts[1]]
                replacement_name, import_path = (
                    value if isinstance(value, list) else [value, None]
                )[:2]
                if import_path:
                    replacement_name = replacement_name.replace(
                        ":filename", Path(import_path).stem
                    )
                    if import_path not in JS_IMPORTS:
                        JS_IMPORTS[replacement_name] = import_path
                if tag_parts[2]:
                    tag_parts[2] = rx.sub(
                        r':?([\w-]+)\s*=\s*([\'"])(?:\s*\{\{)?\s*'
                        + L_FN
                        + r"\s*"
                        + R_BR
                        + r"\s*(?:\}\}\s*)?\2",
                        r'\1="\3"',
                        tag_parts[2],
                    )
                return f"<{tag_parts[0]}{replacement_name}{' ' if tag_parts[2] else ''}{tag_parts[2]}{match.group(4)}>"
            return match.group(0)

        code = re.sub(pattern, replace_tag_name, code)
        return code

    @staticmethod
    def transform_func_names(code: str, function_replacements: dict) -> str:
        def replace_func_name(match: re.Match) -> str:
            func_parts = [match.group(1), match.group(2)]
            if func_parts[0] in function_replacements.keys():
                return f"{function_replacements[func_parts[0]]}({func_parts[1]})"
            return match.group(0)

        code = rx.sub(r"(?i)" + Regex.func_call(), replace_func_name, code)  # type: ignore[overloads]
        return code

    @staticmethod
    def transform_headings(code: str) -> str:
        pattern_one = r'<x-typography\.heading\s+(.*?):?type="\'?(.*?)\'?"(.*?)>(.*?)</x-typography\.heading\s*>'
        pattern_two = r'<x-typography\.heading\s+(.*?):?type=\'"?(.*?)"?\'(.*?)>(.*?)</x-typography\.heading\s*>'

        def replace_heading(match: re.Match) -> str:
            heading = match.group(2)
            attributes = f"{match.group(1).strip()} {match.group(3).strip()}".strip()
            tag_content = match.group(4)
            html_tag = (
                heading if heading in ("h1", "h2", "h3", "h4", "h5", "h6") else "h1"
            )
            return f"<{html_tag} {attributes}>{tag_content}</{html_tag}>".strip()

        code = re.sub(pattern_one, replace_heading, code, flags=re.DOTALL)
        code = re.sub(pattern_two, replace_heading, code, flags=re.DOTALL)
        return code

    @staticmethod
    def transform_loops(code: str) -> str:
        def replace_loop(match: re.Match) -> str:
            loop_content = match.group(1).strip()
            for_match = re.match(
                r"\$([\w_]+)\s*=\s*(\S+)\s*;\s*\$\1\s*([<>=!]+)\s*(\S+)\s*;\s*\$\1([\+\-]+)",
                loop_content,
            )
            if for_match:
                var, start, _, end, _ = for_match.groups()
                return f'<div v-for="{var} in Array.from({{length: {end} - {start} + 1}}, (_, i) => i + {start})" :key="{var}">'
            parts = [part.strip() for part in re.split(r"(?i)\s+as\s*", loop_content)]
            if len(parts) == 2:
                items, item = parts
                if "=>" in item:
                    key, value = item.split("=>")
                    if key.strip() in ("$key", "$index"):
                        key = "$idx"
                    return f'<div v-for="({value.strip()}, {key.strip()}) in {items}" :key="{key.strip()}">'
                else:
                    if item.strip() in ("$key", "$index"):
                        item = "$idx"
                    return (
                        f'<div v-for="{item.strip()} in {items}" :key="{item.strip()}">'
                    )
            return match.group(0)

        code = rx.sub(r"(?i)@for(?:each)?\s*" + R_BR, replace_loop, code)  # type: ignore[overloads]
        return code

    @staticmethod
    def transform_concatenated(code: str) -> str:
        concat_code_regex = r"""(?<!\w)((?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`|\$[\w_]*(?:->[\w]+)*(?:\[[^\]]+\])*)
                          (?:\s*\.\s*(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`|\$[\w_]*(?:->[\w]+)*(?:\[[^\]]+\])*))+)"""
        split_concat_regex = r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`|\$[\w_]*(?:->[\w]+)*(?:\[[^\]]+\])*)|\s*\.\s*"""

        def is_quoted(s: str) -> Optional[re.Match]:
            return re.match(r'^[\'"`].*[\'"`]$', s.strip())

        matches = list(rx.compile(concat_code_regex, rx.VERBOSE).finditer(code))
        if matches:
            for match in matches:
                concat_str = match.group(1)
                parts = cast(list, Data.remove_empty_items(
                    rx.compile(split_concat_regex, rx.VERBOSE).findall(concat_str)
                ))
                if any(char in item for item in parts for char in ('"', "'", "`")):
                    is_str, transformed = 0, ""
                    for i, part in enumerate(parts):
                        part = part.strip()
                        if is_quoted(part):
                            transformed += part[1:-1]
                            is_str += 1
                        else:
                            if i == 0 and not is_quoted(parts[i + 1]):
                                transformed += f"${{{part} +"
                            elif i == len(parts) - 1 and not is_quoted(parts[i - 1]):
                                transformed += f" {part}}}"
                            elif i == 0 or i == len(parts) - 1:
                                transformed += f"${{{part}}}"
                            else:
                                prev_quoted = is_quoted(parts[i - 1])
                                next_quoted = is_quoted(parts[i + 1])
                                if not prev_quoted and not next_quoted:
                                    transformed += f" {part} +"
                                elif prev_quoted and not next_quoted:
                                    transformed += f"${{{part} +"
                                elif not prev_quoted and next_quoted:
                                    transformed += f" {part}}}"
                                else:
                                    transformed += f"${{{part}}}"
                    if not (is_str == len(parts)):
                        transformed = f"`{transformed}`"
                else:
                    transformed = " + ".join(parts)
                code = code.replace(concat_str, transformed)
        return code

    @staticmethod
    def transform_self_closing_tags(
        code: str,
        disallowed_tags: list = [
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        ],
    ) -> str:
        def replace_self_closing_tag(match: re.Match) -> str:
            tag = match.group(2)
            if tag in disallowed_tags:
                return f"<{tag} {match.group(3).strip()}>"
            return (
                match.group(0)
                if match.group(1)
                else f"<{tag} {match.group(3).strip()} />"
            )

        code = re.sub(  # CORRECT ALREADY PRESENT, BUT FORBIDDEN SELF-CLOSING TAGS
            r"<(/?)([\w.-]+)\s*(" + Regex.all_except(r"<|>") + r")\s*/>",
            replace_self_closing_tag,
            code,
            flags=re.DOTALL,
        )
        return re.sub(
            r"<(/?)([\w.-]+)\s*(" + Regex.all_except(r"<|>") + r")>\s*</\2\s*>",
            replace_self_closing_tag,
            code,
            flags=re.DOTALL,
        )

    @staticmethod
    def update_js(code: str, imports: dict, add_js: list, indent: Optional[int] = None) -> str:
        if not (imports or add_js):
            return code
        if not indent or indent < 0:
            indent = 0
        pattern = (
            r"<script(\s+[\s\S]*)?>"
            + Regex.all_except(r"<\/script\s*>", is_group=True)
            + r"<\/script\s*>\s*(?=\s*$)"
        )
        js_parts = {"new": [], "old": []}
        if imports:
            js_parts = {
                "new": [
                    f"import {name} from '{path}';" for (name), path in imports.items()
                ]
            }
        if add_js:
            js_parts["new"] += [""] + add_js

        def add_new_script(match: re.Match) -> str:
            attrs = match.group(1) if not match.group(1) else match.group(1).strip()
            old_js = match.group(2).rstrip(" \n")
            js_parts["old"] = old_js.splitlines()
            updated_js = (
                [*js_parts["new"], *js_parts["old"]] if old_js else [js_parts["new"]]
            )
            updated_js = "\n".join([f"{indent * ' '}{line}" for line in updated_js])
            return f"<script{f' {attrs}' if attrs else ''}>\n{updated_js}\n</script>"

        if re.search(pattern, code, flags=re.DOTALL):
            code = re.sub(pattern, add_new_script, code, flags=re.DOTALL)
        else:
            code += f'\n\n<script setup lang="ts">\n{"".join([f"{indent * ' '}{line}" for line in js_parts["new"]])}\n</script>'
        return code

    def convert(self, code: str, indent: int = 2) -> str:
        code = self.transform_concatenated(code)
        self.add_php_funcs(code, JSON["php_as_js_functions"])
        code = self.transform_script_lang_funcs(code)

        code = rx.sub(  # REPLACE `value->count()` WITH `value.length`
            r"(?i)([\w.-]*\s*[)\]}]?)\s*->\s*count\s*" + R_BR, r"\1.length", code
        )
        code = rx.sub(  # REPLACE `count(  )` AND `strlen(  )` WITH `.length`
            r"(?i)(?:count|strlen)\s*" + R_BR, r"\1.length", code
        )
        code = rx.sub(  # TRANSFORM `<tagname {{ $var.merge(['key_name' => 'values']) }} ...>` INTO `<tagname key_name="values" ...>`
            r"<([\w.-]+)\s+\{\{\s*(\$[\w_]+)\s*->\s*merge\s*\(\s*"
            + S_BR
            + r"\s*\)\s*\}\}(.*?)/?>(\s*(?:\n|<[\w.-]+\s+|$))",
            lambda m: f'<{m.group(1)} {' '.join(f'{a.strip(' \'"')}="{v.strip(' \'"')}"' for a, v in re.findall(r',?\s*(.*)\s*=>\s*(.*)', m.group(3)))} {m.group(4).strip()}>{m.group(5)}',
            code,
        )
        code = re.sub(  # TRANSFORM ARROW CHAINS TO DOT CHAINS
            r"([\w.-]*\s*[)\]}]?)\s*->\s*(?=\w\s*(\(.*?\))?)", r"\1.", code
        )

        # code = self.transform_slots(code)
        code = self.transform_tag_names(code, JSON["component_replacements"])
        code = self.transform_func_names(code, JSON["function_replacements"])
        code = self.transform_self_closing_tags(code)
        code = self.transform_headings(code)
        code = self.transform_loops(code)

        code = re.sub(r"--}}", "-->", code)  # CORRECT COMMENT ENDS
        code = re.sub(r"{{--", "<!--", code)  # CORRECT COMMENT STARTS
        code = re.sub(r"<br\s*/>", "<br>", code)  # CORRECT LINE-BREAK TAGS
        code = re.sub(  # CHANGE VARIABLES `$key`, `$index` TO `$idx`
            r"\$(key|index)(?!\s*\()", "$idx", code
        )
        code = re.sub(  # CHANGE `loop.first` TO `idx == 0`
            r"\s*loop\.first\s*", "idx == 0", code
        )
        code = re.sub(  # CHANGE `loop.last` TO `idx == ….length - 1`
            r"\s*loop\.last\s*", "idx == ….length - 1", code
        )
        code = re.sub(  # CORRECT EQUALS
            r"(?<=[^!<>=\s])\s*([!=])=\s*(?=[^=\s])", r" \1== ", code
        )
        code = re.sub(  # REMOVE EMPTY ATTRIBUTES
            r'(?<![\w$])(\s*:?([\w-]+)\s*=\s*([\'"]))\3', "", code
        )
        code = rx.sub(  # REMOVE `init-errors` VARIABLES
            r"\s*:\s*init-errors\s*=\s*" + QUOTES + r"(\s*(?:\n|$))", "", code
        )
        code = re.sub(  # REPLACE `{{ $slot }}` WITH `<slot />`
            r"(?:<div\s*>\s*)?{{\s*\$(slot)\s*}}(?:\s*</div\s*>)?", r"<\1 />", code
        )
        code = re.sub(  # REPLACE `@php` SYNTAX WITH `<!--` COMMENT-START
            r"(?i)(@php)", r"<!-- \1", code
        )
        code = re.sub(  # REPLACE `@endphp` SYNTAX WITH `-->` COMMENT-END
            r"(?i)\s*@endphp", r" -->", code
        )
        code = rx.sub(  # REPLACE `import { route } from '...';` WITH `import { route } from '@/plugins/route';`
            r"import\s*{\s*route\s*}\s*from\s*" + QUOTES + r"\s*;",
            "import { route } from '@/plugins/route';",
            code,
        )
        code = rx.sub(  # REPLACE `<div @if(true) attr>` SYNTAX WITH `<div :attr="true">` ATTRIBUTES
            r"(?i)(<(?!/)[\w.-]+"
            + Regex.all_except(r"<|>|@if")
            + r")@if\s*"
            + R_BR
            + r"((?:\s+[\w-]+)?)("
            + Regex.all_except(r"<|>")
            + r">)",
            lambda m: (
                f'{m.group(1)}:{m.group(3).strip()}="{m.group(2).strip()}"{m.group(4)}'
                if m.group(3).strip()
                else m.group(0)
            ),
            code,
            flags=re.DOTALL,
        )
        code = rx.sub(  # REPLACE `<div @empty(var) attr>` SYNTAX WITH `<div :attr="!var">` ATTRIBUTES
            r"(?i)(<(?!/)[\w.-]+"
            + Regex.all_except(r"<|>|@empty")
            + r")@empty\s*"
            + R_BR
            + r"((?:\s+[\w-]+)?)("
            + Regex.all_except(r"<|>")
            + r">)",
            lambda m: (
                f'{m.group(1)}:{m.group(3).strip()}="!({m.group(2).strip()})"{m.group(4)}'
                if m.group(3).strip()
                else m.group(0)
            ),
            code,
            flags=re.DOTALL,
        )
        code = rx.sub(  # REPLACE `<div @isset(var) attr>` SYNTAX WITH `<div :attr="(var) !== undefined">` ATTRIBUTES
            r"(?i)(<(?!/)[\w.-]+"
            + Regex.all_except(r"<|>|@isset")
            + r")@isset\s*"
            + R_BR
            + r"((?:\s+[\w-]+)?)("
            + Regex.all_except(r"<|>")
            + r">)",
            lambda m: (
                f'{m.group(1)}:{m.group(3).strip()}="({m.group(2).strip()}) !== undefined"{m.group(4)}'
                if m.group(3).strip()
                else m.group(0)
            ),
            code,
            flags=re.DOTALL,
        )
        code = rx.sub(  # REPLACE `<div @is_null(var) attr>` SYNTAX WITH `<div :attr="(var) === null">` ATTRIBUTES
            r"(?i)(<(?!/)[\w.-]+"
            + Regex.all_except(r"<|>|@is_null")
            + r")@is_null\s*"
            + R_BR
            + r"((?:\s+[\w-]+)?)("
            + Regex.all_except(r"<|>")
            + r">)",
            lambda m: (
                f'{m.group(1)}:{m.group(3).strip()}="({m.group(2).strip()}) === null"{m.group(4)}'
                if m.group(3).strip()
                else m.group(0)
            ),
            code,
            flags=re.DOTALL,
        )
        code = rx.sub(  # REMOVE `@end...` SYNTAX INSIDE TAG-ATTRIBUTES
            r"(?i)(<(?!/)[\w.-]+"
            + Regex.all_except(r"<|>|@end(?:[\w_]+)")
            + r")@end([\w_]+)("
            + Regex.all_except(r"<|>")
            + r">)",
            r"\1\3",
            code,
            flags=re.DOTALL,
        )
        code = rx.sub(  # REPLACE `@if(  )` SYNTAX WITH `<span v-if="  ">` TAGS
            r"(?i)@if\s*" + R_BR, r'<span v-if="\1">', code
        )
        code = rx.sub(  # REPLACE `@empty(  )` SYNTAX WITH `<span v-if="!(  )">` TAGS
            r"(?i)@empty\s*" + R_BR, r'<span v-if="!(\1)">', code
        )
        code = rx.sub(  # REPLACE `@isset(  )` SYNTAX WITH `<span v-if="(  ) !== undefined">` TAGS
            r"(?i)@isset\s*" + R_BR, r'<span v-if="(\1) !== undefined">', code
        )
        code = rx.sub(  # REPLACE `@is_null(  )` SYNTAX WITH `<span v-if="(  ) === null">` TAGS
            r"(?i)@is_null\s*" + R_BR, r'<span v-if="(\1) === null">', code
        )
        code = rx.sub(  # REPLACE `@elseif(  )` SYNTAX WITH `</span><span v-else-if="  ">` TAGS
            r"(?i)@elseif\s*" + R_BR, r'</span><span v-else-if="\1">', code
        )
        code = re.sub(  # REPLACE `@else` SYNTAX WITH `</span><span v-else>` TAGS
            r"(?i)@else(\s+)", r"</span><span v-else>\1", code
        )
        code = re.sub(  # REPLACE `@end...` SYNTAX WITH `</div>` or `</span>` END-TAGS
            r"(?i)@end([\w_]+)",
            lambda m: (
                "</span>"
                if m.group(1) in ("if", "isset", "elseif", "else")
                else "</div>"
            ),
            code,
        )
        code = rx.sub(  # REPLACE `<div v-if="$slot"><slot name="...">{{ $slot }}</slot></div>` WITH `<slot />` OR `<slot name="..." />`
            r'<([\w-]+)\s+v-if\s*=\s*"\s*\$?slot\s*"\s*>\s*<slot(?:\s+name\s*=\s*'
            + QUOTES
            + r")?\s*>\s*{{\s*\$?slot\s*}}\s*</slot\s*>\s*</\1\s*>",
            lambda m: f'<slot{f' name="{m.group(3).strip()}"' if m.group(3).strip() else ''} />',
            code,
        )
        code = rx.sub(  # REPLACE `__()` AND `$lang()` FUNCTIONS WITH `$t()` FUNCTION
            L_FN + r"\s*\((.*?\))", r"$t(\1", code
        )
        code = re.sub(  # REPLACE `{!!  !!}` SYNTAX WITH `<div v-html="  "/>` TAGS
            r"{!!\s*(.*?)\s*!!}", r'<div v-html="\1"/>', code
        )
        code = re.sub(  # REPLACE `:input="$input"` WITH `:input`
            r':([\w-]+)\s*=\s*([\'"])\s*\$?\1\s*\2', r":\1", code
        )
        code = rx.sub(  # REPLACE LEFTOVER `attr="JS"` WITH `:attr="JS"` OR `:attr="string"` WITH `attr="string"`
            r":?([\w-]+)\s*=\s*" + QUOTES,
            lambda m: (
                f':{m.group(1)}="{m.group(3).strip()}"'
                if Code.is_js(m.group(3).strip())
                else f'{m.group(1)}="{m.group(3).strip()}"'
            ),
            code,
        )
        code = rx.sub(  # REPLACE LEFTOVER `attr="{{  }}"` WITH `:attr="  "`
            r':?([\w-]+)\s*=\s*([\'"])\s*\{' + C_BR + r"\}\s*\2",
            lambda m: f':{m.group(1)}="{m.group(3).strip()}"',
            code,
        )
        code = rx.sub(  # REPLACE `{{  }}`-CONCATENATED STRINGS WITH BACKTICK-STRINGS
            r':?([\w-]+)\s*=\s*([\'"])(((?:\\.|(?:(?!\2).)+)*)\{'
            + C_BR
            + r"\}((?:\\.|(?:(?!\2).)+)*))\2",
            lambda m: f':{m.group(1)}="`{m.group(3).replace('{{', '${').replace('}}', '}')}`"',
            code,
        )
        code = rx.sub(  # REMOVE `asset(  )` BRACKETS
            r"(?i)asset\s*" + R_BR, r"\1", code
        )
        code = rx.sub(  # REMOVE `isset(  )` BRACKETS
            r"(?i)isset\s*" + R_BR, r"(\1)", code
        )
        code = re.sub(  # COMMENT OUT LEFTOVER BLADE SYNTAX
            r"(\n\s*)(@[\w_]+.*?)(\s*\n)", r"\1<!-- \2 -->\3", code
        )
        code = rx.sub(  # REMOVE `:` FROM VUE-ATTRIBUTES
            r":v-([\w-]+)\s*=\s*" + QUOTES, r'v-\1="\3"', code
        )
        code = re.sub(  # REMOVE UNNECESSARY QUOTATION MARKS
            r':?([\w-]+)\s*=\s*([\'"])\s*((?:\\\2|(?:(?!\2)[\'"]))+)((?:\\.|(?:(?!\2).)+)*)\3\s*\2',
            lambda m: f'{m.group(1)}="{m.group(4).strip().replace("\\'", "'")}"',
            code,
        )
        code = rx.sub(  # REMOVE UNNECESSARY VARIABLE INPUTS
            r"\$attributes\s*\[\s*" + QUOTES + r"\s*\]", r"\2", code
        )
        code = re.sub(  # REMOVE LEFTOVER `$` PREFIXES FROM VARS AND FUNCTIONS
            r"\$(\w+)(?!\s*\()",
            lambda m: m.group(1) if not m.group(1) == "t" else m.group(0),
            code,
        )

        outside_template_script_pattern = (r"(<script(?:\s+[\s\S]*)?>" + Regex.all_except(r"<\/script\s*>") + r"<\/script\s*>\s*)(?=\s*$)")
        outside_template_script = "\n".join(rx.findall(outside_template_script_pattern, code, flags=re.DOTALL))
        code = rx.sub(  # REMOVE OUTSIDE TEMPLATE SCRIPT
            outside_template_script_pattern, "", code, flags=re.DOTALL
        )
        vue_content = f"<template>\n{Code.add_indent(code.strip(), Code.get_tab_spaces(code))}\n</template>\n\n{outside_template_script}"
        if isinstance(args.indent.value, int):
            vue_content = String.remove_consecutive_empty_lines(vue_content, max_consecutive=1)
            Console.debug("Removed consecutive empty lines to [b|+]max_consecutive=1[_].", DEBUG, start="\n")
            if not args.indent.value < 1:
                vue_content = Code.change_tab_size(vue_content, indent, remove_empty_lines=True)
                Console.debug(f"Changed tab size to [b|+]{indent}[_] spaces and removed [b|+]all[_] empty lines.", DEBUG, start="\n")
        return self.update_js(vue_content, JS_IMPORTS, ADD_JS)


def main(args: Args):
    get_json(args)
    if DEBUG and not Data.is_equal(_JSON, DEFAULT_JSON, ignore_paths="is_in_env_vars"):
        Console.debug(f"{JSON_FILE} does not match the default json.")
    add_to_env_vars()
    args = get_missing_args(args)
    if args.filepath.value in (None, ""):
        Console.fail("No filepath was provided.", pause=DEBUG, end="\n\n")
    args.filepath.value = FileSys.extend_path(str(args.filepath.value), raise_error=True, fuzzy_match=True)
    if not os.path.isfile(args.filepath.value or ""):
        Console.fail(f"Path is not a file: [white]{args.filepath.value}", pause=DEBUG)

    with open(args.filepath.value or "", "r") as file:
        file_content = file.read()
    converter = blade_to_vue()
    converted_content = (converter.convert(file_content, int(args.indent.value or 2)) if args.blade_vue.exists else None)

    if converted_content:
        new_file_path = File.rename_extension(args.filepath.value or "", ".vue", camel_case_filename=True)
        if os.path.exists(new_file_path):
            with open(new_file_path, "r") as existing_file:
                existing_content = existing_file.read()
            if existing_content == converted_content:
                Console.info("Already formatted this file. [dim](nothing changed)", pause=DEBUG, start="\n", end="\n\n")
                Console.pause_exit(exit=True, reset_ansi=True)
            Console.warn(f"File already exists: [white]{new_file_path}", exit=False, start="\n")
            if Console.confirm(f"      \tDo you want to replace [+|b]{os.path.basename(new_file_path)}[*]?", start="\n", end=""):
                pass
            else:
                Console.exit(reset_ansi=True, start="\n", end="\n\n")
        with open(new_file_path, "w") as file:
            file.write(converted_content)
        Console.done(f"Formatted into file: [white]{new_file_path}", pause=DEBUG, start="\n", end="\n\n")
    else:
        Console.fail("Empty file or invalid conversion chosen.", pause=DEBUG, start="\n", end="\n\n")
    Console.pause_exit(exit=True, reset_ansi=True)


if __name__ == "__main__":
    args = Console.get_args(allow_spaces=True, **FIND_ARGS)
    DEBUG = args.debug.exists
    if DEBUG:
        if args.help.exists:
            show_help()
        else:
            main(args)
    else:
        try:
            if args.help.exists:
                show_help()
            else:
                main(args)
        except FileNotFoundError:
            Console.fail(f"File not found: [white]{args.filepath.value}", pause=DEBUG, start="\n", end="\n\n")
        except KeyboardInterrupt:
            Console.exit(start="\n\n", end="\n\n")
        except Exception as e:
            Console.fail(e, pause=DEBUG, start="\n", end="\n\n")
