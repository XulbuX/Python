try: from .xx_format_codes import *
except: from xx_format_codes import *
try: from .xx_cmd import *
except: from xx_cmd import *

import os as _os



def get_version(file:str = '__init__.py', var:str = '__version__') -> str:
  try:
    from . import var
    return var
  except ImportError:
    init_path = _os.path.join(_os.path.dirname(__file__), file)
    if _os.path.isfile(init_path):
      with open(init_path, encoding='utf-8') as f:
        for line in f:
          if line.startswith(var): return line.split('=')[-1].strip().strip("'\"")
    return 'unknown'

def help():
  FormatCodes.print(
  rf'''  [_|b|#7075FF]               __  __              
  [b|#7075FF]  _  __ __  __/ / / /_  __  ___  __
  [b|#7075FF] | |/ // / / / / / __ \/ / / | |/ /
  [b|#7075FF] > , </ /_/ / /_/ /_/ / /_/ /> , < 
  [b|#7075FF]/_/|_|\____/\__/\____/\____//_/|_|  [*|BG:#7B7C8F|#000] v[b]{get_version()} [*]

  [i|#FF806A]A TON OF COOL FUNCTIONS, YOU NEED![*]

  [b|#75A2FF]Usage:[*]
    [#666]# GENERAL LIBRARY[*]
    [#FF606A]import [#77EFEF]XulbuX [#FF606A]as [#77EFEF]xx[*]
    [#666]# CUSTOM TYPES[*]
    [#FF606A]from [#77EFEF]XulbuX [#FF606A]import [#77EFEF]rgba[#666], [#77EFEF]hsla[#666], [#77EFEF]hexa[*]

  [b|#75A2FF]Includes:[*]
    [dim](•) CUSTOM TYPES:
       [dim](•) [#AA90FF]rgba[#666]/([i|#60AAFF]int[_|#666],[i|#60AAFF]int[_|#666],[i|#60AAFF]int[_|#666],[i|#60AAFF]float[_|#666])[*]
       [dim](•) [#AA90FF]hsla[#666]/([i|#60AAFF]int[_|#666],[i|#60AAFF]int[_|#666],[i|#60AAFF]int[_|#666],[i|#60AAFF]float[_|#666])[*]
       [dim](•) [#AA90FF]hexa[#666]/([i|#60AAFF]str[_|#666])[*]
    [dim](•) PATH OPERATIONS          [#77EFEF]xx[#666].[#AA90FF]Path[*]
    [dim](•) FILE OPERATIONS          [#77EFEF]xx[#666].[#AA90FF]File[*]
    [dim](•) JSON FILE OPERATIONS     [#77EFEF]xx[#666].[#AA90FF]Json[*]
    [dim](•) SYSTEM ACTIONS           [#77EFEF]xx[#666].[#AA90FF]System[*]
    [dim](•) MANAGE ENVIRONMENT VARS  [#77EFEF]xx[#666].[#AA90FF]Env_vars[*]
    [dim](•) CMD LOG AND ACTIONS      [#77EFEF]xx[#666].[#AA90FF]Cmd[*]
    [dim](•) PRETTY PRINTING          [#77EFEF]xx[#666].[#AA90FF]FormatCodes[*]
    [dim](•) COLOR OPERATIONS         [#77EFEF]xx[#666].[#AA90FF]Color[*]
    [dim](•) DATA OPERATIONS          [#77EFEF]xx[#666].[#AA90FF]Data[*]
    [dim](•) STR OPERATIONS           [#77EFEF]xx[#666].[#AA90FF]String[*]
    [dim](•) CODE STRING OPERATIONS   [#77EFEF]xx[#666].[#AA90FF]Code[*]
    [dim](•) REGEX PATTERN TEMPLATES  [#77EFEF]xx[#666].[#AA90FF]Regex[*]
  [_]
  [dim](Press any key to exit...)
  ''', '#809FFF')
  Cmd.pause_exit(pause=True)



if __name__ == '__main__':
  help()
