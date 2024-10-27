"""
 >>> import XulbuX as xx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  *  CUSTOM TYPES:
      *  rgb(int,int,int,float)
      *  hsl(int,int,int,float)
      *  hexa(str)
  *  PATH OPERATIONS          xx.Path
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

try: from .System import *
except: from System import *
try: from .consts import *
except: from consts import *

System.check_libs(['keyboard', 'regex'], install_missing=True)

import subprocess as _subprocess
import platform as _platform
import tempfile as _tempfile
import keyboard as _keyboard
import difflib as _difflib
import getpass as _getpass
import ctypes as _ctypes
import shutil as _shutil
import regex as _regex
import math as _math
import json as _json
import time as _time
import sys as _sys
import os as _os
import re as _re



################################################## LIBRARY INITIALIZING ##################################################
def get_version(var:str = '__version__') -> str:
  try:
    from . import var
    return var
  except ImportError:
    init_path = _os.path.join(_os.path.dirname(__file__), '__init__.py')
    if _os.path.isfile(init_path):
      with open(init_path, encoding='utf-8') as f:
        for line in f:
          if line.startswith(var): return line.split('=')[-1].strip().strip("'\"")
    return 'unknown'

__version__ = get_version()



################################################## CUSTOM TYPES ##################################################
class rgba:
  """An RGB/RGBA color: is a tuple of 3 integers, representing the red (`0`-`255`), green (`0`-`255`), and blue (`0`-`255`).<br>
  Also includes an optional 4th param, which is a float, that represents the alpha channel (`0.0`-`1.0`).\n
  -------------------------------------------------------------------------------------------------------------------------------
  Includes methods:
  - `to_hsla()` to convert to HSL color
  - `to_hexa()` to convert to HEX color
  - `has_alpha()` to check if the color has an alpha channel
  - `lighten(amount)` to create a lighter version of the color
  - `darken(amount)` to create a darker version of the color
  - `saturate(amount)` to increase color saturation
  - `desaturate(amount)` to decrease color saturation
  - `rotate(degrees)` to rotate the hue by degrees
  - `invert()` to get the inverse color
  - `grayscale()` to convert to grayscale
  - `blend(other, ratio)` to blend with another color
  - `is_dark()` to check if the color is considered dark
  - `is_light()` to check if the color is considered light
  - `is_grayscale()` to check if the color is grayscale
  - `is_opaque()` to check if the color has no transparency
  - `with_alpha(alpha)` to create a new color with different alpha
  - `complementary()` to get the complementary color"""
  def __init__(self, r:int, g:int, b:int, a:float = None):
    if any(isinstance(x, rgba) for x in (r, g, b)): raise ValueError('Color is already a rgba() color')
    if not all(isinstance(x, int) and 0 <= x <= 255 for x in (r, g, b)): raise ValueError('RGB color must consist of 3 integers in [0, 255]')
    if not a is None and not (isinstance(a, (int, float)) and 0 <= a <= 1): raise ValueError('Alpha channel must be a float/int in [0.0, 1.0]')
    self.r, self.g, self.b, self.a = r, g, b, (1.0 if a > 1.0 else float(a)) if a else None
    self.h, self.s, self.l = self._rgb_to_hsl(r, g, b)
  def __len__(self): return 4 if self.a else 3
  def __iter__(self): return iter((self.r, self.g, self.b) + ((self.a,) if self.a else ()))
  def __getitem__(self, index): return ((self.r, self.g, self.b) + ((self.a,) if self.a else ()))[index]
  def __repr__(self): return f'rgba({self.r}, {self.g}, {self.b}{f", {self.a}" if self.a else ""})'
  def __str__(self): return f'({self.r}, {self.g}, {self.b}{f", {self.a}" if self.a else ""})'
  def __eq__(self, other):
    if not isinstance(other, rgba): return False
    return (self.r, self.g, self.b) == (other.r, other.g, other.b) and self.a == other.a
  def list(self) -> list:
    """Returns the color components as a list [r, g, b] or [r, g, b, a] if alpha is present"""
    return [self.r, self.g, self.b] + ([self.a] if self.a else [])
  def tuple(self) -> tuple:
    """Returns the color components as a tuple (r, g, b) or (r, g, b, a) if alpha is present"""
    return tuple(self.list())
  def dict(self) -> dict:
    """Returns the color components as a dictionary with keys 'r', 'g', 'b' and optionally 'a'"""
    return dict(r=self.r, g=self.g, b=self.b, a=self.a) if self.a else dict(r=self.r, g=self.g, b=self.b)
  def values(self) -> tuple:
    """Returns the color components as single values r, g, b, a"""
    return self.r, self.g, self.b, self.a
  def to_hsla(self) -> 'hsla':
    """Converts the color to HSLA format"""
    return hsla(self.h, self.s, self.l, self.a)
  def to_hexa(self) -> 'hexa':
    """Converts the color to hexadecimal format, including alpha if present"""
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def has_alpha(self) -> bool:
    """Returns True if the color has an alpha channel"""
    return self.a != None
  def lighten(self, amount:float) -> 'rgba':
    """Creates a lighter version of the color by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_hsla().lighten(amount).to_rgba().values()
    return rgba(self.r, self.g, self.b, self.a)
  def darken(self, amount:float) -> 'rgba':
    """Creates a darker version of the color by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_hsla().darken(amount).to_rgba().values()
    return rgba(self.r, self.g, self.b, self.a)
  def saturate(self, amount:float) -> 'rgba':
    """Increases the saturation by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_hsla().saturate(amount).to_rgba().values()
    return rgba(self.r, self.g, self.b, self.a)
  def desaturate(self, amount:float) -> 'rgba':
    """Decreases the saturation by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_hsla().desaturate(amount).to_rgba().values()
    return rgba(self.r, self.g, self.b, self.a)
  def rotate(self, degrees:int) -> 'rgba':
    """Rotates the hue by the specified number of degrees"""
    self.r, self.g, self.b, self.a = self.to_hsla().rotate(degrees).to_rgba().values()
    return rgba(self.r, self.g, self.b, self.a)
  def invert(self) -> 'rgba':
    """Returns the inverse color"""
    self.r, self.g, self.b = 255 - self.r, 255 - self.g, 255 - self.b
    return rgba(self.r, self.g, self.b, self.a)
  def grayscale(self) -> 'rgba':
    """Converts the color to grayscale using luminance formula"""
    gray = int(0.299 * self.r + 0.587 * self.g + 0.114 * self.b)
    self.r = self.g = self.b = gray
    return rgba(self.r, self.g, self.b, self.a)
  def blend(self, other:'rgba', ratio:float = 0.5, additive_alpha:bool = False) -> 'rgba':
    """Blends the current color with another color using the specified ratio (`0.0`-`1.0`):<br>
    If `ratio` is `0.0` it means 100% of the current color and 0% of the `other` color (1:0 mixture)<br>
    If `ratio` is `0.5` it means 50% of both colors (1:1 mixture)<br>
    If `ratio` is `1.0` it means 0% of the current color and 100% of the `other` color (0:1 mixture)"""
    if not (isinstance(ratio, (int, float)) and 0 <= ratio <= 1): raise ValueError("'ratio' must be a float/int in [0.0, 1.0]")
    if not isinstance(other, rgba):
      if Color.is_valid_rgba(other): other = rgba(*other)
      else: raise TypeError("'other' must be a valid RGBA color")
    alpha = (other[3] if other[3] is not None else 1) if len(other) > 3 else 1
    ratio *= 2
    self.r = self._clamp(int((self.r * (2 - ratio)) + (other.r * ratio)), 0, 255)
    self.g = self._clamp(int((self.g * (2 - ratio)) + (other.g * ratio)), 0, 255)
    self.b = self._clamp(int((self.b * (2 - ratio)) + (other.b * ratio)), 0, 255)
    if additive_alpha: self.a = self._clamp((self.a * (2 - ratio)) + (alpha * ratio), 0, 1)
    else: self.a = self._clamp((self.a * (1 - (ratio / 2))) + (alpha * (ratio / 2)), 0, 1)
    return rgba(self.r, self.g, self.b, self.a)
  def is_dark(self) -> bool:
    """Returns `True` if the color is considered dark (luminance < 128)"""
    return (0.299 * self.r + 0.587 * self.g + 0.114 * self.b) < 128
  def is_light(self) -> bool:
    """Returns `True` if the color is considered light (luminance >= 128)"""
    return not self.is_dark()
  def is_grayscale(self) -> bool:
    """Returns `True` if the color is grayscale"""
    return self.r == self.g == self.b
  def is_opaque(self) -> bool:
    """Returns `True` if the color has no transparency"""
    return self.a == 1 or self.a is None
  def with_alpha(self, alpha:float) -> 'rgba':
    """Returns a new color with the specified alpha value"""
    if not (isinstance(alpha, (int, float)) and 0 <= alpha <= 1): raise ValueError("'alpha' must be a float/int in [0.0, 1.0]")
    return rgba(self.r, self.g, self.b, alpha)
  def complementary(self) -> 'rgba':
    """Returns the complementary color (180 degrees on the color wheel)"""
    return self.to_hsla().complementary().to_rgba()
  def _clamp(self, value:int|float, min_val:int|float = 0, max_val:int|float = 255) -> int|float:
    return max(min_val, min(max_val, value))
  def _rgb_to_hsl(self, r:int, g:int, b:int) -> tuple:
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_c, min_c = max(r, g, b), min(r, g, b)
    l = (max_c + min_c) / 2
    if max_c == min_c: h = s = 0
    else:
      delta = max_c - min_c
      s = delta / (1 - abs(2 * l - 1))
      if max_c == r: h = ((g - b) / delta) % 6
      elif max_c == g: h = ((b - r) / delta) + 2
      else: h = ((r - g) / delta) + 4
      h /= 6
    return int(round(h * 360)), int(round(s * 100)), int(round(l * 100))

class hsla:
  """A HSL/HSLA color: is a tuple of 3 integers, representing hue (`0`-`360`), saturation (`0`-`100`), and lightness (`0`-`100`).<br>
  Also includes an optional 4th param, which is a float, that represents the alpha channel (`0.0`-`1.0`).\n
  ------------------------------------------------------------------------------------------------------------------------------------
  Includes methods:
  - `to_rgba()` to convert to RGB color
  - `to_hexa()` to convert to HEX color
  - `has_alpha()` to check if the color has an alpha channel
  - `lighten(amount)` to create a lighter version of the color
  - `darken(amount)` to create a darker version of the color
  - `saturate(amount)` to increase color saturation
  - `desaturate(amount)` to decrease color saturation
  - `rotate(degrees)` to rotate the hue by degrees
  - `invert()` to get the inverse color
  - `grayscale()` to convert to grayscale
  - `blend(other, ratio)` to blend with another color
  - `is_dark()` to check if the color is considered dark
  - `is_light()` to check if the color is considered light
  - `is_grayscale()` to check if the color is grayscale
  - `is_opaque()` to check if the color has no transparency
  - `with_alpha(alpha)` to create a new color with different alpha
  - `complementary()` to get the complementary color"""
  def __init__(self, h:int, s:int, l:int, a:float = None):
    if any(isinstance(x, hsla) for x in (h, s, l)): raise ValueError('Color is already a hsla() color')
    if not (isinstance(h, int) and (0 <= h <= 360) and all(isinstance(x, int) and (0 <= x <= 100) for x in (s, l))): raise ValueError('HSL color must have H in [0, 360] and S L in [0, 100]')
    if not a is None and (not isinstance(a, (int, float)) or not 0 <= a <= 1): raise ValueError('Alpha channel must be a float/int in [0.0, 1.0]')
    self.h, self.s, self.l, self.a = h, s, l, (1.0 if a > 1.0 else float(a)) if a else None
    self.r, self.g, self.b = self._hsl_to_rgb(h, s, l)
  def __len__(self): return 4 if self.a else 3
  def __iter__(self): return iter((self.h, self.s, self.l) + ((self.a,) if self.a else ()))
  def __getitem__(self, index): return ((self.h, self.s, self.l) + ((self.a,) if self.a else ()))[index]
  def __repr__(self): return f'hsla({self.h}, {self.s}, {self.l}{f", {self.a}" if self.a else ""})'
  def __str__(self): return f'({self.h}, {self.s}, {self.l}{f", {self.a}" if self.a else ""})'
  def __eq__(self, other):
    if not isinstance(other, hsla): return False
    return (self.h, self.s, self.l) == (other.h, other.s, other.l) and self.a == other.a
  def list(self) -> list:
    """Returns the color components as a list [h, s, l] or [h, s, l, a] if alpha is present"""
    return [self.h, self.s, self.l] + ([self.a] if self.a else [])
  def tuple(self) -> tuple:
    """Returns the color components as a tuple (h, s, l) or (h, s, l, a) if alpha is present"""
    return tuple(self.list())
  def dict(self) -> dict:
    """Returns the color components as a dictionary with keys 'h', 's', 'l' and optionally 'a'"""
    return dict(h=self.h, s=self.s, l=self.l, a=self.a) if self.a else dict(h=self.h, s=self.s, l=self.l)
  def values(self) -> tuple:
    """Returns the color components as single values h, s, l, a"""
    return self.h, self.s, self.l, self.a
  def to_rgba(self) -> 'rgba':
    """Converts the color to RGBA format"""
    return rgba(self.r, self.g, self.b, self.a)
  def to_hexa(self) -> 'hexa':
    """Converts the color to hexadecimal format, including alpha if present"""
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def has_alpha(self) -> bool:
    """Returns True if the color has an alpha channel"""
    return self.a != None
  def lighten(self, amount:float) -> 'hsla':
    """Creates a lighter version of the color by the specified amount (`0.0`-`1.0`)"""
    if not (isinstance(amount, (int, float)) and 0 <= amount <= 1): raise ValueError("'amount' must be a float/int in [0.0, 1.0]")
    self.l = int(min(100, self.l + (100 - self.l) * amount))
    return hsla(self.h, self.s, self.l, self.a)
  def darken(self, amount:float) -> 'hsla':
    """Creates a darker version of the color by the specified amount (`0.0`-`1.0`)"""
    if not (isinstance(amount, (int, float)) and 0 <= amount <= 1): raise ValueError("'amount' must be a float/int in [0.0, 1.0]")
    self.l = int(max(0, self.l * (1 - amount)))
    return hsla(self.h, self.s, self.l, self.a)
  def saturate(self, amount:float) -> 'hsla':
    """Increases the saturation by the specified amount (`0.0`-`1.0`)"""
    if not (isinstance(amount, (int, float)) and 0 <= amount <= 1): raise ValueError("'amount' must be a float/int in [0.0, 1.0]")
    self.s = int(min(100, self.s + (100 - self.s) * amount))
    return hsla(self.h, self.s, self.l, self.a)
  def desaturate(self, amount:float) -> 'hsla':
    """Decreases the saturation by the specified amount (`0.0`-`1.0`)"""
    if not (isinstance(amount, (int, float)) and 0 <= amount <= 1): raise ValueError("'amount' must be a float/int in [0.0, 1.0]")
    self.s = int(max(0, self.s * (1 - amount)))
    return hsla(self.h, self.s, self.l, self.a)
  def rotate(self, degrees:int) -> 'hsla':
    """Rotates the hue by the specified number of degrees"""
    self.h = (self.h + degrees) % 360
    return hsla(self.h, self.s, self.l, self.a)
  def invert(self) -> 'hsla':
    """Inverts the color by rotating hue by 180 degrees and inverting lightness"""
    self.h = (self.h + 180) % 360
    self.l = 100 - self.l
    return hsla(self.h, self.s, self.l, self.a)
  def grayscale(self) -> 'hsla':
    """Converts the color to grayscale by removing saturation"""
    self.s = 0
    return hsla(self.h, self.s, self.l, self.a)
  def blend(self, other:'hsla', ratio:float = 0.5, additive_alpha:bool = False) -> 'rgba':
    """Blends the current color with another color using the specified ratio (`0.0`-`1.0`):<br>
    If `ratio` is `0.0` it means 100% of the current color and 0% of the `other` color (1:0 mixture)<br>
    If `ratio` is `0.5` it means 50% of both colors (1:1 mixture)<br>
    If `ratio` is `1.0` it means 0% of the current color and 100% of the `other` color (0:1 mixture)"""
    return self.to_rgba().blend(Color.to_rgba(other), ratio, additive_alpha).to_hsla()
  def is_dark(self) -> bool:
    """Returns `True` if the color is considered dark (`lightness < 50`)"""
    return self.l < 50
  def is_light(self) -> bool:
    """Returns `True` if the color is considered light (`lightness >= 50`)"""
    return not self.is_dark()
  def is_grayscale(self) -> bool:
    """Returns `True` if the color is considered grayscale"""
    return self.s == 0
  def is_opaque(self) -> bool:
    """Returns `True` if the color has no transparency"""
    return self.a == 1 or self.a is None
  def with_alpha(self, alpha:float) -> 'hsla':
    """Returns a new color with the specified alpha value"""
    if not (isinstance(alpha, (int, float)) and 0 <= alpha <= 1): raise ValueError("'alpha' must be a float/int in [0.0, 1.0]")
    return hsla(self.h, self.s, self.l, alpha)
  def complementary(self) -> 'hsla':
    """Returns the complementary color (180 degrees on the color wheel)"""
    return hsla((self.h + 180) % 360, self.s, self.l, self.a)
  def _hsl_to_rgb(self, h:int, s:int, l:int) -> tuple:
    h, s, l = h / 360, s / 100, l / 100
    if s == 0: r = g = b = int(l * 255)
    else:
      def hue_to_rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
      q = l * (1 + s) if l < 0.5 else l + s - l * s
      p = 2 * l - q
      r = int(round(hue_to_rgb(p, q, h + 1/3) * 255))
      g = int(round(hue_to_rgb(p, q, h) * 255))
      b = int(round(hue_to_rgb(p, q, h - 1/3) * 255))
    return r, g, b

class hexa:
  """A HEX color: is a string representing a hexadecimal color code with optional alpha channel.\n
  -------------------------------------------------------------------------------------------------
  Supports formats: #RGB, #RGBA, #RRGGBB, #RRGGBBAA (with or without leading #)<br>
  Includes methods:
  - `to_rgba()` to convert to RGB color
  - `to_hsla()` to convert to HSL color
  - `has_alpha()` to check if the color has an alpha channel
  - `lighten(amount)` to create a lighter version of the color
  - `darken(amount)` to create a darker version of the color
  - `saturate(amount)` to increase color saturation
  - `desaturate(amount)` to decrease color saturation
  - `rotate(degrees)` to rotate the hue by degrees
  - `invert()` to get the inverse color
  - `grayscale()` to convert to grayscale
  - `blend(other, ratio)` to blend with another color
  - `is_dark()` to check if the color is considered dark
  - `is_light()` to check if the color is considered light
  - `is_grayscale()` to check if the color is grayscale
  - `is_opaque()` to check if the color has no transparency
  - `with_alpha(alpha)` to create a new color with different alpha
  - `complementary()` to get the complementary color"""
  def __init__(self, color:str):
    if isinstance(color, hexa): raise ValueError('Color is already a hexa() color')
    if not isinstance(color, str): raise TypeError('Color must be a string')
    if not color.startswith('#'): color = f'#{color}'
    color = color.upper()
    if len(color) == 4: self.r, self.g, self.b, self.a = int(color[1] * 2, 16), int(color[2] * 2, 16), int(color[3] * 2, 16), None                             #RGB
    elif len(color) == 5: self.r, self.g, self.b, self.a = int(color[1] * 2, 16), int(color[2] * 2, 16), int(color[3] * 2, 16), int(color[4] * 2, 16) / 255.0  #RGBA
    elif len(color) == 7: self.r, self.g, self.b, self.a = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), None                                 #RRGGBB
    elif len(color) == 9: self.r, self.g, self.b, self.a = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), int(color[7:9], 16) / 255.0          #RRGGBBAA
    else: raise ValueError('Hex color must be in format #RGB, #RGBA, #RRGGBB, or #RRGGBBAA')
  def __len__(self): return 4 if self.a else 3
  def __iter__(self): return iter((f'{self.r:02X}', f'{self.g:02X}', f'{self.b:02X}') + ((f'{int(self.a * 255):02X}',) if self.a else ()))
  def __getitem__(self, index): return ((f'{self.r:02X}', f'{self.g:02X}', f'{self.b:02X}') + ((f'{int(self.a * 255):02X}',) if self.a else ()))[index]
  def __repr__(self): return f'hexa(#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""})'
  def __str__(self): return f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}'
  def __eq__(self, other):
    if not isinstance(other, hexa): return False
    return (self.r, self.g, self.b) == (other.r, other.g, other.b) and self.a == other.a
  def list(self) -> list:
    """Returns the color components as a list of hex strings [R, G, B] or [R, G, B, A] if alpha is present"""
    return [f'{self.r:02X}', f'{self.g:02X}', f'{self.b:02X}'] + ([f'{int(self.a * 255):02X}'] if self.a else [])
  def tuple(self) -> tuple:
    """Returns the color components as a tuple of hex strings (R, G, B) or (R, G, B, A) if alpha is present"""
    return tuple(self.list())
  def dict(self) -> dict:
    """Returns the color components as a dictionary with hex string values for keys 'r', 'g', 'b' and optionally 'a'"""
    return dict(r=f'{self.r:02X}', g=f'{self.g:02X}', b=f'{self.b:02X}', a=f'{int(self.a * 255):02X}') if self.a else dict(r=f'{self.r:02X}', g=f'{self.g:02X}', b=f'{self.b:02X}')
  def values(self) -> tuple:
    """Returns the color components as single values r, g, b, a"""
    return self.r, self.g, self.b, self.a
  def to_rgba(self, round_alpha:bool = True) -> 'rgba':
    """Converts the color to RGBA format"""
    return rgba(self.r, self.g, self.b, (round(self.a, 2) if round_alpha else self.a) if self.a else None)
  def to_hsla(self, round_alpha:bool = True) -> 'hsla':
    """Converts the color to HSLA format"""
    return self.to_rgba(round_alpha).to_hsla()
  def has_alpha(self) -> bool:
    """Returns True if the color has an alpha channel"""
    return self.a is not None
  def lighten(self, amount:float) -> 'hexa':
    """Creates a lighter version of the color by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_rgba(False).lighten(amount).values()
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def darken(self, amount:float) -> 'hexa':
    """Creates a darker version of the color by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_rgba(False).darken(amount).values()
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def saturate(self, amount:float) -> 'hexa':
    """Increases the saturation by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_rgba(False).saturate(amount).values()
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def desaturate(self, amount:float) -> 'hexa':
    """Decreases the saturation by the specified amount (`0.0`-`1.0`)"""
    self.r, self.g, self.b, self.a = self.to_rgba(False).desaturate(amount).values()
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def rotate(self, degrees:int) -> 'hexa':
    """Rotates the hue by the specified number of degrees"""
    self.r, self.g, self.b, self.a = self.to_rgba(False).rotate(degrees).values()
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def invert(self) -> 'hexa':
    """Returns the inverse color by rotating hue by 180 degrees and inverting lightness"""
    self.r, self.g, self.b, self.a = self.to_rgba(False).invert().values()
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def grayscale(self) -> 'hexa':
    """Converts the color to grayscale by removing saturation"""
    self.r, self.g, self.b, self.a = self.to_rgba(False).grayscale().values()
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{f"{int(self.a * 255):02X}" if self.a else ""}')
  def blend(self, other:'hexa', ratio:float = 0.5, additive_alpha:bool = False) -> 'rgba':
    """Blends the current color with another color using the specified ratio (`0.0`-`1.0`):<br>
    If `ratio` is `0.0` it means 100% of the current color and 0% of the `other` color (1:0 mixture)<br>
    If `ratio` is `0.5` it means 50% of both colors (1:1 mixture)<br>
    If `ratio` is `1.0` it means 0% of the current color and 100% of the `other` color (0:1 mixture)"""
    return self.to_rgba(False).blend(Color.to_rgba(other), ratio, additive_alpha).to_hexa()
  def is_dark(self) -> bool:
    """Returns `True` if the color is considered dark (converted `lightness < 50`)"""
    return self.to_hsla(False).is_dark()
  def is_light(self) -> bool:
    """Returns `True` if the color is considered light (`lightness >= 50`)"""
    return self.to_hsla(False).is_light()
  def is_grayscale(self) -> bool:
    """Returns `True` if the color is grayscale (`saturation == 0`)"""
    return self.to_hsla(False).is_grayscale()
  def is_opaque(self) -> bool:
    """Returns `True` if the color has no transparency (`alpha == 1.0`)"""
    return self.to_hsla(False).is_opaque()
  def with_alpha(self, alpha:float) -> 'hexa':
    """Returns a new color with the specified alpha value"""
    if not (isinstance(alpha, (int, float)) and 0 <= alpha <= 1): raise ValueError("'alpha' must be in [0.0, 1.0]")
    return hexa(f'#{self.r:02X}{self.g:02X}{self.b:02X}{int(alpha * 255):02X}')
  def complementary(self) -> 'hexa':
    """Returns the complementary color (180 degrees on the color wheel)"""
    return self.to_hsla(False).complementary().to_hexa()



