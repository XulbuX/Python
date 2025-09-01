# Custom Commands
This repository contains quite a few Python files, which are supposed to be run as commands in the shell and do some useful stuff.<br>
**[Figure out what each file (*command*) does.](#what-each-cmd-does)**

<br>
<br>

## Run the files as shell commands

To run these Python scripts as native commands in your shell, follow these steps.

<br>

### Prerequisites

> [!IMPORTANT]
> Before you begin, ensure you have Python installed and **added to your system's PATH**.<br>
> This is crucial for the commands to be recognized and executed.
> 
>  * **Windows:**, make sure to check the box `Add Python to PATH`<br>
>    and if possible `Install for all users` during the installation of Python.<br>
>    Verify Python is in your PATH by typing `python --version` or `py --version` in your shell.
> 
>  * **macOS and Linux:** Python is often pre-installed, but you should verify<br>
>    it's in your PATH by typing `python3 --version` in your shell.

<br>

### Step 1: Download the Files

Download the Python files you want to use, along with the `requirements.txt` file.<br>
Place them all in a single, permanent directory on your computer. We'll call this your *commands-directory*.

> [!IMPORTANT]
> The way you prepare the files depends on your operating system:
>
>  * **Windows:** You can leave the `.py` extension on the files.<br>
>    As long as `PY` is in your system's `PATHEXT` environment variable (*which is the default*),<br>
>    you can run the commands without typing `.py`.
>
>  * **macOS and Linux:** You **must remove the `.py` extension** from the script files.
>    For example, rename `x-tree.py` to `x-tree`.<br>
>    This allows the operating system to execute them as native commands.

<br>

### Step 2: Install Dependencies

Before the scripts can run, you need to install their required Python packages. 📦

1. Open your shell.
2. Navigate to your *commands-directory* using the `cd` command.
   ```bash
   cd "/path/to/your/commands-directory"
   ```
3. Install the dependencies using pip:
   ```bash
   pip install -r "requirements.txt"
   ```
   
<br>

### Step 3: Add Scripts to the System PATH

This makes your commands available from any location in your shell. ⚙️

#### Windows:

1. Open the Start Menu, search for `Environment Variables`, and select "Edit the system environment variables".
2. In the `System Properties` window, click `Environment Variables...`.
3. Under the `System variables` section, find and select the `Path` variable, then click `Edit...`.
4. Click `New` and paste in the absolute path to your *commands-directory*.
5. Click `OK` to close all dialogs.

#### macOS and Linux:

1. **Add a shebang line:** Make sure the very first line of every script file is `#!/usr/bin/env python3`.<br>
   (*Note: This is already done for you in all the repository's files.*)
2. **Make the files executable:** Open your shell and run the following command, replacing the path with your own:
   ```bash
   chmod +x "/path/to/your/commands-directory/*"
   ```
3. **Add the directory to your shell's PATH:**
    * For modern **macOS** (*and Linux with Zsh*), edit `~/.zshrc`.
    * For most **Linux** distributions, edit `~/.bashrc`.
    * Open the file (*e.g.* `nano ~/.zshrc`) and add this line to the end:
      ```bash
      export PATH="$PATH:/path/to/your/commands-directory"
      ```
    * Save the file, and then apply the changes by running `source ~/.zshrc` (*or the file you edited*).

<br>

### Step 4: Restart your Shell

Close and reopen your shell.<br>
The changes are now active, and you can run the files by typing their names (*e.g.* `x-cmds`). ✅

<br>
<br>

## <span id="what-each-cmd-does">What each file (*command*) does</span>

<br>

### `_`

This is a better version of the `cls` or `clear` command to clear your shell for a few reasons:<br>
 * the command `_` is faster to type
 * the command actually **clears** the shell and doesn't just scroll the content up
 * the command also resets all the color and style formats

<br>

### `capitalize-hex`

This command will capitalize all found HEX colors in the given file or directory.

The path to the file or directory containing files can be directly given as an argument:
```bash
capitalize-hex "/path/to/file"
```
```bash
capitalize-hex "/path/to/directory"
```

<br>

### `code-extensions`

This command will output info about all installed Visual Studio Code extensions:
1. the installed extensions count
2. a list of all installed extensions

You can also output the list of installed extensions, formatted as a JSON array, with the `-j` `--json` option:
```bash
code-extensions --json
```

<br>

### `dir-info`

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

<br>

### `hex-percent`

This command will turn a two digit HEX value into a percentage, where `FF` equals 100% and `00` equals 0%.

When the command is run, it will ask you for the HEX value, but you can also give it directly as an argument:
```bash
hex-percent 'FF'
```

<br>

### `lib-publish`

This is just a single command, which runs the two required commands to package and directly upload your own Python library to [PyPI](https://pypi.org/).

You can also directly specify the path to the library to package and upload and if the process should be verbose:
```bash
lib-publish "/path/to/library/root-directory" --verbose
```

To build but not upload the library, use the option `-ob` `--only-build` `--just-build`:
```bash
lib-publish "/path/to/library/root-directory" --only-build
```

<br>

### `maze`

This command starts a small maze game inside the shell. The game controls and options are first shown at game start.

The maze will adjust itself to the dimensions of your shell after each new maze generation.

<br>

### `mess`

This command will display an animated, random text character mess in your shell with a few options for customizing:
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

<br>

### `pi`

This command will calculate the value of the [Pi number](https://en.wikipedia.org/wiki/Pi) to a certain decimal place.<br>
To specify up to how many decimal places should be calculated, run the command with an argument:
```bash
pi 100
```
Can be cancelled by pressing `Ctrl(⌘) + C`.

<br>

### `process-list`

This command simply lets you input a list of items. It will then output all the items, but each item on a new line.<br>
In addition to that it will display some info about the items. When all the items are numbers, it will also output more info like the min, max, sum and average.

Per default, the list items are separated by a `space`, but this can be changed to anything else with the option `-s` `--sep`:
```bash
process-list "item1, item2, item3" --sep ','
```

<br>

### `sine`

This command will just display a moving sine wave inside your shell.<br>
Can be cancelled by pressing `Ctrl(⌘) + C`.

<br>

### `squares`

This command gives you the option to get a nicely formatted table with the squares of all numbers up to a certain number.

You can specify the number of table columns with the `-c` `--columns` option:
```bash
squares --columns 6
```

<br>

### `x-cmds`

This command outputs a list of all custom Python commands in the current directory, with a short description and their params.

<br>

### `x-qr`

This command lets you quickly generate QR codes directly within the shell. You also have options for generating different special QR codes:
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

<br>

### `x-tree`

This command generates an advanced directory tree. You have the following options when running the command:
 * directories to ignore in the tree (*just writes `...` instead of that directory's contents*)
 * display the contents of the files (*utf-8*) directly included in the tree
 * choose between different tree styles
 * set the tree's indentation size
 * output the tree into a file (*if it's too large to fit inside the shell history*)

The directories to ignore can also be given directly via the option `-i` `--ignore` (*absolute paths, relative paths or directory names*):
```bash
x-tree --ignore "/abs/path/to/dir1" "rel/path/to/dir3" 'dir3'
```

With the option `-n` `-np` `--no-progress`, you can disable the progress from being shown while generating the tree (*might make the generation a bit faster*):
```bash
x-tree --no-progress
```
