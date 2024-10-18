import XulbuX as xx

FIND_ARGS = {
  'f': ['-f', '--file', '-p', '--path', '-fp', '--filepath', '--file-path'],
  'r': ['-r', '--replace', '-rs', '--replace-string'],
  'w': ['-w', '--with', '-rw', '--replace-with']
}


def get_missing_args(args):
  if not args['f']['value']: args['f']['value'] = input('Path to your file >   ').strip()
  if not args['r']['value']: args['r']['value'] = input('String to replace >   ').strip()
  if not args['w']['value']: args['w']['value'] = input('Replacement string >  ').strip()
  return args

def replace_in_file(file_path:str, replace_str:str, replace_with:str):
  xx.Cmd.info('replacing...')
  with open(file_path, 'r') as file:
    content = file.read()
  updated_content = content.replace(replace_str, replace_with)
  with open(file_path, 'w') as file:
    file.write(updated_content)
  xx.Cmd.done(f'replaced all [white]{replace_str}[_] with [white]{replace_with}[_]')


if __name__ == "__main__":
  try:
    args = xx.Cmd.get_args(FIND_ARGS)
    args = get_missing_args(args)
    replace_in_file(args['f']['value'], args['r']['value'], args['w']['value'])
  except KeyboardInterrupt:
    xx.Cmd.exit(start='\n\n')
  except Exception as e:
    xx.Cmd.fail(e)
