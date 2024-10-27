try: from .String import *
except: from String import *
try: from .Regex import *
except: from Regex import *
try: from .Data import *
except: from Data import *

import regex as _regex



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
