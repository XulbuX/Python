<div id="top" style="width:45px; height:45px; right:10px; top:10px; position:absolute">
  <a href="#release"><abbr title="go to bottom" style="text-decoration:none">
    <div style="
      font-size: 2em;
      font-weight: bold;
      background: #88889845;
      border-radius: 0.2em;
      text-align: center;
      justify-content: center;
    ">🠫</div>
  </abbr></a>
</div>


# <br><b>Changelog</b><br>


## 18.10.2024 `v1.2.4` `v1.2.5`
* renamed the class `rgb()` to `rgba()` to communicate, more clearly, that it supports an alpha channel
* renamed the class `hsl()` to `hsla()` to communicate, more clearly, that it supports an alpha channel
* added more info to the `README.md` as well as additional links
* adjusted the structure inside `CHANGELOG.md` for a better overview and readability

## 18.10.2024 `v1.2.3`
* added project links to the Python-project-file
* `CHANGELOG.md` improvements
* `README.md` improvements

## 18.10.2024 `v1.2.1` − `v1.2.2`
* fixed bug in function `Path.get(base_dir=True)`:<br>
  Previously, setting `base_dir` to `True` would not return the actual base directory or even cause an error.<br>
  This was now fixed, and setting `base_dir` to `True` will return the actual base directory of the current program (*except if not running from a file*).

## 17.10.2024 `v1.2.0`
* new function in the `Path` class: `Path.remove()`

## 17.10.2024 `v1.1.9`
* corrected the naming of classes to comply with Python naming standards

## 17.10.2024 `v1.1.8`
* added support for all OSes to the OS-dependent functions

## 17.10.2024 `v1.1.6` − `v1.1.7`
* fixed the `Cmd.cls()` function:<br>
  There was a bug where, on Windows 10, the ANSI formats weren't cleared.

## 17.10.2024 `v1.1.4` − `v1.1.5`
* added link to `CHANGELOG.md` to the `README.md` file

## 17.10.2024 `v1.1.3`
* changed the default value of the param `compactness:int` in the function `Data.print()` to `1` instead of `0`

## 17.10.2024 `v1.1.1` − `v1.1.2`
* adjusted the library's description

## 16.10.2024 `v1.1.0`
* made it possible to also auto-reset the color and not only the predefined formats, using the [auto-reset-format](#autoresetformat) (`[format](Automatically resetting)`)

## 16.10.2024 `v1.0.9`
* added a library description, which gets shown if it's ran directly
* made it possible to escape an <span id="autoresetformat">auto-reset-format</span> (`[format](Automatically resetting)`) with a slash, so you can still have `()` brackets behind a `[format]`:
  ```python
  FormatCodes.print('[u](Automatically resetting) following text')
  ```
  prints:  <code><u>Automatically resetting</u> following text</code>

  ```python
  FormatCodes.print('[u]/(Automatically resetting) following text')
  ```
  prints:  <code><u>(Automatically resetting) following text</u></code>

## 16.10.2024 `v1.0.7` − `v1.0.8`
* added `input()` function to the `FormatCodes` class, so you can make pretty looking input prompts
* added warning for no network connection when trying to [install missing libraries](#improvedlibimporting)

## 15.10.2024 `v1.0.6`
* <span id="improvedlibimporting">improved `XulbuX` library importing:</span><br>
  checks for missing required libraries and gives you the option to directly install them, if there are any
* moved constant variables into a separate file
* fixed issue where configuration file wasn't created and loaded correctly

## 15.10.2024 `v1.0.1` − `v1.0.5`
* fixed `f-string` issues for Python 3.10:<br>
  **1:** no use of same quotes inside f-strings<br>
  **2:** no backslash escaping in f-strings

## <span id="release">14.10.2024 `v1.0.0`</span>
$\color{#F90}\Huge\textsf{RELEASE!\ 🤩🎉}$<br>
**At release**, the library **$\color{#8085FF}\textsf{XulbuX}$** looks like this:
```python
# GENERAL LIBRARY
import XulbuX as xx
# CUSTOM TYPES
from XulbuX import rgb, hsl, hexa
```
<table>
  <thead>
    <tr>
      <th>Features</th>
      <th>class, type, function, ...</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Custom Types:</td>
      <td>
<code>rgb(<em>int</em>, <em>int</em>, <em>int</em>, <em>float</em>)</code><br>
<code>hsl(<em>int</em>, <em>int</em>, <em>int</em>, <em>float</em>)</code><br>
<code>hexa(<em>str</em>)</code>
      </td>
    </tr><tr>
      <td>Directory Operations</td>
      <td><code>xx.Dir</code></td>
    </tr><tr>
      <td>File Operations</td>
      <td><code>xx.File</code></td>
    </tr><tr>
      <td>JSON File Operations</td>
      <td><code>xx.Json</code></td>
    </tr><tr>
      <td>System Actions</td>
      <td><code>xx.System</code></td>
    </tr><tr>
      <td>Manage Environment Vars</td>
      <td><code>xx.EnvVars</code></td>
    </tr><tr>
      <td>CMD Log And Actions</td>
      <td><code>xx.Cmd</code></td>
    </tr><tr>
      <td>Pretty Printing</td>
      <td><code>xx.FormatCodes</code></td>
    </tr><tr>
      <td>Color Operations</td>
      <td><code>xx.Color</code></td>
    </tr><tr>
      <td>Data Operations</td>
      <td><code>xx.Data</code></td>
    </tr><tr>
      <td>String Operations</td>
      <td><code>xx.String</code></td>
    </tr><tr>
      <td>Code String Operations</td>
      <td><code>xx.Code</code></td>
    </tr><tr>
      <td>Regex Pattern Templates</td>
      <td><code>xx.Regex</code></td>
    </tr>
  </tbody>
</table>


<div id="bottom" style="width:45px; height:45px; right:10px; position:absolute">
  <a href="#top"><abbr title="go to top" style="text-decoration:none">
    <div style="
      font-size: 2em;
      font-weight: bold;
      background: #88889845;
      border-radius: 0.2em;
      text-align: center;
      justify-content: center;
    ">🠩</div>
  </abbr></a>
</div>
