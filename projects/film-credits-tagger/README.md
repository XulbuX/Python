# Film Credits Tagger • XulbuX<a href="#film-credits-tagger--xulbux"><img src="./assets/img/FilmCreditsTagger.svg" height="36" align="right" /></a>

A small desktop app for tagging film credits and metadata into video files – powered by [**ExifTool**](https://exiftool.org).<br>
Works on **Windows**, **macOS**, and **Linux**. Follows the system light/dark theme automatically.

> <br>
> Launch the app by running the <code>app.pyw</code> file:<br>
> ❯  On <b>Windows</b> the <code>.pyw</code> extension launches it without a console window by default.<br>
> ❯  On <b>macOS/Linux</b>, run it explicitly: <code>python3 app.pyw</code>
> <br>
> <br>

## Features

- **Write metadata** into `.mp4`, `.mov`, `.m4v`, `.m4a`, `.3gp`, and `.3g2` files.
- **Batch processing** – Select multiple files and apply the same tags to all at once.
- **Editable fields:** A variety of properties covering general info, credits, and descriptions.
- **Cover art** – Select an image, preview it in-app, and embed it as front-cover art.
- **JSON templates** – Save the current field values to a `.json` file and reload them later.
- **Load from video** – Reads existing metadata and cover art back out of a file and populates the fields.
- **Clear-empty toggle** – When enabled, fields left blank actively *delete* the corresponding tags from the file instead of leaving them untouched.
- **Cross-platform tags** – Writes both iTunes/QuickTime atoms (*recognized by macOS, VLC, mpv*) and Windows-specific tags (*recognized by Windows Explorer and WMP*) simultaneously.

## Requirements

- Python 3.10+
- [**ExifTool**](https://exiftool.org) installed and available on `PATH`
- Python packages:
  ```shell
  pip install customtkinter reportlab pymupdf pillow svglib
  ```
