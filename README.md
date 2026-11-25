# 🔮 Horoscope API

A lightweight REST API that serves daily horoscope data for all 12 zodiac signs. It scrapes [AstroTalk](https://astrotalk.com) using a stealth browser fetcher with adaptive XPath learning, stores results as flat JSON files, and exposes them via FastAPI.

---

## ✨ Features

- Daily horoscope data for all 12 zodiac signs
- Rich per-sign payload: general reading, love, finance, career, health, lucky number, auspicious time, mood, tarot card, lucky stone, ruling planets & symbol
- Adaptive XPath scraping — learns and self-corrects element selectors over time
- Cloudflare bypass & ad-blocking via `scrapling`
- Resilient fetcher — up to 5 retries per page with 120s back-off between attempts
- Polite scraping — random 3–6s delay between page fetches
- Circuit breaker — aborts the run if 2 signs fail consecutively (site likely down)
- Idempotent runs — skips signs already scraped for today
- Atomic file writes — `.tmp` swap prevents half-written data on crash
- IST-aware date handling
- Stale-data flag in responses so consumers know if today's data is ready

---

## 🗂️ Project Structure

```
Horoscope-API/
├── main.py          # FastAPI app & route definitions
├── scraper.py       # Scraping logic, retry/resilience, data validation
├── data/
│   ├── {sign}.json          # One JSON file per zodiac sign
│   └── adaptive_storage.db  # Scrapling adaptive XPath cache
├── requirements.txt
└── pyproject.toml
```

---

## 🚀 Getting Started

### Prerequisites

- Python ≥ 3.14
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### Install

```bash
# with uv
uv sync

# or with pip
pip install -r requirements.txt
```

### Run the scraper (populate the data files)

```bash
python scraper.py
```

The scraper exits with code `0` if all 12 signs were scraped successfully, or `1` if any sign is missing data for today.

### Start the API server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

---

## 📡 API Reference

### `GET /horoscope/{sign}`

Returns today's horoscope for the given zodiac sign.

**Path parameter:** `sign` — one of `aries`, `taurus`, `gemini`, `cancer`, `leo`, `virgo`, `libra`, `scorpio`, `sagittarius`, `capricorn`, `aquarius`, `pisces`

**Example request:**
```
GET /horoscope/aries
```

**Example response:**
```json
{
  "stale": false,
  "data": {
    "sign": "aries",
    "date": "2025-07-14",
    "horoscope": "Today brings a surge of energy...",
    "love": "Your relationship deepens...",
    "finance": "A good day to review investments...",
    "career": "Focus and clarity will help you...",
    "health": "Stay hydrated and take short breaks...",
    "lucky_number": "7",
    "auspicious_time_ist": "11:00 AM – 12:30 PM",
    "mood": "Optimistic",
    "ruling_planets": "Mars",
    "symbol": "Ram",
    "tarot_card": "The Emperor",
    "lucky_stone": "Ruby"
  }
}
```

| Field | Description |
|---|---|
| `stale` | `true` if the stored data is not from today (IST) |
| `data` | Full horoscope payload for the requested sign |

**Error responses:**

| Status | Meaning |
|---|---|
| `422` | Invalid zodiac sign |
| `503` | Scraper hasn't run yet / no data file found |

---

## ⚙️ How It Works

```
scraper.py runs (cron / manual)
    │
    ├── Skips signs already scraped for today (idempotent)
    ├── Fetches 5 pages per sign (general, love, finance, career, health)
    │     └── Retries up to 5× per page with 120s back-off on failure
    ├── Extracts fields via adaptive XPath (learns correct selectors over time)
    ├── Validates each field (length checks, digit presence, etc.)
    ├── Rejects partial results — all required fields must pass validation
    ├── Writes result atomically to data/{sign}.json via .tmp swap
    └── Aborts early if 2 consecutive signs fail (circuit breaker)

main.py (FastAPI)
    └── GET /horoscope/{sign} → reads data/{sign}.json, flags if stale
```

---

## 🛡️ Resilience Details

| Behaviour | Value |
|---|---|
| Max retries per page | 5 |
| Wait between retries | 120s |
| Delay between pages | 3–6s (random) |
| Consecutive-failure abort | 2 signs |
| Partial-result guard | all 5 required fields must pass validation |
| Atomic writes | `.tmp` → rename, no corrupt files on crash |

---

## 🛠️ Tech Stack

| | |
|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Scraping** | [Scrapling](https://github.com/D4Vinci/Scrapling) (stealth + adaptive XPath) |
| **Storage** | Flat JSON files (one per sign) |
| **Server** | Uvicorn |
| **Timezone** | IST (`Asia/Kolkata`) via `zoneinfo` |
| **Python** | ≥ 3.14 |

---

## 📋 Interactive Docs

FastAPI auto-generates interactive documentation:

- Swagger UI → `http://127.0.0.1:8000/docs`
- ReDoc → `http://127.0.0.1:8000/redoc`
