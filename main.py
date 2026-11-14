"""Fenn translate-clipboard plugin. Stdlib only (tkinter for the clipboard).
Network: translate.googleapis.com free web endpoint (unofficial, no key). Your text is sent there."""
import json, os, sys, threading, urllib.parse, urllib.request

LANGS = [("English", "en"), ("Sinhala", "si"), ("Tamil", "ta"), ("Hindi", "hi"), ("Japanese", "ja"), ("Spanish", "es")]
DATA = os.environ.get("FENN_DATA_DIR") or os.environ.get("NOOK_DATA_DIR") or "."   # NOOK_DATA_DIR is the older name
CFG_PATH = os.path.join(DATA, "config.json")
out_lock, job_lock = threading.Lock(), threading.Lock()
cfg = {"lang": 0}
src = out = det = status = ""


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


def save_cfg():
    try:
        os.makedirs(DATA, exist_ok=True)
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except OSError as e:
        print("save failed:", e, file=sys.stderr)


def txt(text, **kw):
    return {"type": "text", "text": text, **kw}


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


def translate(text, tl):
    q = urllib.parse.urlencode({"client": "gtx", "sl": "auto", "tl": tl, "dt": "t", "q": text[:1500]})
    req = urllib.request.Request("https://translate.googleapis.com/translate_a/single?" + q,
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
    return "".join(s[0] for s in data[0] if s and s[0]), (data[2] if len(data) > 2 else "")


def render():
    name = LANGS[cfg["lang"]][0]
    tile = {"type": "row", "align": "center", "gap": 10, "children": [
        {"type": "icon", "icon": "translate", "size": 26, "color": "accent"},
        {"type": "column", "gap": 0, "children": [
            txt(f"{det or 'auto'} → {LANGS[cfg['lang']][1]}", size="small", color="dim"),
            txt(out[:40] if out else "Copy text, press Ctrl+Alt+Y", size="small", wrap=True)]}]}
    send({"type": "tile", "view": tile})
    cards = []
    if src:
        cards.append({"type": "card", "padding": 8, "gap": 2, "children": [
            txt("Original", size="small", color="dim"), txt(src[:300], size="small", wrap=True)]})
    if out:
        cards.append({"type": "card", "padding": 8, "gap": 2, "children": [
            txt(name, size="small", color="dim"), txt(out[:600], wrap=True)]})
    page = {"type": "column", "gap": 8, "scroll": True, "children": [
        {"type": "chips", "id": "lang", "options": [n for n, _ in LANGS], "selected": cfg["lang"]},
        {"type": "row", "align": "center", "gap": 8, "children": [
            {"type": "input", "id": "text", "value": "", "hint": "Or type here and press Enter", "width": 280},
            {"type": "spacer"},
            {"type": "button", "id": "go", "label": "Clipboard", "icon": "clipboard-text", "primary": True},
            {"type": "button", "id": "copy", "icon": "copy", "tooltip": "Copy translation"}]},
        *([txt(status, size="small", color="dim")] if status else []),
        *cards]}
    send({"type": "page", "view": page})


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
            out, det = translate(src, LANGS[cfg["lang"]][1])
            status = ""
        except Exception as e:
            status = f"Failed: {str(e)[:60]}"
            print("translate failed:", e, file=sys.stderr)
        render()
    finally:
        job_lock.release()


def bg(fn, *a):
    threading.Thread(target=fn, args=a, daemon=True).start()


def main():
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
                cfg["lang"] = int(v.get("index", 0))
                save_cfg()
                render()
                if src:
                    bg(job, src)
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