################################################## PATH OPERATIONS ##################################################

class Path:
  @staticmethod
  def get(cwd:bool = False, base_dir:bool = False) -> str|list:
    paths = []
    if cwd: paths.append(_os.getcwd())
    if base_dir:
      if getattr(_sys, 'frozen', False) and hasattr(_sys, '_MEIPASS'): base_path = _sys._MEIPASS
      else:
        main_module = _sys.modules['__main__']
        if hasattr(main_module, '__file__'): base_path = _os.path.dirname(_os.path.abspath(main_module.__file__))
        elif hasattr(main_module, '__spec__') and main_module.__spec__ and getattr(main_module.__spec__, 'origin', None):
          base_path = _os.path.dirname(_os.path.abspath(main_module.__spec__.origin))
        else: raise RuntimeError('Can only get base directory if ran from a file.')
      paths.append(base_path)
    return paths[0] if len(paths) == 1 else paths

  @staticmethod
  def extend(path:str, search_in:str|list[str] = None, raise_error:bool = False) -> str:
    def get_closest_match(dir:str, part:str) -> str|None:
      try:
        files_and_dirs = _os.listdir(dir)
        matches = _difflib.get_close_matches(part, files_and_dirs, n=1, cutoff=0.6)
        return matches[0] if matches else None
      except: return None
    def find_path(start:str, parts:list[str]) -> str|None:
      current = start
      for part in parts:
        if _os.path.isfile(current): return current
        closest_match = get_closest_match(current, part)
        if closest_match: current = _os.path.join(current, closest_match)
        else: return None
      return current if _os.path.exists(current) and current != start else None
    def expand_env_path(p:str) -> str:
      if not '%' in p: return p
      parts = p.split('%')
      for i in range(1, len(parts), 2):
        if parts[i].upper() in _os.environ:
          parts[i] = _os.environ[parts[i].upper()]
      return ''.join(parts)
    path = _os.path.normpath(expand_env_path(path))
    if _os.path.isabs(path):
      drive, rel_path = _os.path.splitdrive(path)
      rel_path = rel_path.lstrip(_os.sep)
      search_dirs = [drive + _os.sep] if drive else [_os.sep]
    else:
      rel_path = path.lstrip(_os.sep)
      base_dir = Path.get(base_dir=True)
      search_dirs = [_os.getcwd(), base_dir, _os.path.expanduser('~'), _tempfile.gettempdir()]
    if search_in: search_dirs.extend([search_in] if isinstance(search_in, str) else search_in)
    path_parts = rel_path.split(_os.sep)
    for search_dir in search_dirs:
      full_path = _os.path.join(search_dir, rel_path)
      if _os.path.exists(full_path): return full_path
      match = find_path(search_dir, path_parts)
      if match: return match
    if raise_error: raise FileNotFoundError(f'Path \'{path}\' not found in specified directories.')
    return _os.path.join(search_dirs[0], rel_path)

  @staticmethod
  def remove(path:str, only_content:bool = False) -> None:
    if not _os.path.exists(path): return None
    if not only_content: _shutil.rmtree(path)
    elif _os.path.isdir(path):
      for filename in _os.listdir(path):
        file_path = _os.path.join(path, filename)
        try:
          if _os.path.isfile(file_path) or _os.path.islink(file_path): _os.unlink(file_path)
          elif _os.path.isdir(file_path): _shutil.rmtree(file_path)
        except Exception as e: print(f'Failed to delete {file_path}. Reason: {e}')



