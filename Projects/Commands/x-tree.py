import XulbuX as xx
import sys
import os
import re

ARGS = sys.argv[1:]
DEFAULTS = {
    'ignore_dirs': [],
    'file_contents': False,
    'tree_style': 1,
    'indent': 3,
    'into_file': False
}



class Tree:
    styles = {
        1: {'line_ver':'│', 'line_hor':'─', 'branch_new':'├', 'branch_end':'└', 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
        2: {'line_ver':'│', 'line_hor':'─', 'branch_new':'├', 'branch_end':'╰', 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
        3: {'line_ver':'┃', 'line_hor':'━', 'branch_new':'┣', 'branch_end':'┗', 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
        4: {'line_ver':'║', 'line_hor':'═', 'branch_new':'╠', 'branch_end':'╚', 'error':'⚠', 'skipped':'...', 'dirname_end':'/'},
    }

    @staticmethod
    def get_style(style:int = 1) -> dict:
        return Tree.styles.get(style, Tree.styles[1])

    @staticmethod
    def get_valid_styles() -> list:
        return list(Tree.styles.keys())

    @staticmethod
    def show_styles() -> None:
        for style, details in Tree.styles.items():
            style_example = details['branch_end'] + details['line_hor'] + details['skipped'] + details['dirname_end']
            print(f'{style}: {style_example}', flush=True)



def is_valid_path(path:str) -> bool:
    try:
        if not isinstance(path, str) or not path:
            return False
        elif os.name == 'nt':
            invalid_chars = r'[\\/:*?"<>|]'
        else:
            invalid_chars = r'\0'
        if re.search(invalid_chars, path):
            return False
        return True
    except:
        return False

def get_tree(base_dir:str, ignore_dirs:list[str] = None, file_contents:bool = False, style:int = 1, indent:int = 3, _prefix:str = '', _level:int = 0) -> str:
    result = ''
    try:
        if ignore_dirs in [None, '']:
            ignore_dirs = []
        is_last = False
        tab = ' ' * indent
        tree = Tree.get_style(style)
        items = sorted(os.listdir(base_dir))
        line_hor = tree['line_hor'] * (indent - 1)
        base_dir_name = os.path.basename(base_dir.rstrip(os.sep))
        error_prefix = _prefix + tree['branch_end'] + (tree['line_hor'] * (indent - 1))
        excluded_extensions = {'.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.db', '.sqlite', '.pyc', '.pyo'}
        if _level == 0:
            if base_dir_name == '':
                drive_letter = os.path.splitdrive(base_dir)[0]
                base_dir_name = drive_letter
            result += f'{base_dir_name}{tree['dirname_end']}\n'
        for index, item in enumerate(items):
            item_path = os.path.join(base_dir, item)
            is_last = index == len(items) - 1
            if item in ignore_dirs:
                result += _prefix + (tree['branch_end'] if is_last else tree['branch_new']) + line_hor + item + tree['dirname_end'] + '\n'
                skipped_prefix = _prefix + (tab if is_last else tree['line_ver'] + tab[:-1])
                result += skipped_prefix + tree['branch_end'] + line_hor + tree['skipped'] + '\n'
                continue
            if os.path.isdir(item_path):
                result += _prefix + (tree['branch_end'] if is_last else tree['branch_new']) + line_hor + item + tree['dirname_end'] + '\n'
                new_prefix = _prefix + (tab if is_last else (tree['line_ver'] + tab[:-1]))
                result += get_tree(item_path, ignore_dirs, file_contents, style, indent, new_prefix, _level + 1)
            else:
                result += _prefix + (tree['branch_end'] if is_last else tree['branch_new']) + line_hor + item + '\n'
                if file_contents and os.path.splitext(item)[1].lower() not in excluded_extensions:
                    try:
                        content_prefix = _prefix + (tab if is_last else tree['line_ver'] + tab[:-1])
                        with open(item_path, 'r', encoding='utf-8', errors='replace') as f:
                            lines = f.readlines()
                            max_line_num_len = len(str(len(lines)))
                            for i, line in enumerate(lines, 1):
                                result += f'{content_prefix} {" " * (max_line_num_len - len(str(i)))}{i}  {line.rstrip()}\n'
                            result += content_prefix + '\n'
                    except:
                        result += f'{content_prefix}{error_prefix}{tree['error']} [Error reading file contents]\n'
    except Exception as e:
        result += f'{error_prefix}{tree['error']} [Error: {str(e)}]\n'
    return result



def main():
    if len(ARGS) > 1:
        if ARGS[0] in ['-i', '--ignore']:
            ignore_dirs = ARGS[1:]
        elif ARGS[1] in ['-i', '--ignore']:
            ignore_dirs = ARGS[2:]
    else:
        ignore_dirs = xx.FormatCodes.input('Enter directories to ignore [dim]((`/` separated) >  )').strip().split('/')
    ignore_dirs = [subitem for item in ignore_dirs for subitem in item.split('/')]
    file_contents = True if xx.FormatCodes.input(f'Add file contents to tree [dim]({"(Y/n)" if DEFAULTS["file_contents"] else "(y/N)"} >  )').strip().lower() in ['y', 'yes'] else DEFAULTS['file_contents']
    print('Enter the tree style (1-4): ')
    Tree.show_styles()
    tree_style = xx.FormatCodes.input(f'[dim]([default is {DEFAULTS["tree_style"]}] >  )').strip()
    tree_style = int(tree_style) if tree_style.isnumeric() and int(tree_style) in Tree.get_valid_styles() else DEFAULTS['tree_style']
    indent = xx.FormatCodes.input(f'Enter the indent [dim]([default is {DEFAULTS["indent"]}] >  )').strip()
    indent = int(indent) if indent.isnumeric() and int(indent) >= 0 else DEFAULTS['indent']
    into_file = True if xx.FormatCodes.input(f'Output tree into file [dim]({"(Y/n)" if DEFAULTS["into_file"] else "(y/N)"} >  )').strip().lower() in ['y', 'yes'] else DEFAULTS['into_file']

    xx.Cmd.info('generating tree ...', end='\n')
    result = get_tree(os.getcwd(), ignore_dirs, file_contents, tree_style, indent)

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
    try: main()
    except KeyboardInterrupt: xx.Cmd.exit()
    except PermissionError: xx.Cmd.fail('Permission to create file was denied.')
    except Exception as e: xx.Cmd.fail(str(e))
