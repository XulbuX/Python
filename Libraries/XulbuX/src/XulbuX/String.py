import re as _re



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
