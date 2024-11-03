import XulbuX as xx
import sys
import os
import re
from functools import lru_cache
from typing import List, Set, Dict, Optional
from itertools import chain

ARGS = sys.argv[1:]
DEFAULTS = {
    'ignore_dirs': [],
    'file_contents': False,
    'tree_style': 1,
    'indent': 3,
    'into_file': False
}




class Tree:

    def __init__(self):
        self._styles = {
            1: {'line_ver':'│', 'line_hor':'─', 'branch_new':'├', 'corners':['└', '┘', '┐'], 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
            2: {'line_ver':'│', 'line_hor':'─', 'branch_new':'├', 'corners':['╰', '╯', '╮'], 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
            3: {'line_ver':'┃', 'line_hor':'━', 'branch_new':'┣', 'corners':['┗', '┛', '┓'], 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
            4: {'line_ver':'║', 'line_hor':'═', 'branch_new':'╠', 'corners':['╚', '╝', '╗'], 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
        }
        # CACHE CURRENT STYLE ATTRIBUTES FOR FASTER ACCESS
        self._current_style = None
        self._line_ver = None
        self._line_hor = None
        self._branch_new = None
        self._corners = None
        self._error = None
        self._skipped = None
        self._dirname_end = None


    def _set_style(self, style:int) -> None:
        """Set current style attributes for faster access"""
        if self._current_style != style:
            style_dict = self._styles.get(style, self._styles[1])
            self._current_style = style
            self._line_ver = style_dict['line_ver']
            self._line_hor = style_dict['line_hor']
            self._branch_new = style_dict['branch_new']
            self._corners = style_dict['corners']
            self._error = style_dict['error']
            self._skipped = style_dict['skipped']
            self._dirname_end = style_dict['dirname_end']


    def show_styles(self) -> None:
        for style, details in self.styles.items():
            print(f'{style}: {details["corners"][0]}{details["line_hor"]}{details["skipped"]}{details["dirname_end"]}', flush=True)


    def generate(self, base_dir:str, ignore_dirs:Optional[list[str]] = None, file_contents:bool = False, style:int = 1, indent:int = 3, _prefix:str = '', _level:int = 0) -> str:
        self._set_style(style)
        result_parts = []

        try:
            ignore_set = set(ignore_dirs) if ignore_dirs else set()

            tab = ' ' * indent
            line_hor_mult = indent - 2 if indent > 2 else 1 if indent == 2 else 0
            line_hor = self._line_hor * line_hor_mult
            error_prefix = _prefix + self._corners[0] + (self._line_hor * (indent - 1))

            if _level == 0:
                base_dir_name = os.path.basename(base_dir.rstrip(os.sep))
                if not base_dir_name:
                    base_dir_name = os.path.splitdrive(base_dir)[0]
                result_parts.append(f'{base_dir_name}{self._dirname_end}\n')

            items = sorted(os.listdir(base_dir))
            items_count = len(items)

            for index, item in enumerate(items):
                is_last = index == items_count - 1
                item_path = os.path.join(base_dir, item)
                is_dir = os.path.isdir(item_path)
                branch = self._corners[0] if is_last else self._branch_new
                current_line = _prefix + branch + line_hor

                if item in ignore_set:
                    result_parts.append(f'{current_line}{item}{self._dirname_end if is_dir else ""}\n')
                    if is_dir:
                        next_prefix = _prefix + (tab if is_last else self._line_ver + tab[:-1])
                        result_parts.append(f'{next_prefix}{self._corners[0]}{line_hor}{self._skipped}\n')
                    continue

                if is_dir:
                    result_parts.append(f'{current_line}{item}{self._dirname_end}\n')
                    new_prefix = _prefix + (tab if is_last else (self._line_ver + tab[:-1]))
                    result_parts.append(self.generate(item_path, list(ignore_set), file_contents, style, indent, new_prefix, _level + 1))

                else:
                    result_parts.append(f'{current_line}{item}\n')
                    if file_contents:
                        content_prefix = _prefix + (tab if is_last else self._line_ver + tab[:-1])
                        try:
                            with open(item_path, 'r', encoding='utf-8', errors='replace') as f:
                                lines = f.readlines()
                                if lines:  # ONLY PROCESS IF FILE HAS CONTENT
                                    content_width = max(len(line.rstrip()) for line in lines)
                                    hor_border = self._line_hor * (content_width + 2)
                                    result_parts.append(f'{content_prefix}{self._branch_new}{hor_border}{self._corners[2]}\n')  # TOP BORDER
                                    for line in lines:  # CONTENT LINES
                                        stripped = line.rstrip()
                                        padding = ' ' * (content_width - len(stripped))
                                        result_parts.append(f'{content_prefix}{self._line_ver} {stripped}{padding} {self._line_ver}\n')
                                    result_parts.append(f'{content_prefix}{self._corners[0]}{hor_border}{self._corners[1]}\n')  # BOTTOM BORDER
                        except:
                            result_parts.append(f'{content_prefix}{error_prefix}{self._error} [Error reading file contents]\n')

        except Exception as e:
            result_parts.append(f'{error_prefix}{self._error} [Error: {str(e)}]\n')
        return ''.join(result_parts)




@lru_cache(maxsize=1024)
def is_valid_path(path: str) -> bool:
    if not isinstance(path, str) or not path:
        return False
    try:
        invalid_chars = r'[\\/:*?"<>|]' if os.name == 'nt' else r'\0'
        return not bool(re.search(invalid_chars, path))
    except:
        return False




def main():
    if len(ARGS) > 1:
        if ARGS[0] in ['-i', '--ignore']:
            ignore_dirs = ARGS[1:]
        elif ARGS[1] in ['-i', '--ignore']:
            ignore_dirs = ARGS[2:]
    else:
        ignore_input = xx.FormatCodes.input("Enter directories or files which's content should be ignore [dim]((`/` separated) >  )").strip()
        ignore_dirs = list(chain.from_iterable(item.split('/') for item in ignore_input.split('/')))

    file_contents = xx.FormatCodes.input(
        f'Display the file contents in the tree [dim]({"(Y/n)" if DEFAULTS["file_contents"] else "(y/N)"} >  )'
    ).strip().lower() in ['y', 'yes']

    print('Enter the tree style (1-4): ')
    Tree.show_styles()
    tree_style = xx.FormatCodes.input(f'[dim]([default is {DEFAULTS["tree_style"]}] >  )').strip()
    tree_style = int(tree_style) if tree_style.isnumeric() and 1 <= int(tree_style) <= 4 else DEFAULTS['tree_style']

    indent = xx.FormatCodes.input(f'Enter the indent [dim]([default is {DEFAULTS["indent"]}] >  )').strip()
    indent = int(indent) if indent.isnumeric() and int(indent) >= 0 else DEFAULTS['indent']

    into_file = xx.FormatCodes.input(
        f'Output tree into file [dim]({"(Y/n)" if DEFAULTS["into_file"] else "(y/N)"} >  )'
    ).strip().lower() in ['y', 'yes']

    xx.Cmd.info('generating tree ...', end='\n')
    tree = Tree()
    result = tree.generate(os.getcwd(), ignore_dirs, file_contents, tree_style, indent)

    if into_file:
        file = None
        try:
            file = xx.File.create(result, 'tree.txt')
        except FileExistsError:
            if xx.Cmd.confirm('[white]tree.txt[_] already exists. Overwrite? [dim]((Y/n) >  )', end=''):
                file = xx.File.create(result, 'tree.txt', force=True)
            else:
                xx.Cmd.exit()
        if file:
            xx.Cmd.done(f'[white]{file}[_] successfully created.')
        else:
            xx.Cmd.fail('File is empty or failed to create file.')
    else:
        xx.FormatCodes.print('[white]')
        print(result, end='', flush=True)
        xx.FormatCodes.print('[_]')




if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        xx.Cmd.exit()
    except PermissionError:
        xx.Cmd.fail('Permission to create file was denied.')
    except Exception as e:
        xx.Cmd.fail(str(e))
