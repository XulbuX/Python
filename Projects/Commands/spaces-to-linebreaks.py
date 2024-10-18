import XulbuX as xx

lst = input('>  ').split()
xx.FormatCodes.print(f'\n[bright:cyan]{'\n'.join(lst)}[_]\n')


def check_all(lst, condition):
  return all(eval(f'lambda x: {condition}')(x) for x in lst)

if check_all(lst, 'x.isnumeric()'):
  lst = [int(x) for x in lst]
  average = lambda nums: sum(nums) / len(nums)
  print(average(lst))

