def hexa_int_to_rgba(hex_int:int) -> tuple[int,int,int,float|int|None]:
  if not isinstance(hex_int, int):
    raise ValueError('Input must be an integer (hex value)')
  hex_str = f'{hex_int:x}'
  if len(hex_str) <= 6:
    hex_str = hex_str.zfill(6)
    return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), None
  elif len(hex_str) <= 8:
    hex_str = hex_str.zfill(8)
    return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16) / 255.0
  else:
    raise ValueError(f"Invalid HEX integer '0x{hex_str}': expected in range [0x000000, 0xFFFFFF]")

while True:
  try:
    print('OUT:', hexa_int_to_rgba(int(input('INT: '), 16)))
  except ValueError as e:
    print('ERR:', e)
