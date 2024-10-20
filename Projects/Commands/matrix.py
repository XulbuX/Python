import XulbuX as xx
import random
import time
import sys

ARGS = sys.argv[1:]
x = ['0', '1']
f = ['dim', 'bold', 'inverse', 'underline', 'strikethrough', 'double-underline']
if ARGS and (ARGS.__contains__('-c') or ARGS.__contains__('--color')):
  f.extend([
    'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
    'bright:black', 'bright:red', 'bright:green', 'bright:yellow', 'bright:blue', 'bright:magenta', 'bright:cyan', 'bright:white',
    'BG:black', 'BG:red', 'BG:green', 'BG:yellow', 'BG:blue', 'BG:magenta', 'BG:cyan', 'BG:white',
    'BG:bright:black', 'BG:bright:red', 'BG:bright:green', 'BG:bright:yellow', 'BG:bright:blue', 'BG:bright:magenta', 'BG:bright:cyan', 'BG:bright:white',
    'random', 'randomBG'
  ])


def random_rgb() -> str:
  return f'#{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}'

def replace_special(text:str) -> str:
  return text.replace('random', random_rgb()).replace('randomBG', f'BG:({random_rgb()})')


try:
  while True:
    line = ''.join(
      (f'[{replace_special(random.choice(f))}]' if random.randint(0, 1) == 1 else '') +
      (random.choice(x) if random.randint(0, 1) == 1 else ' ') +
      '[_]' for _ in range(100))
    xx.FormatCodes.print(line)
    if not (ARGS.__contains__('-s') or ARGS.__contains__('--speed') or ARGS.__contains__('-f') or ARGS.__contains__('--fast')): time.sleep(0.025)
except KeyboardInterrupt:
  print()
