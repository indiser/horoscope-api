import json
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Horoscope-API")
DATA = Path(__file__).parent / "data"
IST = timezone(timedelta(hours=5, minutes=30))

class ZodiacSign(str, Enum):
    aries = "aries"
    taurus = "taurus"
    gemini = "gemini"
    cancer = "cancer"
    leo = "leo"
    virgo = "virgo"
    libra = "libra"
    scorpio = "scorpio"
    sagittarius = "sagittarius"
    capricorn = "capricorn"
    aquarius = "aquarius"
    pisces = "pisces"

@app.get("/horoscope/{sign}")
def get_daily_horoscope(sign: ZodiacSign):
    f = DATA / f"{sign.value}.json"
    if not f.exists():
        raise HTTPException(503, "No data yet")
    data = json.loads(f.read_text(encoding="utf-8"))
    today = datetime.now(IST).date().isoformat()
    return {"stale": data.get("date") != today, "data": data}