################################################## FILE OPERATIONS ##################################################

class File:
  @staticmethod
  def _make_path(filename:str, filetype:str, search_in:str|list[str] = None, prefer_base_dir:bool = True) -> str:
    """Get the path to a file in the cwd, the base-dir, or predefined directories.\n
    --------------------------------------------------------------------------------------
    If the `filename` is not found in the above directories, it will be searched<br>
    in the `search_in` directory/directories. If the file is still not found, it will<br>
    return the path to the file in the base-dir per default or to the file in the<br>
    cwd if `prefer_base_dir` is set to `False`."""
    if not filename.lower().endswith(f'.{filetype.lower()}'): filename = f'{filename}.{filetype.lower()}'
    try: return Path.extend(filename, search_in, raise_error=True)
    except FileNotFoundError: return _os.path.join(Path.get(base_dir=True), filename) if prefer_base_dir else _os.path.join(_os.getcwd(), filename)

  @staticmethod
  def rename_extension(file_path:str, new_extension:str) -> str:
    directory, filename_with_ext = _os.path.split(file_path)
    filename = filename_with_ext.split('.')[0]
    camel_case_filename = String.to_camel_case(filename)
    new_filename = f'{camel_case_filename}{new_extension}'
    new_file_path = _os.path.join(directory, new_filename)
    return new_file_path

  @staticmethod
  def create(content:str = '', file:str = 'new_file.txt', force:bool = False) -> str:
    """Create a file with ot without content.\n
    ----------------------------------------------------------------------------
    The function will throw a `FileExistsError` if the file already exists.<br>
    To overwrite the file, set the `force` parameter to `True`."""
    if _os.path.exists(file) and not force:
      with open(file, 'r', encoding='utf-8') as existing_file:
        existing_content = existing_file.read()
        if existing_content == content: raise FileExistsError('Already created this file. (nothing changed)')
      raise FileExistsError('File already exists.')
    with open(file, 'w', encoding='utf-8') as f: f.write(content)
    full_path = _os.path.abspath(file)
    return full_path



################################################## JSON-FILE OPERATIONS ##################################################

class Json:
  @staticmethod
  def read(json_file:str, comment_start:str = '>>', comment_end:str = '<<', return_original:bool = False) -> dict|tuple[dict,dict]:
    """Read JSON files, ignoring comments.\n
    -------------------------------------------------------------------------
    If only `comment_start` is found at the beginning of an item,<br>
    the whole item is counted as a comment and therefore ignored.<br>
    If `comment_start` and `comment_end` are found inside an item,<br>
    the the section from `comment_start` to `comment_end` is ignored.<br>
    If `return_original` is set to `True`, the original JSON is returned<br>
    additionally. (returns: `[processed_json, original_json]`)"""
    file_path = File._make_path(json_file, 'json', prefer_base_dir=True)
    with open(file_path, 'r') as file: content = file.read()
    try: data = _json.loads(content)
    except _json.JSONDecodeError as e: raise ValueError(f"Error parsing JSON in '{file_path}':  {str(e)}")
    processed_data = Data.remove_comments(data, comment_start, comment_end)
    if not processed_data: raise ValueError(f"The JSON file '{file_path}' is empty or contains only comments.")
    return (processed_data, data) if return_original else processed_data

  @staticmethod
  def create(content:dict, new_file:str = 'config', indent:int = 2, compactness:int = 1, force:bool = False) -> str:
    file_path = File._make_path(new_file, 'json', prefer_base_dir=True)
    if _os.path.exists(file_path) and not force:
      with open(file_path, 'r', encoding='utf-8') as existing_file:
        existing_content = _json.load(existing_file)
        if existing_content == content: raise FileExistsError(f'Already created this file. (nothing changed)')
      raise FileExistsError('File already exists.')
    with open(file_path, 'w', encoding='utf-8') as f: f.write(Data.to_str(content, indent, compactness, as_json=True))
    full_path = _os.path.abspath(file_path)
    return full_path

  @staticmethod
  def update(json_file:str, update_values:str|list[str], comment_start:str = '>>', comment_end:str = '<<', sep:tuple[str,str] = ('->', '::')) -> None:
    """Function to easily update single/multiple values inside JSON files.\n
    --------------------------------------------------------------------------------------------------------
    The param `json_file` is the path to the JSON file or just the name of the JSON file to be updated.\n
    --------------------------------------------------------------------------------------------------------
    The param `update_values` is a sort of path (or a list of paths) to the value/s to be updated, with<br>
    the new value at the end of the path.<br>
    In this example:
    ```\n {
       'healthy': {
         'fruit': ['apples', 'bananas', 'oranges'],
         'vegetables': ['carrots', 'broccoli', 'celery']
       }
     }\n```
    ... if you want to change the value of `'apples'` to `'strawberries'`, `update_values` would<br>
    be `healthy->fruit->apples::strawberries` or if you don't know that the value to update<br>
    is `apples` you can also use the position of the value, so `healthy->fruit->0::strawberries`.\n
    ⇾ **If the path from `update_values` doesn't exist, it will be created.**\n
    --------------------------------------------------------------------------------------------------------
    If only `comment_start` is found at the beginning of an item, the whole item is counted<br>
    as a comment and therefore ignored. If `comment_start` and `comment_end` are found<br>
    inside an item, the the section from `comment_start` to `comment_end` is ignored."""
    if isinstance(update_values, str): update_values = [update_values]
    valid_entries = [(parts[0].strip(), parts[1]) for update_value in update_values
      if len(parts := update_value.split(str(sep[1]).strip())) == 2]
    value_paths, new_values = (zip(*valid_entries) if valid_entries else ([], []))
    processed_data, data = Json.read(json_file, comment_start, comment_end, return_original=True)
    update = []
    for value_path, new_value in zip(value_paths, new_values):
      path_id = Data.get_path_id(processed_data, value_path)
      update.append(f'{path_id}::{new_value}')
    updated = Data.set_value_by_path_id(data, update)
    Json.create(updated, json_file, force=True)



################################################## SYSTEM ACTIONS ##################################################

class System:
  @staticmethod
  def restart(msg:str = None, wait:int = 0, continue_program:bool = False, force:bool = False) -> None:
    system = _platform.system().lower()
    if system == 'windows':
      if not force:
        output = _subprocess.check_output('tasklist', shell=True).decode()
        processes = [line.split()[0] for line in output.splitlines()[3:] if line.strip()]
        if len(processes) > 2:  # EXCLUDING THE PYTHON PROCESS AND CMD
          raise RuntimeError('Processes are still running. Use the parameter `force=True` to restart anyway.')
      if msg: _os.system(f'shutdown /r /t {wait} /c "{msg}"')
      else: _os.system('shutdown /r /t 0')
      if continue_program:
        print(f'Restarting in {wait} seconds...')
        _time.sleep(wait)
    elif system in ['linux', 'darwin']:
      if not force:
        output = _subprocess.check_output(['ps', '-A']).decode()
        processes = output.splitlines()[1:]  # EXCLUDE HEADER
        if len(processes) > 2:  # EXCLUDING THE PYTHON PROCESS AND PS
          raise RuntimeError('Processes are still running. Use the parameter `force=True` to restart anyway.')
      if msg:
        _subprocess.Popen(['notify-send', 'System Restart', msg])
        _time.sleep(wait)
      try: _subprocess.run(['sudo', 'shutdown', '-r', 'now'])
      except _subprocess.CalledProcessError: raise PermissionError('Failed to restart: insufficient privileges. Ensure sudo permissions are granted.')
      if continue_program:
        print(f'Restarting in {wait} seconds...')
        _time.sleep(wait)
    else: raise NotImplementedError(f'Restart not implemented for `{system}`')



