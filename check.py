import os, requests
from playwright.sync_api import sync_playwright
import json

TOKEN = os.environ["TG_TOKEN"]
CHAT = os.environ["TG_CHAT"]
COOKIES = json.loads(os.environ["GF_COOKIES"])
DEBUG = os.environ.get("DEBUG") == "1"
STATE = "state/count.txt"
API = f"https://api.telegram.org/bot{TOKEN}"

def tg(text):
    requests.post(f"{API}/sendMessage", data={"chat_id": CHAT, "text": text}, timeout=30)

def tg_photo(path, caption):
    with open(path, "rb") as f:
        requests.post(f"{API}/sendPhoto", data={"chat_id": CHAT, "caption": caption},
                      files={"photo": f}, timeout=60)

def fix_cookie(c):
    ss = {"lax": "Lax", "strict": "Strict", "no_restriction": "None", "none": "None"}
    out = {"name": c["name"], "value": c["value"], "domain": c["domain"],
           "path": c.get("path", "/"), "secure": c.get("secure", True)}
    out["sameSite"] = ss.get(str(c.get("sameSite")).lower(), "Lax")
    if c.get("expirationDate"):
        out["expires"] = c["expirationDate"]
    return out

def read_count(page):
    sels = [os.environ.get("BELL_SELECTOR", "")] + [
        '[class*="badge"]', '[class*="Badge"]', '[class*="notification"] [class*="count"]']
    for s in sels:
        if not s:
            continue
        for el in page.query_selector_all(s):
            t = (el.inner_text() or "").strip()
            if t.isdigit():
                return int(t)
    return 0

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1366, "height": 768})
    ctx.add_cookies([fix_cookie(c) for c in COOKIES])
    page = ctx.new_page()
    page.goto("https://gameflip.com/", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)

    if DEBUG:
        page.screenshot(path="shot.png")
        tg_photo("shot.png", f"Test: okunan sayı = {read_count(page)}")

    count = read_count(page)
    b.close()

os.makedirs("state", exist_ok=True)
prev = int(open(STATE).read()) if os.path.exists(STATE) else 0
if count > prev:
    tg(f"Gameflip'te {count} okunmamış bildirim var, kontrol et.")
open(STATE, "w").write(str(count))
