class DEFAULT:
    hex_type = int
    text_color:int = 0x95B5FF
    color:dict = {
        'white':       0xF1F2FF,
        'lightgray':   0xB6B7C0,
        'gray':        0x7B7C8D,
        'darkgray':    0x67686C,
        'black':       0x202125,
        'red':         0xFF606A,
        'coral':       0xFF7069,
        'orange':      0xFF876A,
        'tangerine':   0xFF9962,
        'gold':        0xFFAF60,
        'yellow':      0xFFD260,
        'green':       0x7EE787,
        'teal':        0x50EAAF,
        'cyan':        0x3EE6DE,
        'ice':         0x77EFEF,
        'lightblue':   0x60AAFF,
        'blue':        0x8085FF,
        'lavender':    0x9B7DFF,
        'purple':      0xAD68FF,
        'magenta':     0xC860FF,
        'pink':        0xEE60BB,
        'rose':        0xFF6090,
    }


class ANSI:
    global CHAR, START, SEP, END

    CHAR  = char  = '\x1b'
    START = start = '['
    SEP   = sep   = ';'
    END   = end   = 'm'

    def seq(parts:int = 1) -> str:
        return CHAR + START + SEP.join(['{}' for _ in range(parts)]) + END

    seq_color:str = CHAR + START + '38' + SEP + '2' + SEP + '{}' + SEP + '{}' + SEP + '{}' + END
    seq_bg_color:str = CHAR + START + '48' + SEP + '2' + SEP + '{}' + SEP + '{}' + SEP + '{}' + END

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
        '_':                         0,
        ('_bold','_b'):              22,
        ('_dim','_d'):               22,
        ('_italic','_i'):            23,
        ('_underline','_u'):         24,
        ('_double-underline','_du'): 24,
        ('_inverse','_in'):          27,
        ('_hidden','_h'):            28,
        ('_strikethrough','_s'):     29,
        ('_color','_c'):             39,
        ('_background','_bg'):       49,
        ################### TEXT FORMATS ###################
        ('bold','b'):              1,
        ('dim','d'):               2,
        ('italic','i'):            3,
        ('underline','u'):         4,
        ('inverse','in'):          7,
        ('hidden','h'):            8,
        ('strikethrough','s'):     9,
        ('double-underline','du'): 21,
        ############## DEFAULT CONSOLE COLORS ##############
        'black':   30,
        'red':     31,
        'green':   32,
        'yellow':  33,
        'blue':    34,
        'magenta': 35,
        'cyan':    36,
        'white':   37,
        ########## BRIGHT DEFAULT CONSOLE COLORS ###########
        ('bright:black','br:black'):     90,
        ('bright:red','br:red'):         91,
        ('bright:green','br:green'):     92,
        ('bright:yellow','br:yellow'):   93,
        ('bright:blue','br:blue'):       94,
        ('bright:magenta','br:magenta'): 95,
        ('bright:cyan','br:cyan'):       96,
        ('bright:white','br:white'):     97,
        ######## DEFAULT CONSOLE BACKGROUND COLORS #########
        'bg:black':   40,
        'bg:red':     41,
        'bg:green':   42,
        'bg:yellow':  43,
        'bg:blue':    44,
        'bg:magenta': 45,
        'bg:cyan':    46,
        'bg:white':   47,
        ##### BRIGHT DEFAULT CONSOLE BACKGROUND COLORS #####
        ('bg:bright:black','bg:br:black'):     100,
        ('bg:bright:red','bg:br:red'):         101,
        ('bg:bright:green','bg:br:green'):     102,
        ('bg:bright:yellow','bg:br:yellow'):   103,
        ('bg:bright:blue','bg:br:blue'):       104,
        ('bg:bright:magenta','bg:br:magenta'): 105,
        ('bg:bright:cyan','bg:br:cyan'):       106,
        ('bg:bright:white','bg:br:white'):     107,
    }
