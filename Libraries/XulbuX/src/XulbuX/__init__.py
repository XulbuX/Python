"""
 >>> import XulbuX as xx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  *  CUSTOM TYPES:
      *  rgb(int,int,int,float)
      *  hsl(int,int,int,float)
      *  hexa(str)
  *  DIRECTORY OPERATIONS     xx.Dir
  *  FILE OPERATIONS          xx.File
  *  JSON FILE OPERATIONS     xx.Json
  *  SYSTEM ACTIONS           xx.System
  *  MANAGE ENVIRONMENT VARS  xx.EnvVars
  *  CMD LOG AND ACTIONS      xx.Cmd
  *  PRETTY PRINTING          xx.FormatCodes
  *  COLOR OPERATIONS         xx.Color
  *  DATA OPERATIONS          xx.Data
  *  STR OPERATIONS           xx.String
  *  CODE STRING OPERATIONS   xx.Code
  *  REGEX PATTERN TEMPLATES  xx.Regex
"""

__version__ = '1.4.3'

from .XulbuX import rgba, hsla, hexa, Path, File, Json, System, EnvVars, Cmd, FormatCodes, Color, Data, String, Code, Regex