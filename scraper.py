import os, json, re, logging, sys, time, random
from datetime import datetime
from zoneinfo import ZoneInfo
from scrapling import StealthyFetcher

log = logging.getLogger("scraper")
IST = ZoneInfo("Asia/Kolkata")
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(BASE, exist_ok=True)
ADAPTIVE_DB = os.path.join(BASE, "adaptive_storage.db")

StealthyFetcher.configure(adaptive=True, storage_args={"storage_file": ADAPTIVE_DB})

SIGNS = ["aries","taurus","gemini","cancer","leo","virgo","libra",
         "scorpio","sagittarius","capricorn","aquarius","pisces"]

RETRY_WAIT = 120            # seconds wait after bad fetch
MAX_TRIES = 5               # per page
PAGE_DELAY = (3, 6)         # polite random delay after good page
MAX_CONSEC_FAILS = 2        # abort run after N signs fail in a row

def today_ist() -> str:
    return datetime.now(IST).date().isoformat()

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
    for attempt in range(1, MAX_TRIES + 1):
        try:
            res = StealthyFetcher.fetch(
                url=url, block_ads=True, solve_cloudflare=True, timeout=60000
            )
            if res.status == 200:
                time.sleep(random.uniform(*PAGE_DELAY))
                return res
            reason = f"status {res.status}"
        except Exception as e:
            reason = f"{type(e).__name__}: {e}"
        if attempt == MAX_TRIES:
            raise RuntimeError(f"{url} failed after {MAX_TRIES} tries: {reason}")
        log.warning("%s %s, try %d/%d, wait %ds", url, reason, attempt, MAX_TRIES, RETRY_WAIT)
        time.sleep(RETRY_WAIT)

def scrape_sign(sign, day):
    u = lambda kind: f"https://astrotalk.com/horoscope/{kind}/{sign}"
    main = fetch(u("daily-horoscope"))
    love = fetch(u("daily-love-horoscope"))
    fin = fetch(u("daily-finance-horoscope"))
    car = fetch(u("daily-career-horoscope"))
    hlt = fetch(u("daily-health-horoscope"))

    g = "/html/body/div[3]/div/main/div/div[4]/div[1]/div/div[1]/div[3]/div/div/div"
    sub_p = "/html/body/div[3]/div/main/div/div[4]/div[1]/div[1]/p"
    d = {
        "sign": sign, "date": day,
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

def sign_path(sign):
    return os.path.join(BASE, f"{sign}.json")

def is_done(sign, day) -> bool:
    try:
        with open(sign_path(sign), encoding="utf-8") as f:
            return json.load(f).get("date") == day
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def save(sign, d):
    tmp = sign_path(sign) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
    os.replace(tmp, sign_path(sign))   # atomic, no half-file on crash

def run() -> int:
    day = today_ist()
    consec = 0
    for sign in SIGNS:
        if is_done(sign, day):
            log.info("skip %s, done for %s", sign, day)
            continue
        try:
            save(sign, scrape_sign(sign, day))
            log.info("saved %s", sign)
            consec = 0
        except Exception:
            log.exception("scrape failed %s", sign)
            consec += 1
            if consec >= MAX_CONSEC_FAILS:
                log.error("%d signs failed in a row, site likely down, abort", consec)
                break
    return sum(1 for s in SIGNS if not is_done(s, day))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(1 if run() else 0)