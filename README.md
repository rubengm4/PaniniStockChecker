# Panini World Cup 2026 stock monitor (Spain)

CLI that checks configured product URLs on **panini.es**, **paninistore.com**, **El Corte Inglés**, **Juguettos**, **Toy Planet**, and **Amazon.es**, and sends a **Telegram** message when something becomes **buyable** (not preorder-only).

Alerts fire only on **status change** (e.g. unavailable → buyable), so you are not spammed on every run.

## Quick start

```bash
cd panini_scrapper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # fallback if sites block plain HTTP

cp .env.example .env
# Edit .env: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

python -m src check --dry-run   # first run: no Telegram, seeds state DB
python -m src list
python -m src check             # real run
```

## Telegram setup

1. Open [@BotFather](https://t.me/BotFather) → `/newbot` → copy the **bot token**.
2. Start a chat with your bot (Send `/start`).
3. Open [@userinfobot](https://t.me/userinfobot) → copy your numeric **chat id**.
4. Put both in `.env` (local) or GitHub repository **Secrets** for Actions:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

## Configure watches

Edit [`config/watchlist.yaml`](config/watchlist.yaml):

```yaml
checks:
  - id: my_watch
    store: panini_es   # panini_es | paninistore | eci | juguettos | toyplanet | amazon_es
    label: "Human-readable name"
    url: "https://..."
    enabled: true      # false to skip
```

Product ideas for Spain: [panini.es FIFA World Cup category](https://www.panini.es/shp_esp_es/cromos-coleccionables/deporte/fifa-world-cuptm.html).

### Amazon.es

1. Search on Amazon.es for the exact product (e.g. `Panini álbum mundial 2026`).
2. Open the product page and copy the URL (`/dp/ASIN` or `/gp/product/...`).
3. Add an entry with `store: amazon_es`.
4. **Note:** Amazon often blocks cloud IPs. If checks return `unknown` / CAPTCHA in GitHub Actions, run Amazon watches from your Mac (`cron` below) or disable them in the workflow and keep panini.es only.

### El Corte Inglés

1. Search on [elcorteingles.es](https://www.elcorteingles.es) for `Panini mundial 2026` (or similar).
2. Copy the **product page** URL (not search results; drop `?utm_...` tracking params).
3. Add an entry with `store: eci`.

ECI often returns **403** from datacenter IPs. Use **Mac cron** for ECI if GitHub Actions shows `unknown` for those watches.

### Juguettos / Toy Planet

Add product URLs with `store: juguettos` or `store: toyplanet`. Online buyable = can add to cart on the website (not “solo en tienda física”).

## Commands

| Command | Description |
|---------|-------------|
| `python -m src check` | Run all enabled checks, update state, send Telegram on new buyable |
| `python -m src check --dry-run` | Same checks, no Telegram |
| `python -m src test-telegram` | Send a test message to your Telegram chat |
| `python -m src list` | Show last status per watch |

## GitHub Actions (every 15 minutes)

Workflow: [`.github/workflows/check-stock.yml`](.github/workflows/check-stock.yml)

1. Push this repo to GitHub.
2. Add secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
3. Enable Actions on the repo. Use **Actions → Check Panini stock → Run workflow** to test.

State is kept in an Actions **cache** (`data/state.db`) so transitions are detected between runs.

## Mac cron (optional)

```cron
*/10 * * * * cd /Users/you/panini_scrapper && .venv/bin/python -m src check >> /tmp/panini-check.log 2>&1
```

Useful for Amazon checks from a residential IP.

## Troubleshooting

| Symptom | What to do |
|---------|------------|
| `unknown` / fetch errors | Site may block the IP; install Playwright; try from home network |
| Amazon `CAPTCHA` | Disable Amazon in `watchlist.yaml` for GitHub; check locally |
| ECI `unknown` / blocked | Run from home IP (Mac cron); ECI blocks many cloud bots |
| Juguettos “solo en tiendas” | Treated as unavailable for online alerts |
| No Telegram but `buyable` in logs | Set `TELEGRAM_*` in `.env` or GitHub secrets |
| No alert when site looks in stock | We only alert on **buyable**, not preorder; first run never alerts (no previous state) |
| Too many sites slow the job | Reduce entries or increase delay in `src/runner.py` |

## Legal

Personal, low-frequency checks on URLs you configure. Not for bypassing queues or retailer anti-bot systems.
