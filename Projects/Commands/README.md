# Custom Commands
This repository contains quite a few Python files, which are supposed<br>
to be run as commands in the console and do some useful stuff.<br>
**[Figure out what each script (*command*) does.](#what-each-cmd-does)**

<br>
<br>

## Run the files as console commands

To run these Python scripts as native commands in your console, follow these steps.

<br>

### Prerequisites

> [!IMPORTANT]<br>
> Before you begin, ensure you have Python installed and **added to your system's PATH**.<br>
> This is crucial for the commands to be recognized and executed.
> 
>  * **Windows:** make sure to check the box `Add Python to PATH`<br>
>    and if possible `Install for all users` during the installation of Python.<br>
>    Verify Python is in your PATH by typing `python --version` or `py --version` in your console.
> 
>  * **macOS and Linux:** Python is often pre-installed, but you should verify<br>
>    it's in your PATH by typing `python3 --version` in your console.

<br>

### Step 1: Download the Files

Download the Python files you want to use, along with the [`requirements.txt`](https://git-link.vercel.app/api/download?url=https://github.com/XulbuX/Python/blob/main/Projects/Commands/requirements.txt) file.<br>
Place them all in a single, permanent directory on your computer. We'll call this your *commands-directory*.

> [!IMPORTANT]<br>
> The way you prepare the files depends on your operating system:
>
>  * **Windows:** You can leave the `.py` or `.pyw` extension on the files.<br>
>    As long as both `PY` and `PYW` are in your system's `PATHEXT` environment variable<br>
>    (*which is the default*), you can run the commands without typing `.py`.
>
>  * **macOS and Linux:** You **must remove the `.py` or `.pyw` extension** from the script files.<br>
>    For example, rename `x-cmds.py` to `x-cmds`.<br>
>    This allows the operating system to execute them as native commands.

<br>

<span id="install-dependencies" />

### Step 2: Install Dependencies

Before the scripts can run, you need to install their required Python packages. 📦

1. Open your console.
2. Navigate to your *commands-directory* using the `cd` command.
   ```shell
   cd "/path/to/your/commands-directory"
   ```
3. Install the dependencies using pip:
   ```shell
   pip install --upgrade -r "requirements.txt"
   ```

<br>

### Step 3: Make Scripts Executable as Commands

This makes your commands available from any location in your console. ⚙️

#### Windows:

* **Add the *commands-directory* to your system's `Path` environment variable:**
  1. Open the Start Menu, search for "Environment Variables", and select `Edit the system environment variables`.
  2. In the `System Properties` window, click `Environment Variables...`.
  3. Under the `System variables` section, find and select the `Path` variable, then click `Edit...`.
  4. Click `New` and paste in the absolute path to your *commands-directory*.
  5. Click `OK` to close all dialogs.
* **Assure correct file associations for `.py` and `.pyw` files:**
   1. In the File Explorer, right-click on any `.py` file and select `Open with` > `Choose another app`.
   2. Scroll all the way down and click `Choose an app on your PC`.
   3. Navigate to your Python installation directory (*e.g.* `C:\Program Files\Python\`), select `python.exe`, and click `Open`.
   4. Now click on `Always` to set Python as the default app for `.py` files.
   5. Lastly, repeat the same steps for a <code>.py**w**</code> file, but select <code>python**w**.exe</code> instead of `python.exe` under step 3.


#### macOS and Linux:

* **Add a shebang line:** Make sure the very first line of every script file is `#!/usr/bin/env python3`.<br>
  (*Note: This is already done for you in all the repository's files.*)
* **Make the files executable:** Open your console and run the following command, replacing the path with your own:
  ```shell
  chmod +x "/path/to/your/commands-directory/*"
  ```
* **Add the directory to your console's PATH:**
   1. For modern **macOS** (*and Linux with Zsh*), edit `~/.zshrc`.
   2. For most **Linux** distributions, edit `~/.bashrc`.
   3. Open the file (*e.g.* `nano ~/.zshrc`) and add this line to the end:
      ```shell
      export PATH="$PATH:/path/to/your/commands-directory"
      ```
   4. Save the file, and then apply the changes by running `source ~/.zshrc` (*or the file you edited*).

<br>

### Step 4: Restart your Console

Close and reopen your console.<br>
The changes are now active, and you can run the files by typing their names (*e.g.* [`x-cmds`](#x-cmds)). ✅

<br>
<br>

<span id="what-each-cmd-does" />

## What each script (*command*) does

Here's a brief overview of what each script does and how to use it.<br>
**⇾** Each process can be canceled by pressing `Ctrl(⌘) + C`.

> [!NOTE]<br>
> If any of the scripts doesn't work (*especially after you updated them to their latest versions*),<br>
> make sure you have updated all the required dependencies to their latest versions.<br>
> For that download the latest [`requirements.txt`](https://git-link.vercel.app/api/download?url=https://github.com/XulbuX/Python/blob/main/Projects/Commands/requirements.txt) file and then follow the [**dependencies installing steps**](#install-dependencies) again.

<br>

### `_`

This is a better version of the `cls` or `clear` command to clear your console for a few reasons:<br>
 * the command `_` is faster to type
 * the command actually **clears** the console and doesn't just scroll the content up
 * the command also resets all the color and style formats

<br>

### `capitalize-hex`

This command will capitalize all found HEX colors in the given file or directory.

The path to the file or directory containing files can be directly given as an argument:
```shell
capitalize-hex "/path/to/file"
```
```shell
capitalize-hex "/path/to/directory"
```

<br>

### `dinfo`

This command will give you the following info about the files in your current working directory (`cwd`):
 * the files count
 * the total files scope (*lines count from all the files with text in them*)
 * the total size of the files

To also scan all subdirectories recursively, use the `-r` `--recursive` option:
```shell
dinfo --recursive
```

It can take quite a bit of time to get this information, thus you can exclude info you don't need with the `-e` `--exclude` option.<br>
Possible exclude values are `scope` and `size`:
```shell
dinfo --exclude='scope'
```
```shell
dinfo --exclude='size'
```
```shell
dinfo --exclude='scope size'
```
The files count will always be included, since it doesn't affect the performance.

You can also decide whether hidden files/directories and/or system files/directories should be skipped with the `-s` `--skip` option.<br>
Possible skip values are `hidden` and `system`:
```shell
dinfo --skip='hidden'
```
```shell
dinfo --skip='system'
```
```shell
dinfo --skip='hidden system'
```

The last option lets you decide if `.gitignore` rules should be applied when getting the info, with the `-g` `--gitignore` option:
```shell
dinfo --gitignore
```

To show help for the command, use the `-h` `--help` option:
```shell
dinfo --help
```

<br>

### `gradient`

This command will generate and preview a color gradient between two or more specified HEX colors.
```shell
gradient '#F00' '#00F'
```

You can also create multicolor gradients by specifying more than two colors:
```shell
gradient 'F00' '00F' '0F0'
```

You can specify the number of steps in the gradient with the `-s` `--steps` option:
```shell
gradient 'F00' '00F' --steps=10
```

Per default the gradient is generated using linear RGB interpolation.<br>
To generate the gradient using HSV color space, use the `-H` `--hsv` option:
```shell
gradient 'F00' '00F' --hsv
```

To generate the gradient using perceptually uniform OKLCH color space, use the `-O` `--oklch` option:
```shell
gradient 'F00' '00F' --oklch
```

When using HSV or OKLCH modes, you can control the direction of hue rotation between colors using `>` (*clockwise*) or `<` (*counterclockwise*):
```shell
gradient 'F00' '<' '00F' --hsv
```
```shell
gradient 'F00' '>' '00F' --oklch
```

You can combine multiple colors with different directions:
```shell
gradient 'F00' '>' '00F' '<' '0F0' --hsv
```

To show a list of all the colors in the generated gradient, use the `-l` `--list` option:
```shell
gradient 'F00' '00F' --list
```

To show step numbers alongside the listed colors, use the `-n` `--numerate` option:
```shell
gradient 'F00' '00F' --numerate
```

To show help for the command, use the `-h` `--help` option:
```shell
gradient --help
```

<br>

### `hex-percent`

This command will turn a two digit HEX value into a percentage, where `FF` equals 100% and `00` equals 0%.

When the command is run, it will ask you for the HEX value, but you can also give it directly as an argument:
```shell
hex-percent 'FF'
```

<br>

### `lib-publish`

This is just a single command, which runs the two required commands to package and directly upload your own Python library to [PyPI](https://pypi.org/).

You can also directly specify the path to the library to package and upload and if the process should be verbose:
```shell
lib-publish "/path/to/library/root-directory" --verbose
```

To build but not upload the library, use the option `-ob` `--only-build`:
```shell
lib-publish "/path/to/library/root-directory" --only-build
```

To show help for the command, use the `-h` `--help` option:
```shell
lib-publish --help
```

<br>

### `life`

This command starts a simulation of [Conway's Game of Life](https://wikipedia.org/wiki/Conway's_Game_of_Life) inside the console.

<br>

### `maze`

This command starts a small maze game inside the console. The game controls and options are first shown at game start.

The maze will adjust itself to the dimensions of your console after each new maze generation.

<br>

### `mess`

This command will display an animated, random text character mess in your console with a few options for customizing:
1. By standard, the matrix symbols are not colored. With the option `-c` `--color` you can make them in random colors:
   ```shell
   mess --color
   ```
3. Normally, the matrix moves rather slowly, but with the option `-s` `--speed` or `-f` `--fast`, it will move very fast:
   ```shell
   mess --fast
   ```
3. You can also make the matrix in color and move fast, by applying both options:
   ```shell
   mess -c -f
   ```

<br>

### `pi`

This command will calculate the value of the [Pi number](https://en.wikipedia.org/wiki/Pi) to a certain decimal place.<br>
To specify up to how many decimal places should be calculated, run the command with an argument:
```shell
pi 100
```

<br>

### `process-list`

This command simply lets you input a list of items. It will then output all the items, but each item on a new line.<br>
In addition to that it will display some info about the items. When all the items are numbers, it will also output more info like the min, max, sum and average.

Per default, the list items are separated by a `space`, but this can be changed to anything else with the option `-s` `--sep`:
```shell
process-list "item1;item2;item3" --sep=';'
```

<br>

### `rand`

This command will generate a truly random integer number with a specific number of digits or between a minimum and maximum value.

To generate a random integer with a specific number of digits, run the command with that number as an argument:
```shell
rand 10
```

To generate a random integer between a minimum and maximum value, run the command with both values as arguments:
```shell
rand 0 100
```

You can also batch generate multiple numbers at once with the option `-b` `--batch` `--batch-gen`:
```shell
rand 10 --batch=5
```

To format the generated number/s with thousands-separators, use the option `-f` `--format`:
```shell
rand -1_000_000 1_000_000 --format
```

To show help for the command, use the `-h` `--help` option:
```shell
rand --help
```

<br>

### `shell-colors`

This command will display all the standard shell colors in your console using a simple sample text.

To use a custom sample text, use the `-t` `--text` option:
```shell
shell-colors --text="Hello, world!"
```

<br>

### `sine`

This command will just display a moving sine wave inside your console.

The rendering of the sine wave can also be inverted with the option `-i` `--invert` `--inverse`:
```shell
sine --invert
```

<br>

### `squares`

This command gives you the option to get a nicely formatted table with the squares of all numbers up to a certain number.

You can specify the number of table columns with the `-c` `--cols` `--columns` option:
```shell
squares --cols=6
```

<br>

### `vscode-ext`

This command will output info about all installed Visual Studio Code extensions:
1. the installed extensions count
2. a list of all installed extensions

You can also output the list of installed extensions, formatted as a JSON array, with the `-j` `--json` option:
```shell
code-extensions --json
```

<br>

### `x-calc`

This command lets you do advanced calculations directly in the console. It supports a wide range of mathematical operations, functions and constants.

You can directly give the calculation as an argument:
```shell
x-calc "2 + 2 * 2"
```

There's also an option to specify a previous answer with the `-a` `--ans` option:
```shell
x-calc "ans * 2" --ans=6
```

You can also specify the calculation precision (*result decimal places*) with the `-p` `--precision` option:
```shell
x-calc "sqrt(ln(10) + 1) / cos(π / 4)" --precision=1000
```

And yes, it can do **very** complex calculations:
```shell
x-calc "(((sinh(2.7) * cosh(1.3) + tanh(0.5)) / (sqrt(abs(sin(π/6) - cos(π/3))) + exp(ln(2)))) * (log10(100) + ln(e^2)) - ((fac(5) / (4! + 3!)) * (2^8 - 3^5)) + (((asin(0.5) + acos(0.5)) * atan(1)) / (sqrt(2) * sqrt(3))) + (cbrt(27) * sqrt(49) - pow(2, 10) / 1024) + ((sinh(1) + cosh(1)) / (1 + tanh(0))) * log(1000, 10) - (((sin(π/4))^2 + (cos(π/4))^2) * exp(0)) + (arctan(sqrt(3)) - arcsin(1/2)) * (log2(256) / ln(e^8)) + ((fac(6) - 5^3) / (sqrt(144) + cbrt(64))) * (sinh(0.5)^2 - cosh(0.5)^2 + 1) - (((2 * φ * sqrt(5)) / (1 + sqrt(5))) * (log(e^10) - ln(exp(10)))) + ((acos(-1) / 2 + asin(1)) * (tan(π/4) + cot(π/4))) / (sec(0) * csc(π/2))) ^ τ" -p 1000
```

To show help for the command, use the `-h` `--help` option:
```shell
x-calc --help
```

<br>

<span id="x-cmds" /><span id="x-commands" />

### `x-cmds`

This command outputs a list of all custom Python commands in the current directory,<br>
with a short description (*if provided*) and their params (*if found*).

To check new commands / command-updates and optionally directly download and install them, use the `-u` `--update` option:
```shell
x-cmds --update
```
⇾ To adjust some update-checking-options, you can edit the `CONFIG` variable, inside the script file.

#### How the Update System Works

The update system is designed to keep managed commands up-to-date while protecting your custom files:

 * **Managed Commands:** Only files with the comment `#[x-cmds]: UPDATE` at the top (*after the shebang*) are checked for updates.<br>
   These commands can be automatically updated or deleted if they're removed from the repository.

 * **User Commands:** Files **without** the `#[x-cmds]: UPDATE` marker are considered user-created and<br>
   will **never** be modified or deleted by the update system, keeping your custom commands safe.

 * **Update Detection:** The system checks multiple GitHub repository URLs (*configurable in the script*),<br>
   merges all available commands, and detects three types of changes:
   - **New commands** - available in the repository but not locally
   - **Updated commands** - local managed commands with content changes
   - **Deleted commands** - local managed commands no longer in any repository

This approach allows you to safely add your own commands to the directory while still benefiting from automatic updates.

<br>

### `x-hw`

Get detailed hardware information about your PC.

To get even more detailed information, use the `-d` `--detailed` option:
```shell
x-hw --detailed
```

You can also output the info as a JSON object with the `-j` `--json` option:
```shell
x-hw --json
```

To show help for the command, use the `-h` `--help` option:
```shell
x-hw --help
```

<br>

### `x-ip`

This command will give you info about your local and public IP addresses, with optional geolocation information about the public IP address.

To include geolocation information, use the `-g` `--geo` option:
```shell
x-ip --geo
```

To specify a specific provider for the geolocation information, use the `-p` `--provider` option:
```shell
x-ip --geo --provider="ipinfo"
```

You can also output the info as a JSON object with the `-j` `--json-output` option:
```shell
x-ip --json-output
```

To show help for the command, use the `-h` `--help` option:
```shell
x-ip --help
```

<br>

### `x-modules`

This command will list all Python modules imported across Python files in the script directory, along with some additional info.

You can exclude standard library modules with the `-e` `--external` option:
```shell
x-modules --external
```

To specify a specific directory to scan, use the `-d` `--directory` option and add the `-r` `--recursive` option to scan subdirectories recursively:
```shell
x-modules --directory="./src"
```
```shell
x-modules --directory="./src" -r
```

To only get the list of modules without any additional info, use the `-nf` `--no-formatting` option:
```shell
x-modules --no-formatting
```

You can also output the info as a JSON object with the `-j` `--json` option:
```shell
x-modules --json
```

There's also the option to directly install all found external modules with `pip` by using the `-i` `--install` option:
```shell  
x-modules --install
```

To show help for the command, use the `-h` `--help` option:
```shell
x-modules --help
```

<br>

### `x-qr`

This command lets you quickly generate QR codes directly within the console. You also have options for generating different special QR codes:
 * Wi-Fi QR codes
 * Contact QR codes

These special QR codes can be generated with the options `-w` `--wifi` and `-c` `--contact`:
```shell
x-qr --wifi
```
```shell
x-qr "James Brown" --contact
```

Generating a normal QR code of some text, URL, etc. can be done by simply giving that text directly as an argument:
```shell
x-qr "https://example.com/"
```

To show help for the command, use the `-h` `--help` option:
```shell
x-qr --help
```

<br>

### `x-rm`

This command is used to force-delete files/directories that are locked somehow and can't be deleted with the normal `rm` or `del` commands.

The confirmation step can be skipped with the `-nc` `--no-confirm` option:
```shell
x-rm "/path/to/file-or-directory" --no-confirm
```

To show help for the command, use the `-h` `--help` option:
```shell
x-rm --help
```

<br>

### `x-tree`

This command generates an advanced directory tree. You have the following options when running the command:
 * directories to ignore in the tree (*just writes `...` instead of that directory's contents*)
 * display the contents of the files (*utf-8*) directly included in the tree
 * choose between different tree styles
 * set the tree's indentation size
 * output the tree into a file (*if it's too large to fit inside the console history*)

The directories to ignore can also be given directly via the option `-i` `--ignore` (*absolute paths, relative paths or directory names, separated by* `|`):
```shell
x-tree --ignore="/abs/to/dir1 | rel/to/dir2 | dir3"
```

With the option `-n` `-np` `--no-progress`, you can disable the progress from being shown while generating the tree (*might make the generation a bit faster*):
```shell
x-tree --no-progress
```

To show help for the command, use the `-h` `--help` option:
```shell
x-tree --help
```

<br>

### `xc`

This tool can be used to run a command and automatically copy the full output including metadata to the clipboard, after execution.

You can directly give the command to run as an argument:
```shell
xc dinfo -r
```

To not include the ran command in the clipboard, use the `-nc` `--no-command` option:
```shell
xc --no-command dinfo -r
```

To not include the metadata in the clipboard, use the `-nm` `--no-metadata` option:
```shell
xc --no-metadata x-modules -e
```

You can also only copy the output without metadata or command, with the `-o` `--only` option:
```shell
xc --only x-hw --detailed
```

If ANSI codes should be included in the clipboard output, use the `-a` `--ansi` option:
```shell
xc --ansi x-ip --geo
```

To show help for the command, use the `-h` `--help` option:
```shell
xc --help
```
