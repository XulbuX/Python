# Apps

This directory contains lots of small, useful desktop apps built with [**Python**](https://www.python.org) and [**CustomTkinter**](https://customtkinter.tomschimansky.com).

✔️  All apps run on **Windows**, **macOS**, and **Linux**.<br>
✨  All apps use a consistent, modern design language.<br>
🔆  All apps follow the system **light/dark theme**.<br>

### Apps in this collection

- [**Film Credits Tagger**](#film-credits-tagger)
- [**Video Trimmer**](#video-trimmer)

### General requirements

- Python 3.10+
- Python packages:
    ```shell
    pip install customtkinter reportlab pymupdf pillow svglib
    ```
- (*Other app-specific requirements noted in each app's section below.*)

<br>
<br>
<br>

# Film Credits Tagger<a href="#film-credits-tagger"><img src="./src/film_credits_tagger/assets/img/FilmCreditsTagger.svg" height="36" align="right" /></a>

A small desktop app for tagging film credits and metadata into video files – powered by [**ExifTool**](https://exiftool.org).

> <br>
> <b>Quick app launch:</b><br>
> ❯  On <b>Windows</b>, double-click <code>film-credits-tagger.vbs</code><br>
> ❯  On <b>macOS/Linux</b>, right-click <code>film-credits-tagger.sh</code> and choose «Run in terminal»<br>
> <br>
> (<i>Or manually run</i> <code>src/film_credits_tagger/app.pyw</code> <i>with Python.</i>)
> <br>
> <br>

### Features

- **Write metadata** into `.mp4`, `.mov`, `.m4v`, `.m4a`, `.3gp`, and `.3g2` files.
- **Batch processing** – Select multiple files and apply the same tags to all at once.
- **Editable fields:** A variety of properties covering general info, credits, and descriptions.
- **Cover art** – Select an image, preview it in-app, and embed it as front-cover art.
- **JSON templates** – Save the current field values to a `.json` file and reload them later.
- **Load from video** – Reads existing metadata and cover art back out of a file and populates the fields.
- **Clear-empty toggle** – When enabled, fields left blank actively *delete* the corresponding tags<br>
    from the file instead of leaving them untouched.
- **Cross-platform tags** – Writes both iTunes/QuickTime atoms (*recognized by macOS, VLC, mpv*)<br>
    and Windows-specific tags (*recognized by Windows Explorer and WMP*) simultaneously.

### Requires

- [**ExifTool**](https://exiftool.org) installed and available on `PATH`

<br>
<br>
<br>

# Video Trimmer

…
