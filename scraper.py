import os, sqlite3, json, re, logging
from datetime import datetime
from zoneinfo import ZoneInfo
from scrapling import StealthyFetcher
import sys

log = logging.getLogger("scraper")
IST = ZoneInfo("Asia/Kolkata")
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(BASE, exist_ok=True)
ADAPTIVE_DB = os.path.join(BASE, "adaptive_storage.db")
STORE_DB = os.path.join(BASE, "horoscope.db")

StealthyFetcher.configure(adaptive=True, storage_args={"storage_file": ADAPTIVE_DB})

SIGNS = ["aries","taurus","gemini","cancer","leo","virgo","libra",
         "scorpio","sagittarius","capricorn","aquarius","pisces"]

def today_ist() -> str:
    return datetime.now(IST).date().isoformat()

def db():
    c = sqlite3.connect(STORE_DB, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS horoscope(sign TEXT, day TEXT, data TEXT, PRIMARY KEY(sign, day))")
    return c

# sanity validators: catch wrong-element matches
VALID = {
    "horoscope": lambda t: len(t) > 80,
    "love": lambda t: len(t) > 40,
    "finance": lambda t: len(t) > 40,
    "career": lambda t: len(t) > 40,
    "health": lambda t: len(t) > 40,
    "lucky_number": lambda t: bool(re.search(r"\d", t)),
    "auspicious_time_ist": lambda t: bool(re.search(r"\d", t)),
}
REQUIRED = ["horoscope", "love", "finance", "career", "health"]

def extract(res, xpath, sign, field):
    ident = f"{sign}:{field}"
    els = res.xpath(xpath, adaptive=True, identifier=ident)
    if not els:
        return None
    text = els[0].get_all_text(strip=True) or None
    if not text:
        return None
    check = VALID.get(field)
    if check and not check(text):
        log.warning("validation failed %s", ident)
        return None
    # save baseline ONLY after validation passes
    res.xpath(xpath, auto_save=True, identifier=ident)
    return text

def fetch(url):
    res = StealthyFetcher.fetch(url=url, block_ads=True, solve_cloudflare=True, timeout=60000)
    if res.status != 200:
        raise RuntimeError(f"{url} status {res.status}")
    return res

def scrape_sign(sign):
    u = lambda kind: f"https://astrotalk.com/horoscope/{kind}/{sign}"
    main = fetch(u("daily-horoscope"))
    love = fetch(u("daily-love-horoscope"))
    fin = fetch(u("daily-finance-horoscope"))
    car = fetch(u("daily-career-horoscope"))
    hlt = fetch(u("daily-health-horoscope"))

    g = "/html/body/div[3]/div/main/div/div[4]/div[1]/div/div[1]/div[3]/div/div/div"
    sub_p = "/html/body/div[3]/div/main/div/div[4]/div[1]/div[1]/p"
    d = {
        "sign": sign, "date": today_ist(),
        "horoscope": extract(main, "/html/body/div[3]/div/main/div/div[4]/div[1]/div/div[1]/p", sign, "horoscope"),
        "lucky_number": extract(main, f"{g}/div[2]/div[2]", sign, "lucky_number"),
        "auspicious_time_ist": extract(main, f"{g}/div[3]/div[2]", sign, "auspicious_time_ist"),
        "mood": extract(main, f"{g}/div[4]/div[2]", sign, "mood"),
        "ruling_planets": extract(main, f"{g}/div[5]/div[2]", sign, "ruling_planets"),
        "symbol": extract(main, f"{g}/div[6]/div[2]", sign, "symbol"),
        "tarot_card": extract(main, f"{g}/div[7]/div[2]", sign, "tarot_card"),
        "lucky_stone": extract(main, f"{g}/div[8]/div[2]", sign, "lucky_stone"),
        "love": extract(love, sub_p, sign, "love"),
        "finance": extract(fin, sub_p, sign, "finance"),
        "career": extract(car, sub_p, sign, "career"),
        "health": extract(hlt, sub_p, sign, "health"),
    }
    missing = [k for k in REQUIRED if not d[k]]
    if missing:
        raise RuntimeError(f"{sign} missing {missing}")   # never store partial
    return d

def run() -> int:
    day = today_ist()
    c = db()
    failed = []
    for sign in SIGNS:
        try:
            d = scrape_sign(sign)
            c.execute("INSERT OR REPLACE INTO horoscope VALUES(?,?,?)", (sign, day, json.dumps(d)))
            c.commit()
        except Exception:
            log.exception("scrape failed %s", sign)
            failed.append(sign)
    c.execute("DELETE FROM horoscope WHERE day < date(?, '-7 day')", (day,))
    c.commit()
    c.close()
    return len(failed)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(1 if run() else 0)