# Medaniyetler Köprüsü — Finance

Internal finance web app for **Medaniyetler Köprüsü** / **جمعية جسور الحضارات** (Civilizations Bridge Association). Users record **income (in)**, **expense (out)**, and see **available balance**, with a **description** on every transaction.

## Stack

- **Python 3.11+**, **Flask**, **PostgreSQL** (via `DATABASE_URL`), **Gunicorn** for production
- **English / Arabic / Turkish** UI (Arabic uses RTL)
- **Security**: password hashing (Werkzeug), CSRF (Flask-WTF), `HttpOnly` session cookies, `Secure` cookies when `RAILWAY_ENVIRONMENT` or `FLASK_ENV=production` is set

## Local run

```bash
cd "/Users/ahmedhassan/Desktop/medaniyetler hesaplar"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="dev-secret"
# Optional: export DATABASE_URL="postgresql://..."
python wsgi.py
```

Open http://127.0.0.1:5000 — register a user, then use the dashboard.

## Deploy on Railway

1. Create a new project and deploy from this repo (or connect GitHub).
2. Add a **PostgreSQL** plugin; Railway injects `DATABASE_URL` automatically.
3. Set a variable **`SECRET_KEY`** to a long random string (e.g. `openssl rand -hex 32`).
4. Start command is already defined in the **Procfile** (`gunicorn wsgi:app`).
5. Railway sets **`PORT`** and often **`RAILWAY_ENVIRONMENT`**; the app enables secure session cookies when those are present.

After deploy, open your Railway URL, **register** the first account(s), then use **Dashboard** to add transactions.

## Environment variables

| Variable        | Required | Description |
|----------------|----------|-------------|
| `SECRET_KEY`   | Yes (prod) | Flask session and CSRF signing |
| `DATABASE_URL` | Yes (prod) | PostgreSQL connection string |
| `PORT`         | Auto     | Set by Railway for Gunicorn |

## License

Use as needed for the association’s internal operations.
