# 🔮 Horoscope API

A lightweight REST API that serves daily horoscope data for all 12 zodiac signs. It scrapes [AstroTalk](https://astrotalk.com) using a stealth browser fetcher with adaptive XPath learning, stores results in SQLite, and exposes them via FastAPI.

---

## ✨ Features

- Daily horoscope data for all 12 zodiac signs
- Rich per-sign payload: general reading, love, finance, career, health, lucky number, auspicious time, mood, tarot card, lucky stone, ruling planets & symbol
- Adaptive XPath scraping — learns and self-corrects element selectors over time
- Cloudflare bypass & ad-blocking via `scrapling`
- IST-aware date handling
- Stale-data flag in responses so consumers know if today's data is ready
- WAL-mode SQLite with automatic 7-day data retention

---

## 🗂️ Project Structure

```
Horoscope-API/
├── main.py          # FastAPI app & route definitions
├── scraper.py       # Scraping logic, DB helpers, data validation
├── data/
│   ├── horoscope.db         # Scraped horoscope storage
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

### Run the scraper (populate the DB)

```bash
python scraper.py
```

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
| `503` | Scraper hasn't run yet / no data available |

---

## ⚙️ How It Works

```
scraper.py runs (cron / manual)
    │
    ├── Fetches 5 pages per sign (general, love, finance, career, health)
    ├── Extracts fields via adaptive XPath (learns correct selectors over time)
    ├── Validates each field (length checks, digit presence, etc.)
    ├── Rejects partial results — all required fields must pass validation
    └── Stores JSON payload in SQLite (sign + date as primary key)

main.py (FastAPI)
    └── GET /horoscope/{sign} → reads latest row from DB, flags if stale
```

---

## 🛠️ Tech Stack

| | |
|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Scraping** | [Scrapling](https://github.com/D4Vinci/Scrapling) (stealth + adaptive XPath) |
| **Database** | SQLite (WAL mode) |
| **Server** | Uvicorn |
| **Timezone** | IST (`Asia/Kolkata`) via `zoneinfo` |
| **Python** | ≥ 3.14 |

---

## 📋 Interactive Docs

FastAPI auto-generates interactive documentation:

- Swagger UI → `http://127.0.0.1:8000/docs`
- ReDoc → `http://127.0.0.1:8000/redoc`
