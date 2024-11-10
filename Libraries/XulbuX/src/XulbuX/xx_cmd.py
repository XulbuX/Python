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
- `Cmd.confirm()`
- `Cmd.input()`
- `Cmd.pwd_input()`\n
----------------------------------------------------------------------------------------------------------
You can also use special formatting codes directly inside the log message to change their appearance.<br>
For more detailed information about formatting codes, see the the `xx_format_codes` description.
"""


from ._consts_ import DEFAULT
from .xx_format_codes import *
from .xx_string import *
from .xx_color import *

import keyboard as _keyboard
import getpass as _getpass
import ctypes as _ctypes
import shutil as _shutil
import msvcrt as _msvcrt
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
                    if arg_index + 1 < len(args) and not args[arg_index + 1].startswith('-'):
                        value = String.to_type(args[arg_index + 1])
                    break
            results[arg_key] = {'exists': exists, 'value': value}
        return results

    def w() -> int: return getattr(_shutil.get_terminal_size(), 'columns', 80)
    def h() -> int: return getattr(_shutil.get_terminal_size(), 'lines', 24)
    def wh() -> tuple[int,int]: return Cmd.w(), Cmd.h()
    def user() -> str: return _os.getenv('USER') or _os.getenv('USERNAME') or _getpass.getuser()

    @staticmethod
    def is_admin() -> bool:
        try:
            if _os.name == 'nt':
                return _ctypes.windll.shell32.IsUserAnAdmin() != 0
            elif _os.name == 'posix':
                return _os.geteuid() == 0
            else:
                return False
        except:
            return False

    @staticmethod
    def pause_exit(pause:bool = False, exit:bool = False, last_msg:str = '', exit_code:int = 0, reset_ansi:bool = False) -> None:
        """Will print the `last_msg` and then pause the program if `pause` is set<br>
        to `True` and after the pause, exit the program if `exit` is set to `True`."""
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
        """Will print a formatted log message:<br>
        `title` -⠀the title of the log message (e.g. `DEBUG`, `WARN`, `FAIL`, etc.)<br>
        `msg` -⠀the log message<br>
        `start` -⠀something to print before the log is printed<br>
        `end` -⠀something to print after the log is printed (e.g. `\\n\\n`)<br>
        `title_bg_color` -⠀the background color of the `title`<br>
        `default_color` -⠀the default text color of the `msg`\n
        --------------------------------------------------------------------------------
        The log message supports special formatting codes. For more detailed<br>
        information about formatting codes, see `xx_format_codes` class description."""
        title_color = '_color' if not title_bg_color else Color.text_color_for_on_bg(title_bg_color)
        if title: FormatCodes.print(f'{start}  [bold][{title_color}]{f"[BG:{title_bg_color}]" if title_bg_color else ""} {title.upper()}: [_]\t{f"[{default_color}]" if default_color else ""}{str(msg)}[_]', default_color, end=end)
        else: FormatCodes.print(f'{start}  {f"[{default_color}]" if default_color else ""}{str(msg)}[_]', default_color, end=end)

    @staticmethod
    def debug(msg:str = 'Point in program reached.', active:bool = True, start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['yellow'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
        """A preset for `log()`: `DEBUG` log message with the options to pause<br>
        at the message and exit the program after the message was printed."""
        if active:
            Cmd.log('DEBUG', msg, start, end, title_bg_color, default_color)
            Cmd.pause_exit(pause, exit)

    @staticmethod
    def info(msg:str = 'Program running.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['blue'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
        """A preset for `log()`: `INFO` log message with the options to pause<br>
        at the message and exit the program after the message was printed."""
        Cmd.log('INFO', msg, start, end, title_bg_color, default_color)
        Cmd.pause_exit(pause, exit)

    @staticmethod
    def done(msg:str = 'Program finished.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['teal'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
        """A preset for `log()`: `DONE` log message with the options to pause<br>
        at the message and exit the program after the message was printed."""
        Cmd.log('DONE', msg, start, end, title_bg_color, default_color)
        Cmd.pause_exit(pause, exit)

    @staticmethod
    def warn(msg:str = 'Important message.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['orange'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = False) -> None:
        """A preset for `log()`: `WARN` log message with the options to pause<br>
        at the message and exit the program after the message was printed."""
        Cmd.log('WARN', msg, start, end, title_bg_color, default_color)
        Cmd.pause_exit(pause, exit)

    @staticmethod
    def fail(msg:str = 'Program error.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['red'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = True, reset_ansi=True) -> None:
        """A preset for `log()`: `FAIL` log message with the options to pause<br>
        at the message and exit the program after the message was printed."""
        Cmd.log('FAIL', msg, start, end, title_bg_color, default_color)
        Cmd.pause_exit(pause, exit, reset_ansi=reset_ansi)

    @staticmethod
    def exit(msg:str = 'Program ended.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = DEFAULT.color['magenta'], default_color:hexa|rgba = DEFAULT.text_color, pause:bool = False, exit:bool = True, reset_ansi=True) -> None:
        """A preset for `log()`: `EXIT` log message with the options to pause<br>
        at the message and exit the program after the message was printed."""
        Cmd.log('EXIT', msg, start, end, title_bg_color, default_color)
        Cmd.pause_exit(pause, exit, reset_ansi=reset_ansi)

    @staticmethod
    def confirm(msg:str = 'Do you want to continue?', start = '\n', end = '\n', default_color:hexa|rgba = DEFAULT.color['cyan'], default_is_yes:bool = True) -> None:
        """Ask a yes/no question.\n
        -----------------------------------------------------------------------------------
        The question can be formatted with special formatting codes. For more detailed<br>
        information about formatting codes, see the `xx_format_codes` description."""
        confirmed = input(FormatCodes.to_ansi(f'{start}  {str(msg)} [_|dim](({"Y" if default_is_yes else "y"}/{"n" if default_is_yes else "N"}):  )', default_color)).strip().lower() in (('', 'y', 'yes') if default_is_yes else ('y', 'yes'))
        if end: Cmd.log('', '') if end == '\n' else Cmd.log('', end[1:]) if end.startswith('\n') else Cmd.log('', end)
        return confirmed

    @staticmethod
    def input(prompt:object = '', allowed_chars:str = '0123456789', min_length:int = None, max_length:int = None, mask_char:str = None) -> str:
        """Acts like a standard Python `input()` with the advantage, that you can specify:
        - what text characters the user is allowed to type and
        - the minimum and/or maximum length of the users input
        - optional mask character (hide user input, e.g. for passwords)\n
        -----------------------------------------------------------------------------------
        The input can be formatted with special formatting codes. For more detailed<br>
        information about formatting codes, see the `xx_format_codes` description."""
        print(FormatCodes.to_ansi(prompt), end='', flush=True)
        result = ''
        while True:
            char = _msvcrt.getch().decode('utf-8', errors='ignore')
            if char == '\r':
                if min_length is not None and len(result) < min_length:
                    continue
                print()
                return result
            elif char == '\b':
                if result:
                    result = result[:-1]
                    _sys.stdout.write('\b \b')
                    _sys.stdout.flush()
            elif (not allowed_chars or char in allowed_chars) and (max_length is None or len(result) < max_length):
                result += char
                _sys.stdout.write(char if mask_char is None else (mask_char if char not in (None, '') else ''))
                _sys.stdout.flush()

    @staticmethod
    def pwd_input(prompt:object = 'Password: ', allowed_chars:str = DEFAULT.char_map['ascii'], min_length:int = None, max_length:int = None) -> str:
        """Password input that masks the entered characters with asterisks."""
        return Cmd.input(prompt, allowed_chars, min_length, max_length, mask_char='*')
