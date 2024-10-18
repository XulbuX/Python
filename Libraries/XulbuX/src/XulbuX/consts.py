ANSI_PREF = '\033['
CODES_MAP = {
  '_':'0m', ('_bold', '_b'):'22m', '_dim':'22m', ('_italic', '_i'):'23m', ('_underline', '_u'):'24m', ('_double-underline', '_du'):'24m', ('_inverse', '_in'):'27m', ('_hidden', '_h'):'28m', ('_strikethrough', '_s'):'29m', ('_color', '_c'):'39m', ('_background', '_bg'):'49m',
  ('bold', 'b'):'1m', 'dim':'2m', ('italic', 'i'):'3m', ('underline', 'u'):'4m', ('inverse', 'in'):'7m', ('hidden', 'h'):'8m', ('strikethrough', 's'):'9m', ('double-underline', 'du'):'21m',
  'black':'30m', 'red':'31m', 'green':'32m', 'yellow':'33m', 'blue':'34m', 'magenta':'35m', 'cyan':'36m', 'white':'37m',
  ('bright:black', 'br:black'):'90m', ('bright:red', 'br:red'):'91m', ('bright:green', 'br:green'):'92m', ('bright:yellow', 'br:yellow'):'93m', ('bright:blue', 'br:blue'):'94m', ('bright:magenta', 'br:magenta'):'95m', ('bright:cyan', 'br:cyan'):'96m', ('bright:white', 'br:white'):'97m',
  'bg:black':'40m', 'bg:red':'41m', 'bg:green':'42m', 'bg:yellow':'43m', 'bg:blue':'44m', 'bg:magenta':'45m', 'bg:cyan':'46m', 'bg:white':'47m',
  ('bg:bright:black', 'bg:br:black'):'100m', ('bg:bright:red', 'bg:br:red'):'101m', ('bg:bright:green', 'bg:br:green'):'102m', ('bg:bright:yellow', 'bg:br:yellow'):'103m', ('bg:bright:blue', 'bg:br:blue'):'104m', ('bg:bright:magenta', 'bg:br:magenta'):'105m', ('bg:bright:cyan', 'bg:br:cyan'):'106m', ('bg:bright:white', 'bg:br:white'):'107m',
}
COLOR_MAP = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
CHARS_MAP = {
  'nums': '0123456789',
  'letters': 'abcdefghijklmnopqrstuvwxyz',
  'ascii': '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|\\:;\"\'<>?,./`~',
}