import XulbuX as xx
import os


if __name__ == '__main__':
    print(xx.Cmd.user())
    print(f'W: {xx.Cmd.w()}, H: {xx.Cmd.h()}')
    print('#' * xx.Cmd.w(), flush=True)
