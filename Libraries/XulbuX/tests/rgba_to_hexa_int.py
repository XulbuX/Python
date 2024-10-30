def rgba_to_hex(r:int, g:int, b:int, a:float = None, _preserve_original:bool = False) -> int:
    """Convert RGBA channels to a HEXA integer (alpha is optional).\n
    -------------------------------------------------------------------------------------------------------------------------
    To preserve leading zeros, the function will add a `1` at the beginning, if the HEX value would start with a `0`.<br>
    This could affect the color a little bit, but will make sure, that it won't be interpreted as a completely different<br>
    color, when initializing it as a `hexa()` color or changing it back to RGBA using `Color.hex_to_rgba()`.\n
    ⇾ **You can disable this behavior by setting `_preserve_original` to `True`**"""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    if a is not None:
        if isinstance(a, float):
            a = int(a * 255)
        a = max(0, min(255, int(a)))
        hex_int = (r << 24) | (g << 16) | (b << 8) | a
        if not _preserve_original and r == 0:
            hex_int |= 0x01000000
    else:
        hex_int = (r << 16) | (g << 8) | b
        if not _preserve_original and (hex_int & 0xF00000) == 0:
            hex_int |= 0x010000
    return hex_int

def hex_to_rgba(hex_int:int) -> tuple[int,int,int,float|int|None]:
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
        rgba = input('RGBA: ').split(',')
        if len(rgba) == 4:
            r, g, b = [int(x.strip()) for x in rgba[:3]]
            a = float(rgba[3].strip())
            hexa = rgba_to_hex(r, g, b, a)
        else:
            rgba = [int(x.strip()) for x in rgba]
            hexa = rgba_to_hex(*rgba)
        print(f'OUT: {hex(hexa)} = {hex_to_rgba(hexa)}')
    except ValueError as e:
        print('ERR:', e)
