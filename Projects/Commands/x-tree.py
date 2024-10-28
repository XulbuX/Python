import XulbuX as xx
import sys
import os
import re

ARGS = sys.argv[1:]
DEFAULTS = {
  'ignore_dirs': [],
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
  def get_style(style=1):
    return Tree.styles.get(style, Tree.styles[1])

  @staticmethod
  def get_valid_styles():
    return list(Tree.styles.keys())

  @staticmethod
  def show_styles():
    for style, details in Tree.styles.items():
      style_example = details['branch_end'] + details['line_hor'] + details['skipped'] + details['dirname_end']
      print(f'{style}: {style_example}', flush=True)


def is_valid_path(path):
  try:
    if not isinstance(path, str) or not path: return False
    if os.name == 'nt': invalid_chars = r'[\\/:*?"<>|]'
    else: invalid_chars = r'\0'
    if re.search(invalid_chars, path): return False
    return True
  except: return False

def get_tree(base_dir, ignore_dirs=None, style=1, indent=3, level=0, prefix=''):
  result = ''
  try:
    if ignore_dirs in [None, '']: ignore_dirs = []
    is_last = False
    tab = ' ' * indent
    tree = Tree.get_style(style)
    items = sorted(os.listdir(base_dir))
    line_hor = tree['line_hor'] * (indent - 1)
    base_dir_name = os.path.basename(base_dir.rstrip(os.sep))
    if level == 0:
      if base_dir_name == '':
        drive_letter = os.path.splitdrive(base_dir)[0]
        base_dir_name = drive_letter
      result += f'{base_dir_name}{tree['dirname_end']}\n'
    for index, item in enumerate(items):
      item_path = os.path.join(base_dir, item)
      is_last = index == len(items) - 1
      if item in ignore_dirs:
        result += prefix + (tree['branch_end'] if is_last else tree['branch_new']) + line_hor + item + tree['dirname_end'] + '\n'
        skipped_prefix = prefix + (tab if is_last else tree['line_ver'] + tab[:-1])
        result += skipped_prefix + tree['branch_end'] + line_hor + tree['skipped'] + '\n'
        continue
      if os.path.isdir(item_path):
        result += prefix + (tree['branch_end'] if is_last else tree['branch_new']) + line_hor + item + tree['dirname_end'] + '\n'
        new_prefix = prefix + (tab if is_last else (tree['line_ver'] + tab[:-1]))
        result += get_tree(item_path, ignore_dirs, style, indent, level + 1, new_prefix)
      else: result += prefix + (tree['branch_end'] if is_last else tree['branch_new']) + line_hor + item + '\n'
  except Exception as e:
    error_prefix = prefix + tree['branch_end'] + (tree['line_hor'] * (indent - 1))
    result += f'{error_prefix}{tree['error']} [Error: {str(e)}]\n'
  return result



def main():
  base_dir = os.getcwd()

  if len(ARGS) > 1:
    if ARGS[0] in ['-i', '--ignore']: ignore_dirs = ARGS[1:]
    elif ARGS[1] in ['-i', '--ignore']: ignore_dirs = ARGS[2:]
  else: ignore_dirs = xx.FormatCodes.input('Enter directories to ignore [dim]((`/` separated) >  )').strip().split('/')
  ignore_dirs = [subitem for item in ignore_dirs for subitem in item.split('/')]

  print('Enter the tree style (1-4): ')
  Tree.show_styles()
  tree_style = xx.FormatCodes.input(f'[dim]([default is {DEFAULTS["tree_style"]}] >  )').strip()
  tree_style = int(tree_style) if tree_style.isnumeric() and int(tree_style) in Tree.get_valid_styles() else DEFAULTS['tree_style']
  indent = xx.FormatCodes.input(f'Enter the indent [dim]([default is {DEFAULTS["indent"]}] >  )').strip()
  indent = int(indent) if indent.isnumeric() and int(indent) >= 0 else DEFAULTS['indent']
  into_file = True if xx.FormatCodes.input('Output tree into file [dim]((y/N) >  )').strip().lower() in ['y', 'yes'] else DEFAULTS['into_file']

  xx.Cmd.info('generating tree ...', end='\n')
  result = get_tree(base_dir, ignore_dirs, tree_style, indent)

  if into_file:
    file = None
    try: file = xx.File.create(result, 'tree.txt')
    except FileExistsError:
      if xx.Cmd.confirm(f'[white]tree.txt[_] already exists. Overwrite? [dim]((Y/n) >  )', end=''): file = xx.File.create(result, 'tree.txt', force=True)
      else: xx.Cmd.exit()
    if file: xx.Cmd.done(f'[white]{file}[_] successfully created.')
    else: xx.Cmd.fail('File is empty or failed to create file.')
  else:
    xx.FormatCodes.print('[white]')
    print(result, end='', flush=True)
    xx.FormatCodes.print('[_]')



if __name__ == '__main__':
  try: main()
  except KeyboardInterrupt: xx.Cmd.exit()
  except PermissionError: xx.Cmd.fail('Permission to create file was denied.')
  except Exception as e: xx.Cmd.fail(str(e))
