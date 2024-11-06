# x-convert
The goal of this file is to be run as a command inside the console.

The program is used to convert one type of code into another type of code. Currently, it supports the following conversions:
* `Laravel Blade` to `Vue.js`

The program will create a new file with the formatted code inside, in the same directory as the file with the old code.


## Running x-convert for the first time

After you download the file (*[Python](./x-convert.py) or [EXE](https://github.com/XulbuX-dev/Python/raw/refs/heads/main/Projects/x-convert/x-convert.exe), it doesn't matter*), you can first run it normally.<br>
If you don't have a `config.json` in the directory you run it in, you will be prompted to create one. (*You have to say* `Yes` *to be able to use it.*)
Then you will be asked if you want to add the base directory to the path. (*Only if you say* `Yes` *you will be able to run it as a command in the console.*)

After you did everything from above, you should be able to run the program with the command `x-convert` in the console.


## Console command

The command to use the converter it with will look something like this:
```gas
x-convert -bv -i <indent after conversion> -f <path to the file to be converted>
```

For example if:
```ps
x-convert -bv -i 2 -f /some/relative/path/to/file.blade.php
```

To see exactly how this program/command works and some other info, run the `x-convert` command with the `-h` or `--help` option:
```ps
x-convert --help
```
