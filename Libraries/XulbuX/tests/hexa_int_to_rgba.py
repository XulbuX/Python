def hexa_int_to_rgba(hex_int:int) -> tuple[int,int,int,float|int|None]:
  if not isinstance(hex_int, int):
    raise ValueError('Input must be an integer (hex value)')
  if hex_int < 0xF:
    raise ValueError(f"Invalid HEX color integer format '0x{hex_int:x}'")
  elif hex_int <= 0xFFF:
    hex_str = f'{hex_int:03x}'
  elif hex_int <= 0xFFFF:
    hex_str = f'{hex_int:04x}'
  elif hex_int <= 0xFFFFFF:
    hex_str = f'{hex_int:06x}'
  elif hex_int <= 0xFFFFFFFF:
    hex_str = f'{hex_int:08x}'
  else:
    raise ValueError(f"Invalid HEX color integer format '0x{hex_int:x}'")
  if len(hex_str) <= 4:
    hex_str = ''.join(c + c for c in hex_str)
  r = int(hex_str[0:2], 16)
  g = int(hex_str[2:4], 16)
  b = int(hex_str[4:6], 16)
  a = None if len(hex_str) == 6 else int(hex_str[6:8], 16) / 255.0
  return r, g, b, a

try: print('1', hexa_int_to_rgba(0x0))  # invalid
except ValueError as e: print('1', e)
try: print('2', hexa_int_to_rgba(0x0F))  # invalid
except ValueError as e: print('2', e)
try: print('3', hexa_int_to_rgba(0x00F))  # (R, G, B, None)
except ValueError as e: print('3', e)
try: print('4', hexa_int_to_rgba(0x00FF))  # (R, G, B, A)
except ValueError as e: print('4', e)
try: print('5', hexa_int_to_rgba(0x000FF))  # invalid
except ValueError as e: print('5', e)
try: print('6', hexa_int_to_rgba(0x0000FF))  # (R, G, B, None)
except ValueError as e: print('6', e)
try: print('7', hexa_int_to_rgba(0x0000FFF))  # invalid
except ValueError as e: print('7', e)
try: print('8', hexa_int_to_rgba(0x0000FFFF))  # (R, G, B, A)
except ValueError as e: print('8', e)
