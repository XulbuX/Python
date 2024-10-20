# Custom Commands
This repository contains quite a few Python files, which are supposed to be ran as command in the console and do some usefull stuff.

## Run the files as console commands
To be able to type a one of the files's names in the console and through this run that corresponding file, you have to do a few things:<br>

## What each file (command) does

### _.py
Run with command:
```console
_
```
This is a better version of the `cls` or `clear` command, to clear your console. The command `_` is:<br>
a) faster to type and
b) the command also resets all the console formats.

### lib-publish.py
Run with command:
```console
lib-publish
```
This is just a single command, which runs the two requiered commands, to package and directly upload your own Python library to [PyPi](https://pypi.org/).
### matrix.py
Run with command:
```console
matrix
```
This command will display a sort of matrix in your console with a few options for customizing:
1. By standard, the matrix symbols are not colored. With the option `-c` or `--color` you can make them be in random colors:
   
   ```console
   matrix --color
   ```
3. Normally, the matrix moves rather slow, but with the option `-s`, `--speed`, `-f` or `--fast`, it will move very fast:
   
   ```console
   matrix --fast
   ```
3. You can also make the matrix be in color and move fast, by applying both options:

   ```console
   matrix -c -f
   ```
Can be cancelled by pressing `Ctrl`+`C` or `Cmd ⌘`+`C`.

### sine-wave.py
Run with command:
```console
sine-wave
```
This command will just display a moving sine wave in your console.<br>
Can be cancelled by pressing `Ctrl`+`C` or `Cmd ⌘`+`C`.

### spaces-to-linebreaks.py
Run with command:
```console
spaces-to-linebreaks
```
This command simply lets you input text and will then output that text but go to the next line after every `space` character.

### x-convert.py
Run with command:
```console
x-convert
```
This command is actually a whole program. It is used to convert one type of code into another type of code.<br>
To see exactly how this command works and what types of conversions are currently supported, run the command with the `-h` or `--help` option:
```console
x-convert --help
```

### x-dir-info.py
Run with command:
```console
x-dir-info
```
This command will

### x
Run with command:
```console
x
```
This 

### x
Run with command:
```console
x
```
This 
