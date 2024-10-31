# Custom Commands
This repository contains quite a few Python files, which are supposed to be run as commands in the console and do some useful stuff.<br>
[Figure out what each file (*command*) does.](#whateachcommanddoes)


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


## <span id="whateachcommanddoes">What each file (*command*) does</span>

### _.py
Run with command:
```console
_
```
This is a better version of the `cls` or `clear` command to clear your console. The command `_` is:<br>
* Faster to type and
* the command also resets all the console formats.

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
dir-info -i scope size
```

### lib-publish.py
Run with command:
```console
lib-publish
```
This is just a single command, which runs the two required commands to package and directly upload your own Python library to [PyPI](https://pypi.org/).

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

### x-tree.py
Run with command:
```console
x-tree
```
This command generates an advanced directory tree. You have the following options when running the command:
* directories to ignore in the tree (*just writes `...` instead of that directory's contents*)
* choose between different tree styles
* set the tree's indentation size
* output the tree into a file (*if it's too large to fit inside the console history*)

The directories to ignore can also be given directly via the option `-i` or `--ignore`:
```console
x-tree --ignore rel/path/to/dir1 rel/path/to/dir2
```
