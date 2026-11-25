import json
from enum import Enum
from fastapi import FastAPI, HTTPException
from scraper import db, today_ist

app = FastAPI(title="Horoscope-API")

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
    c = db()
    row = c.execute("SELECT data, day FROM horoscope WHERE sign=? ORDER BY day DESC LIMIT 1", (sign.value,)).fetchone()
    c.close()
    if not row:
        raise HTTPException(503, "No data yet")
    data, day = row
    return {"stale": day != today_ist(), "data": json.loads(data)}