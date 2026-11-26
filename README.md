# Translate for Fenn

Translate whatever is on your clipboard from the Fenn notch.

## What it does

- Copy some text, then click **Clipboard** on the page (or press Ctrl+Alt+Y) and the translation appears. Opening the page never reads your clipboard.
- **Ctrl+Alt+Y** translates the clipboard from anywhere and opens the notch on the result.
- Language chips show your six most recent languages (English, Sinhala, Tamil, Hindi, Japanese and Spanish to start). Type any other language in the box (`French`, `ur`, `Thai`) and it joins the chips. 43 languages are built in, and the source language is detected automatically.
- A box to type text, a button to copy the translation, and a **Copy result** switch that puts each translation on your clipboard automatically (off by default).
- Texts up to 4,500 characters are translated in pieces.
- If Google doesn't answer, the backup service MyMemory is used.

## Install

1. Copy this folder to `%APPDATA%\Fenn\plugins\translate\` so that `plugin.toml` and `main.py` sit directly inside it.
2. In Fenn, open **Settings** and turn on **Plugin dev mode**. The tile appears within a few seconds, with no restart. (Without dev mode, restart Fenn.)
3. New tiles are added after the built-in ones, possibly on the second page. Use the pencil in the grid to move or resize it.

Requires Fenn with plugin support.

## Requirements

Python 3.8+ (Fenn can set it up for you, or use your own) with `tkinter` (included in the standard python.org Windows installer) for reading the clipboard. No extra packages, no API key.

## Network and privacy

- `translate.googleapis.com`: Google Translate's free web endpoint. This is an unofficial endpoint and can change or stop working.
- `api.mymemory.translated.net`: MyMemory's free translation API, used **only if Google fails**. It takes smaller pieces of text and is less accurate.
- **Your text is sent to Google (or to MyMemory if Google fails)**, up to 4,500 characters, and only when you press the Clipboard button, press the hotkey, or submit the text box. Don't use it for passwords or private material.

## Settings and data

- Target language, recent languages and the Copy result switch are saved in `%APPDATA%\Fenn\plugin-data\translate\config.json`.
- Change the hotkey in `plugin.toml` (`hotkey = "ctrl+alt+KeyY"`) if it clashes with something.

## Limitations

- Texts over 4,500 characters are cut, and the page previews the first 600 characters of the result.
- The backup service handles about 1,500 characters and may be less accurate.
- With Copy result on, pressing the hotkey again translates the translation, because it is now on your clipboard.
- The built-in list has 43 languages. To add more, add `(name, code)` pairs to `LANGS` at the top of `main.py`.

## Troubleshooting

- **Tile says "Stopped":** hover it to see the error and the last lines of the plugin's output.
- **Nothing happens:** Fenn can set up Python for you. If that didn't work, make sure `python --version` works in a new PowerShell window, or install Python from python.org and tick "Add python.exe to PATH".
- **Full log:** the logs of the last ten Fenn runs are in `%APPDATA%\Fenn\logs`.
- **Plugins are programs.** They run with the same rights as Fenn. Read the code (it is one short file) before installing any plugin.

## Credits and license

Translations come from Google Translate's free web endpoint, which is not an official API. Not affiliated with or endorsed by Google.

MIT. See `LICENSE`.

## Files

- `plugin.toml`: the plugin manifest.
- `main.py`: the whole plugin.
- `LICENSE`, `.gitignore`.
