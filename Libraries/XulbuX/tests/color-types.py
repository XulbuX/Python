import XulbuX as xx
from XulbuX import rgba, hexa, hsla



def test_all_methods(instance, instance_name):
  print(f'\n--- Testing methods on {instance_name} ({instance}) ---')
  methods = [func for func in dir(instance) if callable(getattr(instance, func)) and not func.startswith('_')]
  for method in methods:
    func = getattr(instance, method)
    try:
      result = func()
      print(f'{method}() -> {result}')
    except TypeError:
      try:
        if 'blend' in method: result = func(instance, 0.5)
        else: result = func(0.1)
        xx.FormatCodes.print(f'{method}(0.1 or blend arg) -> [{result}]{result}[_]')
      except Exception as e:
        xx.FormatCodes.print(f'{method} failed with error: {e}')



rgba_instance = rgba(255, 0, 0, 0.5)
hexa_instance = hexa('#FF00007D')
hsla_instance = hsla(0, 50, 100)

test_all_methods(rgba_instance, 'rgba')
test_all_methods(hexa_instance, 'hexa')
test_all_methods(hsla_instance, 'hsla')