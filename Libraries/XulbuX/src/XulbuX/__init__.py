"""
 >>> import XulbuX as xx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • CUSTOM TYPES:
     • rgba(int,int,int,float)
     • hsla(int,int,int,float)
     • hexa(str)
  • PATH OPERATIONS          xx.Path
  • FILE OPERATIONS          xx.File
  • JSON FILE OPERATIONS     xx.Json
  • SYSTEM ACTIONS           xx.System
  • MANAGE ENVIRONMENT VARS  xx.EnvVars
  • CMD LOG AND ACTIONS      xx.Cmd
  • PRETTY PRINTING          xx.FormatCodes
  • COLOR OPERATIONS         xx.Color
  • DATA OPERATIONS          xx.Data
  • STR OPERATIONS           xx.String
  • CODE STRING OPERATIONS   xx.Code
  • REGEX PATTERN TEMPLATES  xx.Regex
"""

__version__ = '1.5.0'
__author__ = 'XulbuX'
__email__ = 'xulbux.real@gmail.com'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2024 XulbuX'
__url__ = 'https://github.com/XulbuX-dev/Python/tree/main/Libraries/XulbuX'
__description__ = 'A library which includes a lot of really helpful functions.'
__all__ = [
  'Cmd', 'Code', 'Color', 'Data', 'EnvVars', 'File', 'FormatCodes',
  'Json', 'Path', 'Regex', 'String', 'System'
]

from .Cmd import *
from .Code import *
from .Color import *
from .Data import *
from .EnvVars import *
from .File import *
from .FormatCodes import *
from .Json import *
from .Path import *
from .Regex import *
from .String import *
from .System import *