################################################## PATH ACTIONS ##################################################

class EnvVars:
  """Functions for managing the systems environment-variables:
  - `EnvVars.get_paths()`
  - `EnvVars.has_path()`
  - `EnvVars.add_path()`"""
  @staticmethod
  def get_paths(as_list:bool = False) -> str|list:
    paths = _os.environ.get('PATH')
    return paths.split(_os.pathsep) if as_list else paths

  @staticmethod
  def has_path(path:str = None, cwd:bool = False, base_dir:bool = False) -> bool:
    if cwd: path = _os.getcwd()
    if base_dir: path = Path.get(base_dir=True)
    paths = EnvVars.get_paths()
    return path in paths

  @staticmethod
  def __add_sort_paths(add_path:str, current_paths:str) -> str:
    final_paths = Data.remove_empty_items(Data.remove_duplicates(f'{add_path};{current_paths}'.split(_os.pathsep)))
    final_paths.sort()
    return f'{_os.pathsep.join(final_paths)};'

  @staticmethod
  def add_path(add_path:str = None, cwd:bool = False, base_dir:bool = False, persistent:bool = True) -> None:
    if cwd: add_path = _os.getcwd()
    if base_dir: add_path = Path.get(base_dir=True)
    if not EnvVars.has_path(add_path):
      final_paths = EnvVars.__add_sort_paths(add_path, EnvVars.get_paths())
      _os.environ['PATH'] = final_paths
      if persistent:
        if _os.name == 'nt':  # Windows
          try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, final_paths)
            winreg.CloseKey(key)
          except ImportError: raise ImportError('Unable to make persistent changes on Windows.')
        else:  # UNIX-LIKE (Linux/macOS)
          shell_rc_file = _os.path.expanduser('~/.bashrc' if _os.path.exists(_os.path.expanduser('~/.bashrc')) else '~/.zshrc')
          with open(shell_rc_file, 'a') as f: f.write(f'\n# Added by XulbuX\nexport PATH="$PATH:{add_path}"\n')
          _os.system(f'source {shell_rc_file}')
    else: raise ValueError(f'{add_path} is already in PATH.')



################################################## CMD LOG & ACTIONS ##################################################

