"""
Really long regex code presets:<br>
`quotes` match everything inside quotes<br>
`brackets` match everything inside brackets<br>
`outside_strings` match the pattern but not inside strings<br>
`all_except` match everything except a certain pattern<br>
`func_call` match a function call<br>
`rgba_str` match an RGBA color<br>
"""


import re as _re



class Regex:
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
  def rgba_str(fix_sep:str = ',', allow_alpha:bool = False) -> str:
    """Match an RGBA color inside a string.\n
    ---------------------------------------------------------------------------------
    The RGBA color can be in the formats (for `fix_sep = ','`):<br>
    `rgb(r, g, b)`<br>
    `rgb(r, g, b, a)` (if `allow_alpha = True`)<br>
    `(r, g, b)`<br>
    `(r, g, b, a)` (if `allow_alpha = True`)<br>
    `r, g, b`<br>
    `r, g, b, a` (if `allow_alpha = True`)\n
    ---------------------------------------------------------------------------------
    If the `fix_sep` is set to nothing, and char which is not a letter or number<br>
    can be used to separate the RGB values, including just a space."""
    if fix_sep in (None, ''): fix_sep = r'[^0-9A-Z]'
    else: fix_sep = _re.escape(fix_sep)
    rgb_part = rf'''((?:0*(?:25[0-5]|2[0-4][0-9]|1?[0-9]{{1,2}})))
      (?:\s*{fix_sep}\s*)((?:0*(?:25[0-5]|2[0-4][0-9]|1?[0-9]{{1,2}})))
      (?:\s*{fix_sep}\s*)((?:0*(?:25[0-5]|2[0-4][0-9]|1?[0-9]{{1,2}})))'''
    return rf'''(?ix)
      (?:rgb)?\s*(?:\(?\s*{rgb_part}
        (?:(?:\s*{fix_sep}\s*)((?:0*(?:0?\.[0-9]+|1\.0+|[0-9]+\.[0-9]+|[0-9]+))))?
      \s*\)?)''' if allow_alpha else rf'(?ix)(?:rgb)?\s*(?:\(?\s*{rgb_part}\s*\)?)'
