"""
Functions for logging and other small actions within the console:
- `Cmd.get_args()`
- `Cmd.user()`
- `Cmd.is_admin()`
- `Cmd.pause_exit()`
- `Cmd.cls()`
- `Cmd.log()`
- `Cmd.debug()`
- `Cmd.info()`
- `Cmd.done()`
- `Cmd.warn()`
- `Cmd.fail()`
- `Cmd.exit()`
- `Cmd.confirm()`\n
----------------------------------------------------------------------------------------------------------
You can also use special formatting codes directly inside the log message to change their appearance.<br>
For more detailed information about formatting codes, see the `log` class description.
"""


try: from .xx_format_codes import *
except: from xx_format_codes import *

import keyboard as _keyboard
import getpass as _getpass
import ctypes as _ctypes
import shutil as _shutil
import sys as _sys
import os as _os



class Cmd:
  @staticmethod
  def get_args(find_args:dict) -> dict:
    args = _sys.argv[1:]
    results = {}
    for arg_key, arg_group in find_args.items():
      value = None
      exists = False
      for arg in arg_group:
        if arg in args:
          exists = True
          arg_index = args.index(arg)
          if arg_index + 1 < len(args) and not args[arg_index + 1].startswith('-'): value = String.to_type(args[arg_index + 1])
          break
      results[arg_key] = {'exists': exists, 'value': value}
    return results

  @staticmethod
  def user() -> str:
    return _os.getenv('USER') or _getpass.getuser()

  @staticmethod
  def is_admin() -> bool:
    try: return _ctypes.windll.shell32.IsUserAnAdmin() in [1, True]
    except AttributeError: return False
  
  @staticmethod
  def pause_exit(pause:bool = False, exit:bool = False, last_msg:str = '', exit_code:int = 0, reset_ansi:bool = False) -> None:
    print(last_msg, end='', flush=True)
    if reset_ansi: FormatCodes.print('[_]', end='')
    if pause: _keyboard.read_event()
    if exit: _sys.exit(exit_code)

  @staticmethod
  def cls() -> None:
    """Will clear the console in addition to completely resetting the ANSI formats."""
    if _shutil.which('cls'): _os.system('cls')
    elif _shutil.which('clear'): _os.system('clear')
    print('\033[0m', end='', flush=True)

  @staticmethod
  def log(title:str, msg:str, start:str = '', end:str = '\n', title_bg_color:hexa|rgba = None, default_color:hexa|rgba = None) -> None:
    title_color = '_color' if not title_bg_color else Color.text_color_for_on_bg(title_bg_color)
    if title: FormatCodes.print(f'{start}  [bold][{title_color}]{f"[BG:{title_bg_color}]" if title_bg_color else ""} {title.upper()}: [_]\t{f"[{default_color}]" if default_color else ""}{str(msg)}[_]', default_color, end=end)
    else: FormatCodes.print(f'{start}  {f"[{default_color}]" if default_color else ""}{str(msg)}[_]', default_color, end=end)

  @staticmethod
  def debug(msg:str = 'Point in program reached.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['yellow'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
    Cmd.log('DEBUG', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def info(msg:str = 'Program running.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['blue'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
    Cmd.log('INFO', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def done(msg:str = 'Program finished.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['teal'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
    Cmd.log('DONE', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def warn(msg:str = 'Important message.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['orange'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
    Cmd.log('WARN', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def fail(msg:str = 'Program error.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['red'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = True, reset_ansi=True) -> None:
    Cmd.log('FAIL', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit, reset_ansi=reset_ansi)

  @staticmethod
  def exit(msg:str = 'Program ended.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['magenta'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = True, reset_ansi=True) -> None:
    Cmd.log('EXIT', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit, reset_ansi=reset_ansi)

  @staticmethod
  def confirm(msg:str = 'Are you sure? [_|dim]((Y/n):  )', start = '\n', end = '\n', default_color:hexa|rgba = DEFAULT.color['cyan'], default_is_yes:bool = True) -> None:
    confirmed = input(FormatCodes.to_ansi(f'{start}  {str(msg)}', default_color)).strip().lower() in (('', 'y', 'yes') if default_is_yes else ('y', 'yes'))
    if end: Cmd.log('', '') if end == '\n' else Cmd.log('', end[1:]) if end.startswith('\n') else Cmd.log('', end)
    return confirmed
