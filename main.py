"""Fenn translate-clipboard plugin. Stdlib only (tkinter for the clipboard).
Network: translate.googleapis.com (Google Translate's free web endpoint, unofficial), with
api.mymemory.translated.net as a backup if Google doesn't answer. Nothing is sent until you press
the Clipboard button, press the hotkey, or submit the text box."""
import html, json, os, sys, threading, urllib.parse, urllib.request

LANGS = [("English", "en"), ("Sinhala", "si"), ("Tamil", "ta"), ("Hindi", "hi"), ("Arabic", "ar"),
         ("Bengali", "bn"), ("Chinese (Simplified)", "zh-CN"), ("Chinese (Traditional)", "zh-TW"),
         ("Czech", "cs"), ("Danish", "da"), ("Dutch", "nl"), ("Finnish", "fi"), ("French", "fr"),
         ("German", "de"), ("Greek", "el"), ("Gujarati", "gu"), ("Hebrew", "iw"), ("Hungarian", "hu"),
         ("Indonesian", "id"), ("Italian", "it"), ("Japanese", "ja"), ("Kannada", "kn"), ("Korean", "ko"),
         ("Malay", "ms"), ("Malayalam", "ml"), ("Marathi", "mr"), ("Nepali", "ne"), ("Norwegian", "no"),
         ("Persian", "fa"), ("Polish", "pl"), ("Portuguese", "pt"), ("Punjabi", "pa"), ("Romanian", "ro"),
         ("Russian", "ru"), ("Spanish", "es"), ("Swahili", "sw"), ("Swedish", "sv"), ("Telugu", "te"),
         ("Thai", "th"), ("Turkish", "tr"), ("Ukrainian", "uk"), ("Urdu", "ur"), ("Vietnamese", "vi")]
NAMES = {code: name for name, code in LANGS}
OLD_CHIPS = ["en", "si", "ta", "hi", "ja", "es"]     # the first version stored an index into this list
BACKUP_CODES = {"iw": "he"}                          # MyMemory spells a few codes differently
CHUNK, MAX_CHUNKS = 1500, 3                          # characters per request, requests per translation

DATA = os.environ.get("FENN_DATA_DIR") or os.environ.get("NOOK_DATA_DIR") or "."   # NOOK_DATA_DIR is the older name
CFG_PATH = os.path.join(DATA, "config.json")
out_lock, job_lock = threading.Lock(), threading.Lock()
cfg = {"lang": "en", "recent": list(OLD_CHIPS), "autocopy": False}
src = out = det = status = note = ""


def send(msg):
    with out_lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def load_cfg():
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    if isinstance(cfg.get("lang"), int):              # settings saved by the first version
        cfg["lang"] = OLD_CHIPS[cfg["lang"]] if 0 <= cfg["lang"] < len(OLD_CHIPS) else "en"
    if cfg["lang"] not in NAMES:
        cfg["lang"] = "en"
    cfg["recent"] = [c for c in cfg.get("recent", OLD_CHIPS) if c in NAMES][:6] or list(OLD_CHIPS)
    if cfg["lang"] not in cfg["recent"]:
        cfg["recent"].insert(0, cfg["lang"])
        del cfg["recent"][6:]


def save_cfg():
    try:
        os.makedirs(DATA, exist_ok=True)
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except OSError as e:
        print("save failed:", e, file=sys.stderr)


def txt(text, **kw):
    return {"type": "text", "text": text, **kw}


def friendly(e):
    s = str(e)
    if any(k in s for k in ("11001", "getaddrinfo", "Name or service", "unreachable", "10051", "10065")):
        return "No internet"
    if "timed out" in s:
        return "Timed out"
    if "429" in s:
        return "Rate limited, try again soon"
    return s[:50]


def read_clip():
    import tkinter
    r = tkinter.Tk()
    r.withdraw()
    try:
        return r.clipboard_get()
    except tkinter.TclError:
        return ""
    finally:
        r.destroy()


def split_text(text, size):
    """Cuts long text at a line end, sentence end or space, never mid-word if it can help it."""
    parts = []
    while len(text) > size:
        cut = max(text.rfind("\n", 0, size), text.rfind(". ", 0, size), text.rfind(" ", 0, size))
        cut = size if cut < size // 3 else cut + 1
        parts.append(text[:cut])
        text = text[cut:]
    parts.append(text)
    return [p for p in parts if p.strip()]


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def google(text, tl):
    q = urllib.parse.urlencode({"client": "gtx", "sl": "auto", "tl": tl, "dt": "t", "q": text})
    data = fetch_json("https://translate.googleapis.com/translate_a/single?" + q)
    return "".join(s[0] for s in data[0] if s and s[0]), (data[2] if len(data) > 2 else "")


def mymemory(text, tl):
    """Backup service. Its free tier takes about 500 bytes per request, so the pieces are small."""
    tl = BACKUP_CODES.get(tl, tl)
    pieces = split_text(text[:CHUNK], 450 if text.isascii() else 150)
    outs = []
    for p in pieces:
        q = urllib.parse.urlencode({"q": p, "langpair": "Autodetect|" + tl})
        d = fetch_json("https://api.mymemory.translated.net/get?" + q)
        if int(d.get("responseStatus", 0)) != 200:
            raise ValueError(str(d.get("responseDetails", "backup service refused"))[:50])
        outs.append(html.unescape(d["responseData"]["translatedText"]))
    return " ".join(outs)


