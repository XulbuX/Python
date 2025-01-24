# Custom Commands
This repository contains quite a few Python files, which are supposed to be run as commands in the console and do some useful stuff.<br>
[Figure out what each file (*command*) does.](#what-each-cmd-does)


## Run the files as console commands
To be able to type one of the file's names in the console and, through this, run that corresponding file, you need to follow these steps:

1. Download the Python files you want to use as commands.
2. Place all downloaded files in a single directory of your choice.
3. Add the absolute path to that directory to your system's PATH environment variable. This process varies depending on your operating system:

   ### Windows:
   * Press Win + X and select "System".
   * Click on "Advanced System Settings".
   * Click on "Environment Variables".
   * Under "System Variables", find and select "Path", then click "Edit".
   * Click "New" and add the full path to your directory.
   * Click "OK" to close all windows.

   ### macOS and Linux:
   * Open your terminal.
   * Edit your shell configuration file (*e.g.*, `~/.bash_profile`, `~/.bashrc`, *or* `~/.zshrc`) using a text editor.
   * Add the following line at the end of the file, replacing `/path/to/your/directory` with the actual path:
     ```bash
     export PATH="$PATH:/path/to/your/directory"
     ```
   * Save the file and run `source ~/.bash_profile` (*or the appropriate file you edited*) to apply changes.

4. For macOS and Linux, make the files executable:
   ```s
   chmod +x /path/to/your/directory/*.py
   ```
5. Restart your terminal or command prompt for the changes to take effect.

After completing these steps, you should be able to run the commands described below.


## <span id="what-each-cmd-does">What each file (*command*) does</span>


### _.py
Run with command:
```console
_
```
This is a better version of the `cls` or `clear` command to clear your console. The command `_` is:<br>
* Faster to type and
* the command also resets all the console formats.


### capitalize-hex.py
Run with command:
```console
capitalize-hex
```
This command will capitalize all found HEX colors in the given file or directory.

The path to the file or directory containing files can be directly given as an argument:
```console
capitalize-hex /path/to/file
```
```console
capitalize-hex /path/to/directory
```


### code-extensions.py
Run with command:
```console
code-extensions
```
This command will output info about all installed Visual Studio Code extensions:
1. the installed extensions count
2. a list of all installed extensions

You can also output the list of installed extensions, formatted as a JSON array, with the `-j` or `--json` option:
```console
code-extensions --json
```


### dir-info.py
Run with command:
```console
dir-info
```
This command will give you the following info about your current working directory (`cwd`):
* the files count
* the total files scope (*lines count from all the files with text in them*)
* the total size of the files

It can take quite a bit of time to get this information, thus you can ignore the info you don't need with the `-i` or `--ignore` option:
```console
dir-info --ignore scope
```
```console
dir-info --ignore size
```
```console
dir-info --ignore scope size
```
The files count will always be included, since it doesn't affect the performance.


### hex-percent.py
Run with command:
```console
hex-percent
```
This command will turn a two digit HEX value into a percentage, where `FF` equals 100% and `00` equals 0%.

When the command is run, it will ask you for the HEX value, but you can also give it directly as an argument:
```console
hex-percent FF
```


### lib-publish.py
Run with command:
```console
lib-publish
```
This is just a single command, which runs the two required commands to package and directly upload your own Python library to [PyPI](https://pypi.org/).

You can also directly specify the path to the library to package and upload and if the process should be verbose:
```console
lib-publish --lib /path/to/library/root-directory --verbose
```


### matrix.py
Run with command:
```console
matrix
```
This command will display a sort of matrix in your console with a few options for customizing:
1. By standard, the matrix symbols are not colored. With the option `-c` or `--color` you can make them in random colors:
   ```console
   matrix --color
   ```
3. Normally, the matrix moves rather slowly, but with the option `-s`, `--speed`, `-f` or `--fast`, it will move very fast:
   ```console
   matrix --fast
   ```
3. You can also make the matrix in color and move fast, by applying both options:
   ```console
   matrix -c -f
   ```
Can be cancelled by pressing `Ctrl(⌘) + C`.


### pi.py
Run with command:
```console
pi
```
This command will calculate the value of the [Pi number](https://en.wikipedia.org/wiki/Pi) to a certain decimal place.<br>
To specify up to how many decimal places should be calculated, run the command with an argument:
```console
pi 100
```
Can be cancelled by pressing `Ctrl(⌘) + C`.


### process-list.py
Run with command:
```console
process-list
```
This command simply lets you input a list of items. It will then output all the items, but each item on a new line.<br>
In addition to that it will display some info about the items. When all the items are numbers, it will also output more info like the min, max, sum and average.

Per default, the list items are separated by a `space`, but this can be changed to anything else with the option `-s` or `--sep`:
```console
process-list --sep ","
```


### sine.py
Run with command:
```console
sine
```
This command will just display a moving sine wave, inside your console.<br>
Can be cancelled by pressing `Ctrl(⌘) + C`.


### x-tree.py
Run with command:
```console
x-tree
```
This command generates an advanced directory tree. You have the following options when running the command:
* directories to ignore in the tree (*just writes `...` instead of that directory's contents*)
* display the contents of the files (*utf-8*) directly included in the tree
* choose between different tree styles
* set the tree's indentation size
* output the tree into a file (*if it's too large to fit inside the console history*)

The directories to ignore can also be given directly via the option `-i` or `--ignore`:
```console
x-tree --ignore rel/path/to/dir1 rel/path/to/dir2
```