class Cmd:
  """Functions for logging and other small actions within the console:
  - `Cmd.get_args()`
  - `Cmd.user()`
  - `Cmd.is_admin()`
  - `Cmd.pause_exit()`
  - `Cmd.cls()`
  - `Cmd.log()`
  - `Cmd.info()`
  - `Cmd.done()`
  - `Cmd.warn()`
  - `Cmd.fail()`
  - `Cmd.exit()`
  - `Cmd.confirm()`\n
  ----------------------------------------------------------------------------------------------------------
  You can also use special formatting codes directly inside the log message to change their appearance.<br>
  For more detailed information about formatting codes, see the `log` class description."""
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
  def debug(msg:str = 'Point in program reached.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = '#FFD260', default_color:hexa|rgba = '#809FFF', pause:bool = False, exit:bool = False) -> None:
    Cmd.log('DEBUG', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def info(msg:str = 'Program running.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = '#77F', default_color:hexa|rgba = '#809FFF', pause:bool = False, exit:bool = False) -> None:
    Cmd.log('INFO', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def done(msg:str = 'Program finished.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = '#49EAB7', default_color:hexa|rgba = '#809FFF', pause:bool = False, exit:bool = False) -> None:
    Cmd.log('DONE', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def warn(msg:str = 'Important message.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = '#FF8C60', default_color:hexa|rgba = '#809FFF', pause:bool = False, exit:bool = True) -> None:
    Cmd.log('WARN', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit)

  @staticmethod
  def fail(msg:str = 'Program error.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = '#FF606A', default_color:hexa|rgba = '#809FFF', pause:bool = False, exit:bool = True, reset_ansi=True) -> None:
    Cmd.log('FAIL', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit, reset_ansi=reset_ansi)

  @staticmethod
  def exit(msg:str = 'Program ended.', start:str = '\n', end:str = '\n\n', title_bg_color:hexa|rgba = '#C860FF', default_color:hexa|rgba = '#809FFF', pause:bool = False, exit:bool = True, reset_ansi=True) -> None:
    Cmd.log('EXIT', msg, start, end, title_bg_color, default_color)
    Cmd.pause_exit(pause, exit, reset_ansi=reset_ansi)

  @staticmethod
  def confirm(msg:str = 'Are you sure? [_|dim]((Y/n):  )', start = '\n', end = '\n', default_color:hexa|rgba = '#3EE6DE', default_is_yes:bool = True) -> None:
    confirmed = input(FormatCodes.to_ansi(f'{start}  {str(msg)}', default_color)).strip().lower() in (('', 'y', 'yes') if default_is_yes else ('y', 'yes'))
    if end: Cmd.log('', '') if end == '\n' else Cmd.log('', end[1:]) if end.startswith('\n') else Cmd.log('', end)
    return confirmed



################################################## ANSI-/PRETTY PRINTING ##################################################

class FormatCodes:
  """Functions to be able to use special (easy) formatting codes directly inside some message (string).<br>
  These codes, when used within following functions, will change the look of log within the console:
  - `FormatCodes.print()` (*print a special format-codes containing string*)
  - `FormatCodes.input()` (*input with a special format-codes containing prompt*)
  - `FormatCodes.to_ansi()` (*transform all special format-codes into ANSI codes in a string*)\n
  --------------------------------------------------------------------------------------------------------------------
  How to change the text format and color?<br>
  **Example string with formatting codes:**<br>
  > `[bold]This is bold text, [#F08]which is pink now [black|BG:#FF0088] and now it changed`<br>
  > `to black with a pink background. [_]And this is the boring text, where everything is reset.`\n
  ⇾ **Instead of writing the formats all separate** `[…][…][…]` **you can join them like this** `[…|…|…]`\n
  --------------------------------------------------------------------------------------------------------------------
  You can also automatically reset a certain format, behind text like shown in the following example:<br>
  > `This is normal text [b](which is bold now) but now it was automatically reset to normal.`\n
  This will only reset formats, that have a reset listed below. Colors and BG-colors won't be reset.<br>
  This is what will happen, if you use it with a color-format:<br>
  > `[cyan]This is cyan text [b](which is bold now.) Now it's not bold any more but still cyan.`\n
  If you want to ignore the `()` brackets you can put a `\\` or `/` between:<br>
  > `[cyan]This is cyan text [b]/(which is bold now.) And now it is still bold and cyan.`\n
  ⇾ **To see these examples in action, you can put them into the** `FormatCodes.print()` **function.**\n
  --------------------------------------------------------------------------------------------------------------------
  **All possible formatting codes:**
  - HEX colors:  `[#F08]` or `[#FF0088]` (*with or without leading #*)
  - RGB colors:  `[rgb(255, 0, 136)]`
  - bright colors:  `[bright:#F08]`
  - background colors:  `[BG:#F08]`
  - standard cmd colors:
    - `[black]`
    - `[red]`
    - `[green]`
    - `[yellow]`
    - `[blue]`
    - `[magenta]`
    - `[cyan]`
    - `[white]`
  - bright cmd colors: `[bright:black]` or `[br:black]`, `[bright:red]` or `[br:red]`, ...
  - background cmd colors: `[BG:black]`, `[BG:red]`, ...
  - bright background cmd colors: `[BG:bright:black]` or `[BG:br:black]`, `[BG:bright:red]` or `[BG:br:red]`, ...<br>
    ⇾ **The order of** `BG:` **and** `bright:` or `br:` **does not matter.**
  - text formats:
    - `[bold]` or `[b]`
    - `[dim]`
    - `[italic]` or `[i]`
    - `[underline]` or `[u]`
    - `[inverse]` or `[in]`
    - `[hidden]` or `[h]`
    - `[strikethrough]` or `[s]`
    - `[double-underline]` or `[du]`
  - specific reset:  `[_bold]` or `[_b]`, `[_dim]`, ... or `[_color]` or `[_c]`, `[_background]` or `[_bg]`
  - total reset: `[_]` (only if no `default_color` is set, otherwise see **↓** )
  --------------------------------------------------------------------------------------------------------------------
  **Special formatting when param `default_color` is set to a color:**
  - `[*]` will reset everything, just like `[_]`, but the text-color will remain in `default_color`
  - `[*color]` will reset the text-color, just like `[_color]`, but then also make it `default_color`
  - `[default]` will just color the text in `default_color`,
  - `[BG:default]` will color the background in `default_color`\n
  Unlike the standard cmd colors, the default color can be changed by using the following modifiers:
  - `[l]` will lighten the `default_color` text by `brightness_steps`%
  - `[ll]` will lighten the `default_color` text by `2 × brightness_steps`%
  - `[lll]` will lighten the `default_color` text by `3 × brightness_steps`%
  - ... etc. Same thing for darkening:
  - `[d]` will darken the `default_color` text by `brightness_steps`%
  - `[dd]` will darken the `default_color` text by `2 × brightness_steps`%
  - `[ddd]` will darken the `default_color` text by `3 × brightness_steps`%
  - ... etc.\n
  Per default, you can also use `+` and `-` to get lighter and darker `default_color` versions.<br>
  This can also be changed by changing the param `_modifiers = ('+l', '-d')`."""

  @staticmethod
  def print(prompt:str, default_color:hexa|rgba = None, brightness_steps:int = 20, sep:str = ' ', end:str = '\n') -> None:
    FormatCodes.__config_console()
    ansi_prompt = FormatCodes.to_ansi(prompt, default_color, brightness_steps)
    print(ansi_prompt, sep=sep, end=end, flush=True)

  @staticmethod
  def input(prompt:str, default_color:hexa|rgba = None, brightness_steps:int = 20) -> str:
    FormatCodes.__config_console()
    ansi_prompt = FormatCodes.to_ansi(prompt, default_color, brightness_steps)
    return input(ansi_prompt)

  @staticmethod
  def to_ansi(string:str, default_color:hexa|rgba = None, brightness_steps:int = 20, _default_start:bool = True) -> str:
    result, use_default = '', default_color and (Color.is_valid_rgba(default_color, False) or Color.is_valid_hexa(default_color, False))
    if use_default:
      string = _re.sub(r'\[\s*([^]_]*?)\s*\*\s*([^]_]*?)\]', r'[\1_|default\2]', string)  # REPLACE `[…|*|…]` WITH `[…|_|default|…]`
      string = _re.sub(r'\[\s*([^]_]*?)\s*\*color\s*([^]_]*?)\]', r'[\1default\2]', string)  # REPLACE `[…|*color|…]` WITH `[…|default|…]`
    def replace_keys(match:_regex.Match) -> str:
      format_keys, esc, auto_reset_txt = match.group(1), match.group(2), match.group(3)
      if not format_keys: return match.group(0)
      else:
        format_keys = [k.replace(' ', '') for k in format_keys.split('|') if k.replace(' ', '')]
        ansi_resets, ansi_formats = [], [FormatCodes.__get_replacement(k, default_color, brightness_steps) for k in format_keys]
        if auto_reset_txt and not esc:
          reset_keys = ['_color' if Color.is_valid(k) or k in COLOR_MAP
            else '_bg' if (set(k.lower().split(':')) & {'bg', 'bright', 'br'} and len(k.split(':')) <= 3 and any(Color.is_valid(k[i:]) or k[i:] in COLOR_MAP for i in range(len(k))))
            else f'_{k}' for k in format_keys]
          ansi_resets = [r for k in reset_keys if (r := FormatCodes.__get_replacement(k, default_color, brightness_steps)).startswith(ANSI_PREF)]
      if not all(f.startswith(ANSI_PREF) for f in ansi_formats): return match.group(0)
      return ''.join(ansi_formats) + ((f'({FormatCodes.to_ansi(auto_reset_txt, default_color, brightness_steps, False)})' if esc else auto_reset_txt) if auto_reset_txt else '') + ('' if esc else ''.join(ansi_resets))
    result = '\n'.join(_regex.sub(Regex.brackets('[', ']', is_group=True) + r'(?:\s*([/\\]?)\s*' + Regex.brackets('(', ')', is_group=True) + r')?', replace_keys, line) for line in string.splitlines())
    return (FormatCodes.__get_default_ansi(default_color) if _default_start else '') + result if use_default else result

  @staticmethod
  def __config_console() -> None:
    _sys.stdout.flush()
    kernel32 = _ctypes.windll.kernel32
    h = kernel32.GetStdHandle(-11)
    mode = _ctypes.c_ulong()
    kernel32.GetConsoleMode(h, _ctypes.byref(mode))
    kernel32.SetConsoleMode(h, mode.value | 0x0004)  # ENABLE VIRTUAL TERMINAL PROCESSING

  @staticmethod
  def __get_default_ansi(default_color:hexa|rgba, format_key:str = None, brightness_steps:int = None, _modifiers:tuple[str,str] = ('+l', '-d')) -> str|None:
    if Color.is_valid_hexa(default_color, False): default_color = Color.to_rgba(default_color)
    if not brightness_steps or (format_key and _re.search(r'(?i)((?:BG\s*:)?)\s*default', format_key)):
      if format_key and _re.search(r'(?i)BG\s*:\s*default', format_key): return f'{ANSI_PREF}48;2;{default_color[0]};{default_color[1]};{default_color[2]}m'
      return f'{ANSI_PREF}38;2;{default_color[0]};{default_color[1]};{default_color[2]}m'
    match = _re.match(rf'(?i)((?:BG\s*:)?)\s*({"|".join([f"{_re.escape(m)}+" for m in _modifiers[0] + _modifiers[1]])})$', format_key)
    if not match or not match.group(2): return None
    is_bg, modifier = match.group(1), match.group(2)
    new_rgb, lighten, darken = None, None, None
    for mod in _modifiers[0]:
      lighten = String.get_repeated_symbol(modifier, mod)
      if lighten and lighten > 0:
        new_rgb = Color.adjust_brightness(default_color, (brightness_steps / 100) * lighten)
        break
    if not new_rgb:
      for mod in _modifiers[1]:
        darken = String.get_repeated_symbol(modifier, mod)
        if darken and darken > 0:
          print(-(brightness_steps / 100) * darken)
          new_rgb = Color.adjust_brightness(default_color, -(brightness_steps / 100) * darken)
          break
    if new_rgb: return f'{ANSI_PREF}48;2;{new_rgb[0]};{new_rgb[1]};{new_rgb[2]}m' if is_bg else f'{ANSI_PREF}38;2;{new_rgb[0]};{new_rgb[1]};{new_rgb[2]}m'

  @staticmethod
  def __get_replacement(format_key:str, default_color:hexa|rgba = None, brightness_steps:int = 20, _modifiers:tuple[str, str] = ('+l', '-d')) -> str:
    """Gives you the corresponding ANSI code for the given format key.<br>
    If `default_color` is not `None`, the text color will be `default_color` if all formats<br>
    are reset or you can get lighter or darker version of `default_color` (also as BG) by<br>
    using one or more `_modifiers` symbols as a format key ()"""
    def key_exists(key:str) -> bool:
      for map_key in CODES_MAP:
        if isinstance(map_key, tuple) and key in map_key: return True
        elif key == map_key: return True
      return False
    def get_value(key:str) -> any:
      for map_key in CODES_MAP:
        if isinstance(map_key, tuple) and key in map_key: return CODES_MAP[map_key]
        elif key == map_key: return CODES_MAP[map_key]
      return None
    use_default = default_color and (Color.is_valid_rgba(default_color, False) or Color.is_valid_hexa(default_color, False))
    _format_key, format_key = format_key, FormatCodes.__normalize(format_key)
    if use_default:
      new_default_color = FormatCodes.__get_default_ansi(default_color, format_key, brightness_steps, _modifiers)
      if new_default_color: return new_default_color
    if key_exists(format_key): return ANSI_PREF + get_value(format_key)
    rgb_match = _re.match(r'(?i)\s*(BG\s*:)?\s*(rgb)?\s*\(?\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)?\s*', format_key)
    hex_match = _re.match(r'(?i)\s*(BG\s*:)?\s*#?([0-9A-F]{8}|[0-9A-F]{6}|[0-9A-F]{4}|[0-9A-F]{3})\s*', format_key)
    try:
      if rgb_match:
        is_bg = rgb_match.group(1)
        r, g, b = map(int, rgb_match.groups()[2:])
        if Color.is_valid_rgba((r, g, b)): return f'{ANSI_PREF}48;2;{r};{g};{b}m' if is_bg else f'{ANSI_PREF}38;2;{r};{g};{b}m'
      elif hex_match:
        is_bg = hex_match.group(1)
        rgb = Color.to_rgba(hex_match.group(2))
        return f'{ANSI_PREF}48;2;{rgb[0]};{rgb[1]};{rgb[2]}m' if is_bg else f'{ANSI_PREF}38;2;{rgb[0]};{rgb[1]};{rgb[2]}m'
    except Exception: pass
    return _format_key

  @staticmethod
  def __normalize(format_key:str) -> str:
    """Put the given format key in the correct format:<br>
    `1` put `BG:` as first key-part<br>
    `2` put `bright:` or `br:` as second key-part<br>
    `3` put everything else behind<br>
    `4` everything in lower case"""
    format_key = format_key.replace(' ', '').lower().strip()
    if ':' in format_key:
      key_parts = format_key.split(':')
      format_key = ('bg:' if 'bg' in key_parts else '') + ('bright:' if 'bright' in key_parts or 'br' in key_parts else '') + ''.join(Data.remove(key_parts, ['bg', 'bright', 'br']))
    return format_key

  
  
################################################## COLOR OPERATIONS ##################################################

class Color:
  @staticmethod
  def has_alpha(color:rgba|hsla|hexa) -> bool:
    """Check if the given color has an alpha channel.\n
    --------------------------------------------------------------------------------
    Input a HEX or RGB color as `color`.<br>
    Returns `True` if the color has an alpha channel and `False` otherwise."""
    if isinstance(color, (rgba, hsla, hexa)): return color.has_alpha()
    if isinstance(color, str) and Color.is_valid_hexa(color): return len(color.lstrip('#')) == 4 or len(color.lstrip('#')) == 8
    elif isinstance(color, (list, tuple, dict)) and len(color) == 4: return True
    else: return False

  @staticmethod
  def is_valid_rgba(color:str|list|tuple|dict, allow_alpha:bool = True) -> bool:
    try:
      if isinstance(color, (list, tuple, rgba)):
        if allow_alpha and Color.has_alpha(color): return 0 <= color[0] <= 255 and 0 <= color[1] <= 255 and 0 <= color[2] <= 255 and 0 <= color[3] <= 255
        else: return 0 <= color[0] <= 255 and 0 <= color[1] <= 255 and 0 <= color[2] <= 255
      elif isinstance(color, dict):
        if allow_alpha and Color.has_alpha(color): return 0 <= color['r'] <= 255 and 0 <= color['g'] <= 255 and 0 <= color['b'] <= 255 and 0 <= color['a'] <= 255
        else: return 0 <= color['r'] <= 255 and 0 <= color['g'] <= 255 and 0 <= color['b'] <= 255
      elif isinstance(color, str): return bool(_re.fullmatch(Regex.rgb_str(), color))
    except: return False

  @staticmethod
  def is_valid_hsla(color:str|list|tuple|dict, allow_alpha:bool = True) -> bool:
    try:
      if isinstance(color, (list, tuple, hsla)):
        if allow_alpha and Color.has_alpha(color): return 0 <= color[0] <= 360 and 0 <= color[1] <= 100 and 0 <= color[2] <= 100 and 0.0 <= color[3] <= 1.0
        else: return 0 <= color[0] <= 360 and 0 <= color[1] <= 100 and 0 <= color[2] <= 100
      elif isinstance(color, dict):
        if allow_alpha and Color.has_alpha(color): return 0 <= color['h'] <= 360 and 0 <= color['s'] <= 100 and 0 <= color['l'] <= 100 and 0.0 <= color['a'] <= 1.0
        else: return 0 <= color['h'] <= 360 and 0 <= color['s'] <= 100 and 0 <= color['l'] <= 100
      elif isinstance(color, str): return bool(_re.fullmatch(Regex.hsl_str(), color))
    except: return False

  @staticmethod
  def is_valid_hexa(color:str, allow_alpha:bool = True) -> bool:
    try:
      if allow_alpha: pattern = r'(?i)^([0-9A-F]{8}|[0-9A-F]{6}|[0-9A-F]{4}|[0-9A-F]{3})$'
      else: pattern = r'(?i)^([0-9A-F]{6}|[0-9A-F]{3})$'
      return bool(_re.fullmatch(pattern, color.lstrip('#')))
    except: return False

  @staticmethod
  def is_valid(color:str|list|tuple|dict, allow_alpha:bool = True) -> bool:
    return Color.is_valid_hexa(color, allow_alpha) or Color.is_valid_rgba(color, allow_alpha) or Color.is_valid_hsla(color, allow_alpha)

  @staticmethod
  def str_to_rgba(rgb_str:str) -> rgba|None:
    try: _rgba = _re.match(Regex.rgb_str(allow_alpha=True), rgb_str).groups()
    except: return None
    if _rgba[3] in ['', None]: return rgba(int(_rgba[0]), int(_rgba[1]), int(_rgba[2]))
    else: return rgba(int(_rgba[0]), int(_rgba[1]), int(_rgba[2]), (int(_rgba[3]) if _rgba[3].count('.') == 0 else float(_rgba[3])))

  @staticmethod
  def to_rgba(color:hsla|hexa) -> rgba:
    if isinstance(color, (hsla, hexa)): return color.to_rgba()
    if Color.is_valid_hsla(color): return hsla(color[0], color[1], color[2], color[3]).to_rgba() if Color.has_alpha(color) else hsla(color[0], color[1], color[2]).to_rgba()
    if Color.is_valid_hexa(color): return hexa(color).to_rgba()
    raise ValueError('Invalid color format')

  @staticmethod
  def to_hsla(color:rgba|hexa) -> hsla:
    if isinstance(color, (rgba, hexa)): return color.to_hsla()
    if Color.is_valid_rgba(color): return rgba(color[0], color[1], color[2], color[3]).to_hsla() if Color.has_alpha(color) else rgba(color[0], color[1], color[2]).to_hsla()
    if Color.is_valid_hexa(color): return hexa(color).to_hsla()
    raise ValueError('Invalid color format')

  @staticmethod
  def to_hexa(color:rgba|hsla) -> hexa:
    if isinstance(color, (rgba, hsla)): return color.to_hexa()
    if Color.is_valid_rgba(color): return rgba(color[0], color[1], color[2], color[3]).to_hexa() if Color.has_alpha(color) else rgba(color[0], color[1], color[2]).to_hexa()
    if Color.is_valid_hsla(color): return hsla(color[0], color[1], color[2], color[3]).to_hexa() if Color.has_alpha(color) else hsla(color[0], color[1], color[2]).to_hexa()
    raise ValueError('Invalid color format')

  @staticmethod
  def text_color_for_on_bg(title_bg_color:hexa|rgba = '#FFF') -> hexa|rgba:
    was_hex = False
    if Color.is_valid_hexa(title_bg_color): was_hex, title_bg_color = True, Color.to_rgba(title_bg_color)
    brightness = 0.2126 * title_bg_color[0] + 0.7152 * title_bg_color[1] + 0.0722 * title_bg_color[2]
    return (hexa('#FFF') if was_hex else rgba(255, 255, 255)) if brightness < 128 else (hexa('#000') if was_hex else rgba(0, 0, 0))

  @staticmethod
  def adjust_brightness(color:hexa|rgba, brightness_change:float) -> hexa|rgba:
    """In- or decrease the brightness of the input color.\n
    -----------------------------------------------------------------------------------------------------------------
    **color** (hexa | rgb): HEX or RGB color.<br>
    **brightness_change** (float): A float between -1.0 (darken by `100%`) and 1.0 (lighten by `100%`), inclusive.\n
    -----------------------------------------------------------------------------------------------------------------
    **returns** (hexa | rgb): The adjusted color in the format of the input color."""
    if Color.is_valid_hexa(color): _rgba = Color.to_rgba(color)
    elif Color.is_valid_rgba(color): _rgba = color
    else: raise ValueError(f"Invalid color format '{str(color)}' Use HEX (e.g. '#F00' and '#FF0000') or RGB (e.g. (255, 0, 0) and (255, 0, 0, 1.0))")
    r, g, b, a = _rgba.r, _rgba.g, _rgba.b, _rgba.a if hasattr(_rgba, 'a') else None
    r = int(max(min(r + (255 - r) * brightness_change if brightness_change > 0 else r * (1 + brightness_change), 255), 0))
    g = int(max(min(g + (255 - g) * brightness_change if brightness_change > 0 else g * (1 + brightness_change), 255), 0))
    b = int(max(min(b + (255 - b) * brightness_change if brightness_change > 0 else b * (1 + brightness_change), 255), 0))
    if isinstance(color, (str, hexa)): return Color.to_hexa((r, g, b, a))
    else: return rgba(r, g, b, a) if a else rgba(r, g, b)

  @staticmethod
  def adjust_saturation(color:hexa|rgba, saturation_change:float) -> hexa|rgba:
    if Color.is_valid_hexa(color): _rgb = Color.to_rgba(color)
    elif Color.is_valid_rgba(color): _rgb = color
    else: raise ValueError(f'Invalid color format "{str(color)}". Use HEX (e.g. "#F00" and "#FF0000") or RGB (e.g. (255, 0, 0) and (255, 0, 0, 1.0))')
    hsl = Color.to_hsla(_rgb)
    h, s, l, a = hsl[0], hsl[1], hsl[2], hsl[3]
    s = max(0, min(100, s + saturation_change * 100))
    if isinstance(color, (str, hexa)): return Color.to_hexa(Color.to_rgba((h, s, l, a)))
    return Color.to_rgba((h, s, l, a))


################################################## DATA OPERATIONS ##################################################

class Data:
  @staticmethod
  def chars_count(data:list|tuple|set|frozenset|dict) -> int:
    """The sum of all the characters including the keys in dictionaries."""
    if isinstance(data, dict): return sum(len(str(k)) + len(str(v)) for k, v in data.items())
    return sum(len(str(item)) for item in data)

  @staticmethod
  def strip(data:list|tuple|dict) -> list|tuple|dict:
    if isinstance(data, dict): return {k: v.strip() if isinstance(v, str) else Data.strip(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
      stripped = [item.strip() if isinstance(item, str) else Data.strip(item) for item in data]
      return tuple(stripped) if isinstance(data, tuple) else stripped
    return data.strip() if isinstance(data, str) else data

  @staticmethod
  def remove(data:list|tuple|dict, items:list[str]) -> list|tuple|dict:
    """Remove multiple items from lists and tuples or keys from dictionaries."""
    if isinstance(data, (list, tuple)):
      result = [k for k in data if k not in items]
      return result if isinstance(data, list) else tuple(result)
    if isinstance(data, dict): return {k: v for k, v in data.items() if k not in items}

  @staticmethod
  def remove_empty_items(data:list|tuple|dict, spaces_are_empty:bool = False) -> list|tuple|dict:
    if isinstance(data, dict):
      filtered_dict = {}
      for key, value in data.items():
        if isinstance(value, (list, tuple, dict)):
          filtered_value = Data.remove_empty_items(value, spaces_are_empty)
          if filtered_value: filtered_dict[key] = filtered_value
        elif value not in ['', None] and not ((spaces_are_empty and isinstance(value, str)) and value.strip() in ['', None]): filtered_dict[key] = value
      return filtered_dict
    filtered = []
    for item in data:
      if isinstance(item, (list, tuple, dict)):
        deduped_item = Data.remove_empty_items(item, spaces_are_empty)
        if deduped_item:
          if isinstance(item, tuple): deduped_item = tuple(deduped_item)
          filtered.append(deduped_item)
      elif item not in ['', None] and not ((spaces_are_empty and isinstance(item, str)) and item.strip() in ['', None]): filtered.append(item)
    return tuple(filtered) if isinstance(data, tuple) else filtered

  @staticmethod
  def remove_duplicates(data:list|tuple|dict) -> list|tuple|dict:
    if isinstance(data, dict): return {k: Data.remove_duplicates(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
      unique_items = []
      for item in data:
        if isinstance(item, (list, tuple, set, dict)):
          deduped_item = Data.remove_duplicates(item)
          if deduped_item not in unique_items: unique_items.append(deduped_item)
        elif item not in unique_items: unique_items.append(item)
      return tuple(unique_items) if isinstance(data, tuple) else unique_items
    return data

  @staticmethod
  def remove_comments(data:list|tuple|dict, comment_start:str = '>>', comment_end:str = '<<', comment_sep:str = '') -> list|tuple|dict:
    """Remove comments from a list, tuple or dictionary.\n
    -----------------------------------------------------------------------------------------------------------------
    The `data` parameter is your list, tuple or dictionary, where the comments should get removed from.<br>
    The `comment_start` parameter is the string that marks the start of a comment inside `data`. (default: `>>`)<br>
    The `comment_end` parameter is the string that marks the end of a comment inside `data`. (default: `<<`)<br>
    The `comment_sep` parameter is a string with which a comment will be replaced, if it is between strings.\n
    -----------------------------------------------------------------------------------------------------------------
    Examples:\n
    ```python\n data = {
       'key1': [
         '>> COMMENT IN THE BEGINNING OF THE STRING <<  value1',
         'value2  >> COMMENT IN THE END OF THE STRING',
         'val>> COMMENT IN THE MIDDLE OF THE STRING <<ue3',
         '>> FULL VALUE IS A COMMENT  value4'
       ],
       '>> FULL KEY + ALL ITS VALUES ARE A COMMENT  key2': [
         'value',
         'value',
         'value'
       ],
       'key3': '>> ALL THE KEYS VALUES ARE COMMENTS  value'
     }
     processed_data = Data.remove_comments(data, comment_start='>>', comment_end='<<', comment_sep='__')\n```
    -----------------------------------------------------------------------------------------------------------------
    For this example, `processed_data` will be:
    ```python\n {
       'key1': [
         'value1',
         'value2',
         'val__ue3'
       ],
       'key3': None
     }\n```
    For `key1`, all the comments will just be removed, except at `value3` and `value4`:<br>
     `value3` The comment is removed and the parts left and right are joined through `comment_sep`.<br>
     `value4` The whole value is removed, since the whole value was a comment.<br>
    For `key2`, the key, including its whole values will be removed.<br>
    For `key3`, since all its values are just comments, the key will still exist, but with a value of `None`."""
    def process_item(item:dict|list|tuple|str) -> dict|list|tuple|str|None:
      if isinstance(item, dict):
        processed_dict = {}
        for key, val in item.items():
          processed_key = process_item(key)
          if processed_key is not None:
            processed_val = process_item(val)
            if isinstance(val, (list, tuple, dict)):
              if processed_val: processed_dict[processed_key] = processed_val
            elif processed_val is not None: processed_dict[processed_key] = processed_val
            else: processed_dict[processed_key] = None
        return processed_dict
      elif isinstance(item, list):  return [v for v in (process_item(val) for val in item) if v is not None]
      elif isinstance(item, tuple): return tuple(v for v in (process_item(val) for val in item) if v is not None)
      elif isinstance(item, str):
        if comment_end: no_comments = _re.sub(rf'^((?:(?!{_re.escape(comment_start)}).)*){_re.escape(comment_start)}(?:(?:(?!{_re.escape(comment_end)}).)*)(?:{_re.escape(comment_end)})?(.*?)$',
            lambda m: f'{m.group(1).strip()}{comment_sep if (m.group(1).strip() not in ["", None]) and (m.group(2).strip() not in ["", None]) else ""}{m.group(2).strip()}', item)
        else: no_comments = None if item.lstrip().startswith(comment_start) else item
        return no_comments.strip() if no_comments and no_comments.strip() != '' else None
      else: return item
    return process_item(data)

  @staticmethod
  def is_equal(data1:list|tuple|dict, data2:list|tuple|dict, ignore_paths:str|list[str] = '', comment_start:str = '>>', comment_end:str = '<<', sep:str = '->') -> bool:
    """Compares two structures and returns `True` if they are equal and `False` otherwise.\n
    ⇾ **Will not detect, if a key-name has changed, only if removed or added.**\n
    ------------------------------------------------------------------------------------------------
    Ignores the specified (found) key/s or item/s from `ignore_paths`. Comments are not ignored<br>
    when comparing. `comment_start` and `comment_end` are only used for key recognition.\n
    ------------------------------------------------------------------------------------------------
    The paths from `ignore_paths` work exactly the same way as the paths from `value_paths`<br>
    in the function `Data.get_path_id()`, just like the `sep` parameter. For more detailed<br>
    explanation, see the documentation of the function `Data.get_path_id()`."""
    def process_ignore_paths(ignore_paths:str|list[str]) -> list[list[str]]:
      if isinstance(ignore_paths, str): ignore_paths = [ignore_paths]
      return [path.split(sep) for path in ignore_paths if path]
    def compare(d1:dict|list|tuple, d2:dict|list|tuple, ignore_paths:list[list[str]], current_path:list = []) -> bool:
      if ignore_paths and any(current_path == path[:len(current_path)] and len(current_path) == len(path) for path in ignore_paths): return True
      if isinstance(d1, dict) and isinstance(d2, dict):
        if set(d1.keys()) != set(d2.keys()): return False
        return all(compare(d1[key], d2[key], ignore_paths, current_path + [key]) for key in d1)
      elif isinstance(d1, (list, tuple)) and isinstance(d2, (list, tuple)):
        if len(d1) != len(d2): return False
        return all(compare(item1, item2, ignore_paths, current_path + [str(i)]) for i, (item1, item2) in enumerate(zip(d1, d2)))
      else: return d1 == d2
    return compare(Data.remove_comments(data1, comment_start, comment_end), Data.remove_comments(data2, comment_start, comment_end), process_ignore_paths(ignore_paths))

  @staticmethod
  def get_fingerprint(data:list|tuple|dict) -> list|tuple|dict|None:
    if isinstance(data, dict): return {i: type(v).__name__ for i, v in enumerate(data.values())}
    elif isinstance(data, (list, tuple)): return {i: type(v).__name__ for i, v in enumerate(data)}
    return None

  @staticmethod
  def get_path_id(data:list|tuple|dict, value_paths:str|list[str], sep:str = '->', ignore_not_found:bool = False) -> str|list[str]:
    """Generates a unique ID based on the path to a specific value within a nested data structure.\n
    -------------------------------------------------------------------------------------------------
    The `data` parameter is the list, tuple, or dictionary, which the id should be generated for.\n
    -------------------------------------------------------------------------------------------------
    The param `value_path` is a sort of path (or a list of paths) to the value/s to be updated.<br>
    In this example:
    ```\n {
       'healthy': {
         'fruit': ['apples', 'bananas', 'oranges'],
         'vegetables': ['carrots', 'broccoli', 'celery']
       }
     }\n```
    ... if you want to change the value of `'apples'` to `'strawberries'`, `value_path`<br>
    would be `healthy->fruit->apples` or if you don't know that the value is `apples`<br>
    you can also use the position of the value, so `healthy->fruit->0`.\n
    -------------------------------------------------------------------------------------------------
    The `sep` param is the separator between the keys in the path<br>
    (default is `->` just like in the example above).\n
    -------------------------------------------------------------------------------------------------
    If `ignore_not_found` is `True`, the function will return `None` if the value is not<br>
    found instead of raising an error."""
    if isinstance(value_paths, str): value_paths = [value_paths]
    path_ids = []
    for path in value_paths:
      keys = [k.strip() for k in path.split(str(sep).strip()) if k.strip() != '']
      id_part_len, _path_ids, _obj = 0, [], data
      try:
        for k in keys:
          if isinstance(_obj, dict):
            if k.isdigit(): raise TypeError(f'Key \'{k}\' is invalid for a dict type.')
            try:
              idx = list(_obj.keys()).index(k)
              _path_ids.append(idx)
              _obj = _obj[k]
            except KeyError:
              if ignore_not_found:
                _path_ids = None
                break
              raise KeyError(f'Key \'{k}\' not found in dict.')
          elif isinstance(_obj, (list, tuple)):
            try:
              idx = int(k)
              _path_ids.append(idx)
              _obj = _obj[idx]
            except ValueError:
              try:
                idx = _obj.index(k)
                _path_ids.append(idx)
                _obj = _obj[idx]
              except ValueError:
                if ignore_not_found:
                  _path_ids = None
                  break
                raise ValueError(f'Value \'{k}\' not found in list/tuple.')
          else: break
          if _path_ids: id_part_len = max(id_part_len, len(str(_path_ids[-1])))
        if _path_ids is not None: path_ids.append(f'{id_part_len}>{"".join([str(id).zfill(id_part_len) for id in _path_ids])}')
        elif ignore_not_found: path_ids.append(None)
      except (KeyError, ValueError, TypeError) as e:
        if ignore_not_found: path_ids.append(None)
        else: raise e
    return path_ids if len(path_ids) > 1 else path_ids[0] if len(path_ids) == 1 else None

  @staticmethod
  def get_value_by_path_id(data:list|tuple|dict, path_id:str, get_key:bool = False) -> any:
    """Retrieves the value from `data` using the provided `path_id`.\n
    ------------------------------------------------------------------------------------
    Input a list, tuple or dict as `data`, along with `path_id`, which is a path-id<br>
    that was created before using `Object.get_path_id()`. If `get_key` is True<br>
    and the final item is in a dict, it returns the key instead of the value.\n
    ------------------------------------------------------------------------------------
    The function will return the value (or key) from the path-id location, as long as<br>
    the structure of `data` hasn't changed since creating the path-id to that value."""
    def get_nested(data:list|tuple|dict, path:list[int], get_key:bool) -> any:
      parent = None
      for i, idx in enumerate(path):
        if isinstance(data, dict):
          keys = list(data.keys())
          if i == len(path) - 1 and get_key: return keys[idx]
          parent = data
          data = data[keys[idx]]
        elif isinstance(data, (list, tuple)):
          if i == len(path) - 1 and get_key:
            if parent is None or not isinstance(parent, dict): raise ValueError('Cannot get key from list or tuple without a parent dictionary')
            return next(key for key, value in parent.items() if value is data)
          parent = data
          data = data[idx]
        else: raise TypeError(f'Unsupported type {type(data)} at path {path[:i+1]}')
      return data
    path = Data._sep_path_id(path_id)
    return get_nested(data, path, get_key)

  @staticmethod
  def set_value_by_path_id(data:list|tuple|dict, update_values:str|list[str], sep:str = '::') -> list|tuple|dict:
    """Updates the value/s from `update_values` in the `data`.\n
    --------------------------------------------------------------------------------
    Input a list, tuple or dict as `data`, along with `update_values`, which is<br>
    a path-id that was created before using `Object.get_path_id()`, together<br>
    with the new value to be inserted where the path-id points to. The path-id<br>
    and the new value are separated by `sep`, which per default is `::`.\n
    --------------------------------------------------------------------------------
    The value from path-id will be changed to the new value, as long as the<br>
    structure of `data` hasn't changed since creating the path-id to that value."""
    def update_nested(data:list|tuple|dict, path:list[int], value:any) -> list|tuple|dict:
      if len(path) == 1:
        if isinstance(data, dict):
          keys = list(data.keys())
          data[keys[path[0]]] = value
        elif isinstance(data, (list, tuple)):
          data = list(data)
          data[path[0]] = value
          data = type(data)(data)
      elif isinstance(data, dict):
        keys = list(data.keys())
        key = keys[path[0]]
        data[key] = update_nested(data[key], path[1:], value)
      elif isinstance(data, (list, tuple)):
        data = list(data)
        data[path[0]] = update_nested(data[path[0]], path[1:], value)
        data = type(data)(data)
      return data
    if isinstance(update_values, str): update_values = [update_values]
    valid_entries = [(parts[0].strip(), parts[1]) for update_value in update_values
      if len(parts := update_value.split(str(sep).strip())) == 2]
    if not valid_entries: raise ValueError(f'No valid update_values found: {update_values}')
    path, new_values = (zip(*valid_entries) if valid_entries else ([], []))
    for path_id, new_val in zip(path, new_values):
      path = Data._sep_path_id(path_id)
      data = update_nested(data, path, new_val)
    return data

  @staticmethod
  def print(data:list|tuple|dict, indent:int = 2, compactness:int = 1, sep:str = ', ', max_width:int = 140, as_json:bool = False, end:str = '\n') -> None:
    """Print nicely formatted data structures.\n
    ------------------------------------------------------------------------------------
    The indentation spaces-amount can be set with with `indent`.<br>
    There are three different levels of `compactness`:<br>
    `0` expands everything possible<br>
    `1` only expands if there's other lists, tuples or dicts inside of data or,<br>
     ⠀if the data's content is longer than `max_width`<br>
    `2` keeps everything collapsed (all on one line)\n
    ------------------------------------------------------------------------------------
    If `as_json` is set to `True`, the output will be in valid JSON format."""
    print(Data.to_str(data, indent, compactness, sep, max_width, as_json), end=end, flush=True)

  @staticmethod
  def to_str(data:list|tuple|dict, indent:int = 2, compactness:int = 1, sep:str = ', ', max_width:int = 140, as_json:bool = False) -> str:
    """Get nicely formatted data structure-strings.\n
    ------------------------------------------------------------------------------------
    The indentation spaces-amount can be set with with `indent`.<br>
    There are three different levels of `compactness`:<br>
    `0` expands everything possible<br>
    `1` only expands if there's other lists, tuples or dicts inside of data or,<br>
     ⠀if the data's content is longer than `max_width`<br>
    `2` keeps everything collapsed (all on one line)\n
    ------------------------------------------------------------------------------------
    If `as_json` is set to `True`, the output will be in valid JSON format."""
    def escape_string(s:str, str_quotes:str = '"') -> str:
      s = s.replace('\\', r'\\').replace('\n', r'\n').replace('\r', r'\r').replace('\t', r'\t').replace('\b', r'\b').replace('\f', r'\f').replace('\a', r'\a')
      if str_quotes == '"': s = s.replace(r"\\'", "'").replace(r'"', r'\"')
      if str_quotes == "'": s = s.replace(r'\\"', '"').replace(r"'", r"\'")
      return s
    def format_value(value:any, current_indent:int) -> str:
      if isinstance(value, dict): return format_dict(value, current_indent + indent)
      elif hasattr(value, '__dict__'): return format_dict(value.__dict__, current_indent + indent)
      elif isinstance(value, (list, tuple, set, frozenset)): return format_sequence(value, current_indent + indent)
      elif isinstance(value, bool): return str(value).lower() if as_json else str(value)
      elif isinstance(value, (int, float)): return 'null' if as_json and (_math.isinf(value) or _math.isnan(value)) else str(value)
      elif isinstance(value, complex): return f'[{value.real}, {value.imag}]' if as_json else str(value)
      elif value is None: return 'null' if as_json else 'None'
      else: return '"' + escape_string(str(value), '"') + '"' if as_json else "'" + escape_string(str(value), "'") + "'"
    def should_expand(seq:list|tuple|dict) -> bool:
      if compactness == 0: return True
      if compactness == 2: return False
      complex_items = sum(1 for item in seq if isinstance(item, (list, tuple, dict, set, frozenset)))
      return complex_items > 1 or (complex_items == 1 and len(seq) > 1) or Data.chars_count(seq) + (len(seq) * len(sep)) > max_width
    def format_key(k:any) -> str: return '"' + escape_string(str(k), '"') + '"' if as_json else "'" + escape_string(str(k), "'") + "'" if isinstance(k, str) else str(k)
    def format_dict(d:dict, current_indent:int) -> str:
      if not d or compactness == 2: return '{' + sep.join(f'{format_key(k)}: {format_value(v, current_indent)}' for k, v in d.items()) + '}'
      if not should_expand(d.values()): return '{' + sep.join(f'{format_key(k)}: {format_value(v, current_indent)}' for k, v in d.items()) + '}'
      items = []
      for key, value in d.items():
        formatted_value = format_value(value, current_indent)
        items.append(f'{" " * (current_indent + indent)}{format_key(key)}: {formatted_value}')
      return '{\n' + ',\n'.join(items) + f'\n{" " * current_indent}}}'
    def format_sequence(seq, current_indent:int) -> str:
      if as_json: seq = list(seq)
      if not seq or compactness == 2: return '[' + sep.join(format_value(item, current_indent) for item in seq) + ']' if isinstance(seq, list) else '(' + sep.join(format_value(item, current_indent) for item in seq) + ')'
      if not should_expand(seq): return '[' + sep.join(format_value(item, current_indent) for item in seq) + ']' if isinstance(seq, list) else '(' + sep.join(format_value(item, current_indent) for item in seq) + ')'
      items = [format_value(item, current_indent) for item in seq]
      formatted_items = ',\n'.join(f'{" " * (current_indent + indent)}{item}' for item in items)
      if isinstance(seq, list): return '[\n' + formatted_items + f'\n{" " * current_indent}]'
      else: return '(\n' + formatted_items + f'\n{" " * current_indent})'
    return format_dict(data, 0) if isinstance(data, dict) else format_sequence(data, 0)

  @staticmethod
  def _is_key(data:list|tuple|dict, path_id:str) -> bool:
    """Returns `True` if the path-id points to a key in `data` and `False` otherwise.\n
    ------------------------------------------------------------------------------------
    Input a list, tuple or dict as `data`, along with `path_id`, which is a path-id<br>
    that was created before using `Object.get_path_id()`."""
    def check_nested(data:list|tuple|dict, path:list[int]) -> bool:
      for i, idx in enumerate(path):
        if isinstance(data, dict):
          keys = list(data.keys())
          if i == len(path) - 1:
            return True
          data = data[keys[idx]]
        elif isinstance(data, (list, tuple)):
          return False
        else:
          raise TypeError(f'Unsupported type {type(data)} at path {path[:i+1]}')
      return False
    if isinstance(data, (list, tuple)):
      return False
    path = Data._sep_path_id(path_id)
    return check_nested(data, path)

  @staticmethod
  def _sep_path_id(path_id:str) -> list[int]:
    if path_id.count('>') != 1: raise ValueError(f'Invalid path-id: {path_id}')
    id_part_len, path_ids_str = int(path_id.split('>')[0]), path_id.split('>')[1]
    return [int(path_ids_str[i:i+id_part_len]) for i in range(0, len(path_ids_str), id_part_len)]



################################################## STRING OPERATIONS ##################################################

class String:
  @staticmethod
  def to_type(value: str):
    if value.lower() in ['true', 'false']: return value.lower() == 'true'  # BOOLEAN
    if value.lower() in ['none', 'null', 'undefined']: return None  # NONE
    if value.startswith('[') and value.endswith(']'): return [String.to_type(item.strip()) for item in value[1:-1].split(',') if item.strip()]  # LIST
    if value.startswith('(') and value.endswith(')'): return tuple(String.to_type(item.strip()) for item in value[1:-1].split(',') if item.strip())  # TUPLE
    if value.startswith('{') and value.endswith('}'): return {String.to_type(item.strip()) for item in value[1:-1].split(',') if item.strip()}  # SET
    if value.startswith('{') and value.endswith('}') and ':' in value: return {String.to_type(k.strip()): String.to_type(v.strip()) for k, v in [item.split(':') for item in value[1:-1].split(',') if item.strip()]}  # DICT
    try:  # NUMBER (INT OR FLOAT)
      if '.' in value or 'e' in value.lower(): return float(value)
      else: return int(value)
    except ValueError: pass
    if value.startswith(("'", '"')) and value.endswith(("'", '"')): return value[1:-1]  # STRING (WITH OR WITHOUT QUOTES)
    try: return complex(value)  # COMPLEX
    except ValueError: pass
    return value  # IF NOTHING ELSE MATCHES, RETURN AS IS

  @staticmethod
  def get_repeated_symbol(string:str, symbol:str) -> int|bool:
    if len(string) == len(symbol) * string.count(symbol): return string.count(symbol)
    else: return False

  @staticmethod
  def decompose(case_string:str, seps:str = '-_') -> list:
    return [part.lower() for part in _re.split(rf'(?<=[a-z])(?=[A-Z])|[{seps}]', case_string)]

  @staticmethod
  def to_camel_case(string:str) -> str:
    return ''.join(part.capitalize() for part in String.decompose(string))

  @staticmethod
  def to_snake_case(string:str, sep:str = '_', screaming:bool = False) -> str:
    return sep.join(part.upper() if screaming else part for part in String.decompose(string))

  @staticmethod
  def get_string_lines(string:str, remove_empty_lines:bool = False) -> list:
    if not remove_empty_lines: return string.splitlines()
    lines = string.splitlines()
    if not lines: return []
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines: return []
    return non_empty_lines

  @staticmethod
  def remove_consecutive_empty_lines(string:str, max_consecutive:int = 0) -> str:
    return _re.sub(r'(\n\s*){2,}', r'\1' * (max_consecutive + 1), string)

  @staticmethod
  def multi_strip(string:str, strip_chars:str = ' _-') -> str:
    for char in string:
      if char in strip_chars: string = string[1:]
      else: break
    for char in string[::-1]:
      if char in strip_chars: string = string[:-1]
      else: break
    return string

  @staticmethod
  def multi_lstrip(string:str, strip_chars:str = ' _-') -> str:
    for char in string:
      if char in strip_chars: string = string[1:]
      else: break
    return string

  @staticmethod
  def multi_rstrip(string:str, strip_chars:str = ' _-') -> str:
    for char in string[::-1]:
      if char in strip_chars: string = string[:-1]
      else: break
    return string



################################################## CODE-STRING OPERATIONS ##################################################

class Code:
  @staticmethod
  def add_indent(code:str, indent:int) -> str:
    indented_lines = [' ' * indent + line for line in code.splitlines()]
    return '\n'.join(indented_lines)

  @staticmethod
  def get_tab_spaces(code:str) -> int:
    code_lines = String.get_string_lines(code, remove_empty_lines=True)
    indents = [len(line) - len(line.lstrip()) for line in code_lines]
    non_zero_indents = [i for i in indents if i > 0]
    return min(non_zero_indents) if non_zero_indents else 0

  @staticmethod
  def change_tab_size(code:str, new_tab_size:int, remove_empty_lines:bool = False) -> str:
    code_lines = String.get_string_lines(code, remove_empty_lines=True)
    lines = code_lines if remove_empty_lines else String.get_string_lines(code)
    tab_spaces = Code.get_tab_spaces(code)
    if (tab_spaces == new_tab_size) or tab_spaces == 0:
      if remove_empty_lines: return '\n'.join(code_lines)
      return code
    result = []
    for line in lines:
      stripped = line.lstrip()
      indent_level = (len(line) - len(stripped)) // tab_spaces
      new_indent = ' ' * (indent_level * new_tab_size)
      result.append(new_indent + stripped)
    return '\n'.join(result)

  @staticmethod
  def get_func_calls(code:str) -> list:
    funcs, nested_func_calls = _regex.findall(r'(?i)' + Regex.func_call(), code), []
    for _, func_attrs in funcs:
      nested_calls = _regex.findall(r'(?i)' + Regex.func_call(), func_attrs)
      if nested_calls: nested_func_calls.extend(nested_calls)
    return Data.remove_duplicates(funcs + nested_func_calls)

  @staticmethod
  def is_js(code:str, funcs:list = ['__', '$t', '$lang']) -> bool:
    funcs = '|'.join(funcs)
    js_pattern = _regex.compile(Regex.outside_strings(r'''^(?:
      (\$[\w_]+)\s*                      # JQUERY-STYLE VARIABLES
      |(\$[\w_]+\s*\()                   # JQUERY-STYLE FUNCTION CALLS
      |((''' + funcs + r')' + Regex.brackets('()') + r'''\s*) # PREDEFINED FUNCTION CALLS
      |(\bfunction\s*\()                 # FUNCTION DECLARATIONS
      |(\b(var|let|const)\s+[\w_]+\s*=)  # VARIABLE DECLARATIONS
      |(\b(if|for|while|switch)\s*\()    # CONTROL STRUCTURES
      |(\b(return|throw)\s+)             # RETURN OR THROW STATEMENTS
      |(\bnew\s+[\w_]+\()                # OBJECT INSTANTIATION
      |(\b[\w_]+\s*=>\s*{)               # ARROW FUNCTIONS
      |(\b(true|false|null|undefined)\b) # JAVASCRIPT LITERALS
      |(\b(document|window|console)\.)   # BROWSER OBJECTS
      |(\b[\w_]+\.(forEach|map|filter|reduce)\() # ARRAY METHODS
      |(/[^/\n\r]*?/[gimsuy]*)           # REGULAR EXPRESSIONS
      |(===|!==|\+\+|--|\|\||&&)         # JAVASCRIPT-SPECIFIC OPERATORS
      |(\bclass\s+[\w_]+)                # CLASS DECLARATIONS
      |(\bimport\s+.*?from\s+)           # IMPORT STATEMENTS
      |(\bexport\s+(default\s+)?)        # EXPORT STATEMENTS
      |(\basync\s+function)              # ASYNC FUNCTIONS
      |(\bawait\s+)                      # AWAIT KEYWORD
      |(\btry\s*{)                       # TRY-CATCH BLOCKS
      |(\bcatch\s*\()
      |(\bfinally\s*{)
      |(\byield\s+)                      # GENERATOR FUNCTIONS
      |(\[.*?\]\s*=)                     # DESTRUCTURING ASSIGNMENT
      |(\.\.\.)                          # SPREAD OPERATOR
      |(==|!=|>=|<=|>|<)                 # COMPARISON OPERATORS
      |(\+=|-=|\*=|/=|%=|\*\*=)          # COMPOUND ASSIGNMENT OPERATORS
      |(\+|-|\*|/|%|\*\*)                # ARITHMETIC OPERATORS
      |(&|\||\^|~|<<|>>|>>>)             # BITWISE OPERATORS
      |(\?|:)                            # TERNARY OPERATOR
      |(\bin\b)                          # IN OPERATOR
      |(\binstanceof\b)                  # INSTANCEOF OPERATOR
      |(\bdelete\b)                      # DELETE OPERATOR
      |(\btypeof\b)                      # TYPEOF OPERATOR
      |(\bvoid\b)                        # VOID OPERATOR
    )[\s\S]*$'''), _regex.VERBOSE | _regex.IGNORECASE)
    return bool(js_pattern.fullmatch(code))



################################################## REGEX STRING-TEMPLATES ##################################################

class Regex:
  """Big regex code presets.\n
  -----------------------------------------------------
  `brackets` match everything inside brackets<br>
  `outside_strings` match the pattern but not inside strings<br>
  `all_except` match everything except a certain pattern<br>
  `func_call` match a function call
  """

  @staticmethod
  def quotes() -> str:
    """Match everything inside quotes. (Strings)\n
    ------------------------------------------------------------------------------------
    Will create two named groups:<br>
    **`quote`** the quote type (single or double)<br>
    **`string`** everything inside the found quote pair\n
    ------------------------------------------------------------------------------------
    **Attention:** Requires non standard library `regex` not standard library `re`!"""
    return r'(?P<quote>[\'"])(?P<string>(?:\\.|(?!\g<quote>).)*?)\g<quote>'

  @staticmethod
  def brackets(bracket1:str = '(', bracket2:str = ')', is_group:bool = False) -> str:
    """Match everything inside brackets, including other nested brackets.\n
    ------------------------------------------------------------------------------------
    **Attention:** Requires non standard library `regex` not standard library `re`!"""
    g, b1, b2 = '' if is_group else '?:', _re.escape(bracket1) if len(bracket1) == 1 else bracket1, _re.escape(bracket2) if len(bracket2) == 1 else bracket2
    return rf'{b1}\s*({g}(?:[^{b1}{b2}"\']|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|{b1}(?:[^{b1}{b2}"\']|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|(?R))*{b2})*)\s*{b2}'

  @staticmethod
  def outside_strings(pattern:str = r'.*') -> str:
    """Match the `pattern` only when it is not found inside a string (`'...'` or `"..."`)."""
    return rf'(?<!["\'])(?:{pattern})(?!["\'])'

  @staticmethod
  def all_except(disallowed_pattern:str, ignore_pattern:str = '', is_group:bool = False) -> str:
    """Match everything except `disallowed_pattern`, unless the `disallowed_pattern` is found inside a string (`'...'` or `"..."`).\n
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    The `ignore_pattern` is just always ignored. For example if `disallowed_pattern` is `>` and `ignore_pattern` is `->`, the `->`-arrows will be allowed, even though they have `>` in them.<br>
    If `is_group` is `True`, you will be able to reference the matched content as a group (e.g. <code>match.group(<i>int</i>)</code> or <code>r'\\<i>int</i>'</code>)."""
    return rf'({"" if is_group else "?:"}(?:(?!{ignore_pattern}).)*(?:(?!{Regex.outside_strings(disallowed_pattern)}).)*)'

  @staticmethod
  def func_call(func_name:str = None) -> str:
    """Match a function call<br>
    **`1`** function name<br>
    **`2`** the function's arguments\n
    If no `func_name` is given, it will match any function call.\n
    ------------------------------------------------------------------------------------
    **Attention:** Requires non standard library `regex` not standard library `re`!"""
    return r'(?<=\b)(' + (func_name if func_name else r'[\w_]+') + r')\s*' + Regex.brackets("(", ")", is_group=True)

  @staticmethod
  def rgb_str(fix_sep:str = ',', allow_alpha:bool = False) -> str:
    """Match an RGB color inside a string.\n
    ---------------------------------------------------------------------------------
    The RGB color can be in the formats (for `fix_sep = ','`):<br>
    `rgb(r, g, b)`<br>
    `rgb(r, g, b, a)` (if `allow_alpha = True`)<br>
    `(r, g, b)`<br>
    `(r, g, b, a)` (if `allow_alpha = True`)<br>
    `r, g, b`<br>
    `r, g, b, a` (if `allow_alpha = True`)\n
    ---------------------------------------------------------------------------------
    If the `fix_sep` is set to nothing, and char which is not a letter or number<br>
    can be used to separate the RGB values, including just a space."""
    if fix_sep in ['', None]: fix_sep = r'[^0-9A-Z]'
    else: fix_sep = _re.escape(fix_sep)
    rgb_part = rf'''((?:0*(?:25[0-5]|2[0-4][0-9]|1?[0-9]{{1,2}})))
      (?:\s*{fix_sep}\s*)((?:0*(?:25[0-5]|2[0-4][0-9]|1?[0-9]{{1,2}})))
      (?:\s*{fix_sep}\s*)((?:0*(?:25[0-5]|2[0-4][0-9]|1?[0-9]{{1,2}})))'''
    return rf'''(?ix)
      (?:rgb)?\s*(?:\(?\s*{rgb_part}
        (?:(?:\s*{fix_sep}\s*)((?:0*(?:0?\.[0-9]+|1\.0+|[0-9]+\.[0-9]+|[0-9]+))))?
      \s*\)?)''' if allow_alpha else rf'(?ix)(?:rgb)?\s*(?:\(?\s*{rgb_part}\s*\)?)'



################################################## LIBRARY DESCRIPTION ##################################################

if __name__ == '__main__':
  FormatCodes.print(
  rf'''  [_|b|#7075FF]               __  __              
  [b|#7075FF]  _  __ __  __/ / / /_  __  ___  __
  [b|#7075FF] | |/ // / / / / / __ \/ / / | |/ /
  [b|#7075FF] > , </ /_/ / /_/ /_/ / /_/ /> , < 
  [b|#7075FF]/_/|_|\____/\__/\____/\____//_/|_|  [*|BG:#7B7C8F|#000] v[b]{__version__} [*]

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
  [_]''', '#809FFF')
  Cmd.pause_exit(pause=True)