def translate_all(text, tl):
    """(translation, detected language code, service). Google first, MyMemory if Google fails."""
    chunks = split_text(text, CHUNK)[:MAX_CHUNKS]
    try:
        outs, detected = [], ""
        for c in chunks:
            o, d = google(c, tl)
            outs.append((o.rstrip(), c.endswith("\n")))
            detected = detected or d
        return "".join(o + ("\n" if nl else " ") for o, nl in outs).strip(), detected, "Google"
    except Exception as e:
        print("google failed, trying backup:", e, file=sys.stderr)
    return mymemory(text, tl), "", "MyMemory"


def find_lang(q):
    q = q.strip().lower()
    if not q:
        return None
    for name, code in LANGS:
        if q in (name.lower(), code.lower()):
            return code
    for name, code in LANGS:
        if name.lower().startswith(q):
            return code
    for name, code in LANGS:
        if q in name.lower():
            return code
    return None


def render():
    name, code = NAMES[cfg["lang"]], cfg["lang"]
    tile = {"type": "row", "align": "center", "gap": 10, "children": [
        {"type": "icon", "icon": "translate", "size": 26, "color": "accent"},
        {"type": "column", "gap": 0, "children": [
            txt(f"{det or 'auto'} → {code}", size="small", color="dim"),
            txt(out[:40] if out else "Copy text, press Ctrl+Alt+Y", size="small", wrap=True)]}]}
    send({"type": "tile", "view": tile})
    cards = []
    if src:
        cards.append({"type": "card", "padding": 8, "gap": 2, "children": [
            txt("Original" + (f" ({NAMES.get(det, det)})" if det else ""), size="small", color="dim"),
            txt(src[:300], size="small", wrap=True)]})
    if out:
        cards.append({"type": "card", "padding": 8, "gap": 2, "children": [
            txt(name, size="small", color="dim"), txt(out[:600], wrap=True)]})
    recent = cfg["recent"]
    page = {"type": "column", "gap": 8, "scroll": True, "children": [
        {"type": "chips", "id": "lang", "options": [NAMES[c] for c in recent],
         "selected": recent.index(cfg["lang"]) if cfg["lang"] in recent else 0},
        {"type": "row", "align": "center", "gap": 8, "children": [
            {"type": "input", "id": "langbox", "value": "", "hint": "Other language (French, ur, Thai...)", "width": 200},
            {"type": "spacer"},
            {"type": "toggle", "id": "autocopy", "value": bool(cfg["autocopy"]), "label": "Copy result"}]},
        {"type": "row", "align": "center", "gap": 8, "children": [
            {"type": "input", "id": "text", "value": "", "hint": "Or type here and press Enter", "width": 260},
            {"type": "spacer"},
            {"type": "button", "id": "go", "label": "Clipboard", "icon": "clipboard-text", "primary": True},
            {"type": "button", "id": "copy", "icon": "copy", "tooltip": "Copy translation"}]},
        *([txt(note, size="small", color="red")] if note else []),
        *([txt(status, size="small", color="dim")] if status else []),
        *cards]}
    send({"type": "page", "view": page})


def use_lang(code):
    global note
    cfg["lang"] = code
    if code not in cfg["recent"]:
        cfg["recent"].insert(0, code)
        del cfg["recent"][6:]
    note = ""
    save_cfg()
    render()
    if src:
        bg(job, src)


def job(text=None):
    global src, out, det, status
    if not job_lock.acquire(blocking=False):
        return
    try:
        if text is None:
            text = read_clip()
        if not text.strip():
            status = "Clipboard is empty"
            render()
            return
        src, status = text.strip(), "Translating…"
        render()
        try:
            out, det, service = translate_all(src, cfg["lang"])
            status = "Google didn't answer, so the backup service was used." if service == "MyMemory" else ""
            if len(src) > CHUNK * MAX_CHUNKS:
                status = (status + " " if status else "") + f"Long text: only the first {CHUNK * MAX_CHUNKS:,} characters were translated."
            if cfg["autocopy"]:
                send({"type": "copy", "text": out})
        except Exception as e:
            status = f"Failed: {friendly(e)}"
            print("translate failed:", e, file=sys.stderr)
        render()
    finally:
        job_lock.release()


def bg(fn, *a):
    threading.Thread(target=fn, args=a, daemon=True).start()


def main():
    global note
    try:
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass
    load_cfg()
    render()
    for line in sys.stdin:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        t = msg.get("type")
        if t == "event":
            i, v = msg.get("id"), msg.get("value")
            if i == "lang" and isinstance(v, dict):
                idx = int(v.get("index", 0))
                if 0 <= idx < len(cfg["recent"]):
                    use_lang(cfg["recent"][idx])
            elif i == "langbox" and msg.get("kind") == "submit":
                code = find_lang(str(v or ""))
                if code:
                    use_lang(code)
                else:
                    note = "No such language. Try the English name or its code."
                    render()
            elif i == "autocopy":
                cfg["autocopy"] = bool(v)
                save_cfg()
                render()
            elif i == "go":
                bg(job)
            elif i == "text" and msg.get("kind") == "submit" and str(v or "").strip():
                bg(job, str(v))
            elif i == "copy" and out:
                send({"type": "copy", "text": out})
        elif t == "hotkey":
            send({"type": "show"})
            bg(job)
        elif t == "shutdown":
            save_cfg()
            return


if __name__ == "__main__":
    main()
