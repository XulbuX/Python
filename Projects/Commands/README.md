# Custom Commands
This repository contains quite a few Python files, which are supposed to be run as commands in the console and do some useful stuff.<br>
**[Figure out what each file (*command*) does.](#what-each-cmd-does)**


## Run the files as console commands
To be able to type one of the file's names in the console and, through this, run that corresponding file, you need to follow these steps:

1. Download the Python files you want to use as commands.

2. Place all downloaded files in a single directory of your choice.
   We'll call this directory the *commands-directory* from now on.

3. > [!IMPORTANT]
   > Now, make sure you have [Python](https://www.python.org/downloads/) installed *for all users* on your system
   > and the absolute path to the Python installation directory (*the one containing* `python.exe`) is in your system's environment variables.<br>
   > If the Python installation directory is not in your system's environment variables, follow the same steps below for adding the *commands-directory*
   > and additional to the *commands-directory* also add the Python installation directory to your system's environment variables.

4. Now we need to add the absolute path to the *commands-directory* to your system's environment variables. This process varies depending on your OS:

   ### Windows:
   * Open the Start Menu and search for `Environment Variables`.
   * Select "Edit the system environment variables".
   * In the `System Properties` window, click on the `Environment Variables...` button.
   * Under the `System variables` section, find and select the `Path` variable, then click `Edit...`.
   * Click `New` and add the absolute path to your *commands-directory*.
   * Click `OK` to close all dialog boxes.

   ### macOS and Linux:
   * Open your terminal.
   * Edit your shell configuration file (*e.g.*, `~/.bash_profile`, `~/.bashrc`, *or* `~/.zshrc`) using a text editor.
   * Add the following line at the end of the file, replacing `/path/to/your/directory` with the actual *commands-directory* path:
     ```bash
     export PATH="$PATH:/path/to/your/directory"
     ```
   * Save the file and run `source ~/.bash_profile` (*or the appropriate file you edited*) to apply changes.
   * Make the files executable:
     ```bash
     chmod +x "/path/to/your/directory/*.py"
     ```

5. Restart your terminal or command prompt for the changes to take effect.

After completing these steps, you should be able to run the commands described below.


## <span id="what-each-cmd-does">What each file (*command*) does</span>


### _.py
Run with command:
```bash
_
```
This is a better version of the `cls` or `clear` command to clear your console. The command `_` is:<br>
* Faster to type and
* the command also resets all the console formats.


### capitalize-hex.py
Run with command:
```bash
capitalize-hex
```
This command will capitalize all found HEX colors in the given file or directory.

The path to the file or directory containing files can be directly given as an argument:
```bash
capitalize-hex "/path/to/file"
```
```bash
capitalize-hex "/path/to/directory"
```


### code-extensions.py
Run with command:
```bash
code-extensions
```
This command will output info about all installed Visual Studio Code extensions:
1. the installed extensions count
2. a list of all installed extensions

You can also output the list of installed extensions, formatted as a JSON array, with the `-j` `--json` option:
```bash
code-extensions --json
```


### dir-info.py
Run with command:
```bash
dir-info
```
This command will give you the following info about your current working directory (`cwd`):
* the files count
* the total files scope (*lines count from all the files with text in them*)
* the total size of the files

It can take quite a bit of time to get this information, thus you can ignore the info you don't need with the `-i` `--ignore` option:
```bash
dir-info --ignore 'scope'
```
```bash
dir-info --ignore 'size'
```
```bash
dir-info --ignore 'scope' 'size'
```
The files count will always be included, since it doesn't affect the performance.


### hex-percent.py
Run with command:
```bash
hex-percent
```
This command will turn a two digit HEX value into a percentage, where `FF` equals 100% and `00` equals 0%.

When the command is run, it will ask you for the HEX value, but you can also give it directly as an argument:
```bash
hex-percent 'FF'
```


### lib-publish.py
Run with command:
```bash
lib-publish
```
This is just a single command, which runs the two required commands to package and directly upload your own Python library to [PyPI](https://pypi.org/).

You can also directly specify the path to the library to package and upload and if the process should be verbose:
```bash
lib-publish "/path/to/library/root-directory" --verbose
```


### maze.py
Run with command:
```bash
maze
```
This command starts a small maze game inside the console. The game controls and options are first shown at game start.

The maze will adjust itself to the dimensions of your console after each new maze generation.


### mess.py
Run with command:
```bash
mess
```
This command will display an animated, random text character mess in your console with a few options for customizing:
1. By standard, the matrix symbols are not colored. With the option `-c` `--color` you can make them in random colors:
   ```bash
   mess --color
   ```
3. Normally, the matrix moves rather slowly, but with the option `-s` `--speed` or `-f` `--fast`, it will move very fast:
   ```bash
   mess --fast
   ```
3. You can also make the matrix in color and move fast, by applying both options:
   ```bash
   mess -c -f
   ```
Can be cancelled by pressing `Ctrl(⌘) + C`.


### pi.py
Run with command:
```bash
pi
```
This command will calculate the value of the [Pi number](https://en.wikipedia.org/wiki/Pi) to a certain decimal place.<br>
To specify up to how many decimal places should be calculated, run the command with an argument:
```bash
pi 100
```
Can be cancelled by pressing `Ctrl(⌘) + C`.


### process-list.py
Run with command:
```bash
process-list
```
This command simply lets you input a list of items. It will then output all the items, but each item on a new line.<br>
In addition to that it will display some info about the items. When all the items are numbers, it will also output more info like the min, max, sum and average.

Per default, the list items are separated by a `space`, but this can be changed to anything else with the option `-s` `--sep`:
```bash
process-list "item1, item2, item3" --sep ','
```


### sine.py
Run with command:
```bash
sine
```
This command will just display a moving sine wave, inside your console.<br>
Can be cancelled by pressing `Ctrl(⌘) + C`.


### squares.py
Run with command:
```bash
squares
```
This command gives you the option to get a nicely formatted table with the squares of all numbers up to a certain number.

You can specify the number of table columns with the `-c` `--columns` option:
```bash
squares --columns 6
```


### x-cmds.py
Run with command:
```bash
x-cmds
```
This command outputs a list of all custom Python commands in the current directory, with a short description and their params.


### x-qr.py
Run with command:
```bash
x-qr
```
This command lets you quickly generate QR codes directly within the terminal. You also have options for generating different special QR codes:
* Wi-Fi QR codes
* Contact QR codes

These special QR codes can be generated with the options `-w` `--wifi` and `-c` `--contact`:
```bash
x-qr --wifi
```
```bash
x-qr "James Brown" --contact
```

Generating a normal QR code of some text, URL, etc. can be done by simply giving that text directly as an argument:
```bash
x-qr "https://example.com/"
```

Running the command without any arguments or options will show help for the command.


### x-tree.py
Run with command:
```bash
x-tree
```
This command generates an advanced directory tree. You have the following options when running the command:
* directories to ignore in the tree (*just writes `...` instead of that directory's contents*)
* display the contents of the files (*utf-8*) directly included in the tree
* choose between different tree styles
* set the tree's indentation size
* output the tree into a file (*if it's too large to fit inside the console history*)

The directories to ignore can also be given directly via the option `-i` `--ignore` (*absolute paths, relative paths or directory names*):
```bash
x-tree --ignore "/abs/path/to/dir1" "rel/path/to/dir3" 'dir3'
```

With the option `-n` `-np` `--no-progress`, you can disable the progress from being shown while generating the tree (*might make the generation a bit faster*):
```bash
x-tree --no-progress
```
