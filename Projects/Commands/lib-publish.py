# ALSO REQUIRES MODULES:
# - pip install build
# - pip install twine

import XulbuX as xx
import subprocess
import shutil
import sys
import os

FIND_ARGS = {'lib_base': ['-f', '--file', '-p', '--path', '-fp', '--filepath', '--file-path']}



def get_latest_python_version() -> str:
  py_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Python')
  versions = []
  try:
    for d in os.listdir(py_dir):
      if d.startswith('Python3'): versions.append(d)
    return sorted(versions)[-1] if versions else 'Python312'
  except: return 'Python312'

def find_twine_path() -> str:
  python_paths = [
    os.path.join(sys.base_prefix, 'Scripts', 'twine.exe'),
    os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Programs', 'Python', get_latest_python_version(), 'Scripts', 'twine.exe'),
    os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Python', get_latest_python_version(), 'Scripts', 'twine.exe')
  ]
  for path in python_paths:
    if os.path.isfile(path): return path
  print('Error: twine.exe not found in expected locations. Please verify installation.')
  sys.exit(1)

def run_command(command:str) -> None:
  try: subprocess.run(command, check=True, shell=True)
  except subprocess.CalledProcessError as e:
    print(f'Error executing command: {e}')
    sys.exit(1)

def remove_dir_contents(dir:str, remove_dir:bool = False) -> None:
  if os.path.exists(dir) and os.path.isdir(dir):
    if remove_dir:
      shutil.rmtree(dir)
      return None
    for filename in os.listdir(dir):
      file_path = os.path.join(dir, filename)
      try:
        if os.path.isfile(file_path) or os.path.islink(file_path): os.unlink(file_path)
        elif os.path.isdir(file_path): shutil.rmtree(file_path)
      except Exception as e: print(f'Failed to delete {file_path}. Reason: {e}')

def main(args:dict) -> None:
  os.chdir(args['lib_base']['value'])
  run_command('py -m build')
  twine_path = find_twine_path()
  run_command(f'"{twine_path}" upload dist/*')
  if input('\nDirectly remove dist directory? (Y/n):  ').lower() in ['', 'y', 'yes']:
    xx.Path.remove(os.path.join(os.getcwd(), 'dist'))
    print()



if __name__ == '__main__':
  main(xx.Cmd.get_args(FIND_ARGS))