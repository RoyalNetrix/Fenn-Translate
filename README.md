# Translate for Fenn

Translate whatever is on your clipboard from the Fenn notch.

## What it does

- Copy some text, then click **Clipboard** on the page (or press Ctrl+Alt+Y) and the translation appears. Opening the page never reads your clipboard.
- **Ctrl+Alt+Y** translates the clipboard from anywhere and opens the notch on the result.
- Target language chips: English, Sinhala, Tamil, Hindi, Japanese, Spanish. The source language is detected automatically.
- A box to type text, and a button to copy the translation.

## Install

1. Copy this folder to `%APPDATA%\Fenn\plugins\translate\` so that `plugin.toml` and `main.py` sit directly inside it.
2. In Fenn, open **Settings** and turn on **Plugin dev mode**. The tile appears within a few seconds, with no restart. (Without dev mode, restart Fenn.)
3. New tiles are added after the built-in ones, possibly on the second page. Use the pencil in the grid to move or resize it.

Requires Fenn with plugin support.

## Requirements

Python 3.8+ with `tkinter` (included in the standard python.org Windows installer) for reading the clipboard. No extra packages, no API key.

## Network and privacy

- `translate.googleapis.com`: Google Translate's free web endpoint.
- **Your text is sent to Google** (the first 1,500 characters), and only when you press the Clipboard button, press the hotkey, or submit the text box. Don't use it for passwords or private material.
- This is an unofficial endpoint and can change or stop working.

## Settings and data

- Target language is saved in `%APPDATA%\Fenn\plugin-data\translate\config.json`.
- Change the hotkey in `plugin.toml` (`hotkey = "ctrl+alt+KeyY"`) if it clashes with something.

## Limitations

- Long texts are cut to 1,500 characters and the page previews the first 600 characters of the result.
- More languages: edit the `LANGS` list at the top of `main.py` (name, code).

## Troubleshooting

- **Tile says "Stopped":** hover it to see the error and the last lines of the plugin's output.
- **Nothing happens:** make sure `python --version` works in a new PowerShell window. If it doesn't, install Python from python.org and tick "Add python.exe to PATH".
- **Full log:** The `.log` file in `%APPDATA%\Fenn\` has the plugin's errors.
- **Plugins are programs.** They run with the same rights as Fenn. Read the code (it is one short file) before installing any plugin.

## Credits and license

Translations come from Google Translate's free web endpoint, which is not an official API. Not affiliated with or endorsed by Google.

MIT. See `LICENSE`.

## Files

- `plugin.toml`: the plugin manifest.
- `main.py`: the whole plugin.
- `LICENSE`, `.gitignore`.
