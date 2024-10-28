class DEFAULT:
  hex_type = int
  text_color:int = 0x95B5FF
  color:dict = {
    'white':       0xF1F1FF,
    'lightgray':   0xB6B6C0,
    'darkgray':    0x67676C,
    'black':       0x202025,
    'red':         0xFF606A,
    'coral':       0xFF7069,
    'orange':      0xFF876A,
    'lightorange': 0xFF9962,
    'gold':        0xFFAF60,
    'yellow':      0xFFD260,
    'green':       0x7EE787,
    'teal':        0x50EAAF,
    'cyan':        0x3EE6DE,
    'lightblue':   0x60AAFF,
    'blue':        0x7075FF,
    'purple':      0xAA90FF,
    'magenta':     0xC860FF,
    'pink':        0xEE60BB,
    'rose':        0xFF6090,
  }


class ANSI:
  prefix:str = '\033['
  color_map:list[str] = [
    ########### DEFAULT CONSOLE COLOR NAMES ############
      'black',
      'red',
      'green',
      'yellow',
      'blue',
      'magenta',
      'cyan',
      'white'
    ]
  codes_map:dict = {
    ###################### RESETS ######################
      '_':                         '0m',
      ('_bold','_b'):              '22m',
      ('_dim','_d'):               '22m',
      ('_italic','_i'):            '23m',
      ('_underline','_u'):         '24m',
      ('_double-underline','_du'): '24m',
      ('_inverse','_in'):          '27m',
      ('_hidden','_h'):            '28m',
      ('_strikethrough','_s'):     '29m',
      ('_color','_c'):             '39m',
      ('_background','_bg'):       '49m',
    ################### TEXT FORMATS ###################
      ('bold','b'):              '1m',
      ('dim','d'):               '2m',
      ('italic','i'):            '3m',
      ('underline','u'):         '4m',
      ('inverse','in'):          '7m',
      ('hidden','h'):            '8m',
      ('strikethrough','s'):     '9m',
      ('double-underline','du'): '21m',
    ############## DEFAULT CONSOLE COLORS ##############
      'black':   '30m',
      'red':     '31m',
      'green':   '32m',
      'yellow':  '33m',
      'blue':    '34m',
      'magenta': '35m',
      'cyan':    '36m',
      'white':   '37m',
    ########## BRIGHT DEFAULT CONSOLE COLORS ###########
      ('bright:black','br:black'):     '90m',
      ('bright:red','br:red'):         '91m',
      ('bright:green','br:green'):     '92m',
      ('bright:yellow','br:yellow'):   '93m',
      ('bright:blue','br:blue'):       '94m',
      ('bright:magenta','br:magenta'): '95m',
      ('bright:cyan','br:cyan'):       '96m',
      ('bright:white','br:white'):     '97m',
    ######## DEFAULT CONSOLE BACKGROUND COLORS #########
      'bg:black':   '40m',
      'bg:red':     '41m',
      'bg:green':   '42m',
      'bg:yellow':  '43m',
      'bg:blue':    '44m',
      'bg:magenta': '45m',
      'bg:cyan':    '46m',
      'bg:white':   '47m',
    ##### BRIGHT DEFAULT CONSOLE BACKGROUND COLORS #####
      ('bg:bright:black','bg:br:black'):     '100m',
      ('bg:bright:red','bg:br:red'):         '101m',
      ('bg:bright:green','bg:br:green'):     '102m',
      ('bg:bright:yellow','bg:br:yellow'):   '103m',
      ('bg:bright:blue','bg:br:blue'):       '104m',
      ('bg:bright:magenta','bg:br:magenta'): '105m',
      ('bg:bright:cyan','bg:br:cyan'):       '106m',
      ('bg:bright:white','bg:br:white'):     '107m',
    }
