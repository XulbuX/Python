# x-convert
The goal of this file is to run it as a command inside the console.

The program is used to convert one type of code into another type of code. Currently, it supports the following conversions:
* `Laravel Blade` to `Vue.js`


## running x-convert for the first time

After you download the file (Python or EXE), you can first run it normally.<br>
If you don't have a `config.json` in the directory you run it in, you will be prompted to create one. (*You have to say* `Yes` *to be able to use it.*)
Then you will be asked if you want to add the base directory to the path. (*Only if you say* `Yes` *you will be able to run it as a command in the console.*)

After you did everything from above, you should be able to execute the command `x-convert` in the console.

## console command

The command to use it with will look something like this:
```gas
x-convert -bv -i <indent after conversion> -f <path to the file to be converted>
```

For example if:
```ps
x-convert -bv -i 2 -f /some/relative/path/to/file.blade.php
```

To see exactly how this command works and some other info, run the command with the `-h` or `--help` option:
```gas
x-convert --help
```
