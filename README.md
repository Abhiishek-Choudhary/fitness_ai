# Fitness AI — Backend

Django REST API for AI-assisted fitness: plan generation, calorie estimation from
food photos, push-up posture analysis, workout logging, gym discovery and
management, a content feed, and community features.

This repository is **backend only**. The web frontend is a separate project
deployed to Vercel and is not in this tree.

- Production: `https://fitness-ai-qa9m.onrender.com`
- Interactive API docs: `/api/docs/` (Swagger) and `/api/redoc/`
- OpenAPI schema: `/api/schema/`

## Stack

| | |
|---|---|
| Runtime | Python 3.12 (pinned in `.python-version`) |
| Framework | Django 4.2 LTS, Django REST Framework 3.15 |
| Auth | SimpleJWT (access 60 min, refresh 1 day, rotation + blacklist) |
| Database | Postgres in production, SQLite locally |
| AI | Google Gemini via `google-genai`, with fallback to an OpenAI-compatible gateway |
| Docs | drf-spectacular |
| Serving | gunicorn + WhiteNoise |
| Payments | Razorpay |

Python 3.12 is deliberate: Django 4.2 LTS is only supported through 3.12, and
Render now defaults new services to 3.14. Removing `.python-version` puts you on
an unsupported combination.

## Local setup

Python 3.12 is required. If `python` on your machine is older, invoke 3.12
explicitly (`py -3.12` on Windows).

```bash
py -3.12 -m venv venv
venv/Scripts/activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env           # then fill in the values below
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Generate a secret key for your `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

For local work set `DEBUG=True`. With `DEBUG=False` the app refuses to start
without `DJANGO_SECRET_KEY`, and it will try to redirect everything to HTTPS.

## Configuration

Every variable the project reads is listed in `.env.example`. `.env` is
gitignored and must stay that way.

### Required

| Variable | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | Startup fails without it unless `DEBUG=True`. |
| `DEBUG` | Defaults to `False`. Never `True` in production. |
| `ALLOWED_HOSTS` | Comma-separated. Defaults already include the Render host. |

### Database

| Variable | Notes |
|---|---|
| `DATABASE_URL` | Falls back to a local SQLite file when unset. |
| `DATABASE_SSL_REQUIRE` | Defaults to on for Postgres when `DEBUG` is off. Ignored for SQLite. |

### AI

| Variable | Notes |
|---|---|
| `GEMINI_API_KEYS` | Comma-separated, tried in order. Free-tier quota is per Google Cloud **project**, so extra keys only add headroom if they belong to different projects. |
| `GEMINI_MODEL` | Default `models/gemini-flash-latest`. |
| `AI_PROVIDERS` | Backend order, default `gemini,omniroute`. |
| `OMNIROUTE_BASE_URL` | OpenAI-compatible gateway URL. The backend is skipped entirely when unset. |
| `OMNIROUTE_MODEL` / `OMNIROUTE_API_KEY` | Default `auto` / `omniroute`. |
| `AI_REQUEST_TIMEOUT` | Seconds, default `60`. |

### Other integrations

| Variable | Notes |
|---|---|
| `YOUTUBE_API_KEY` | Content feed video ingestion. Needs YouTube Data API v3 enabled — a Generative Language key will not work here, and vice versa. |
| `NEWS_API_KEY` | Gym news feed. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP for gym campaign email. |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | The webhook returns `503` unless the webhook secret is set — it fails closed rather than trusting unverified payloads. |
| `LOG_LEVEL` | Root log level, default `INFO`. |

## Apps and routes

Mounted in `fitness_ai/urls.py`:

| Prefix | App | Purpose |
|---|---|---|
| `/api/accounts/` | `accounts` | Signup, login, logout, JWT refresh |
| `/api/fitness/` | `fitness` | Profile, calorie maths, AI plan generate/view/regenerate |
| `/api/workout/` | `workout` | Workout logging |
| `/workout/` | `workout_agent` | AI workout enrichment |
| `/api/calories/` | `calorie_ai` | Calorie estimation from a food photo |
| `/posture/` | `posture_ai` | Push-up upload and posture analysis |
| `/api/dashboard/` | `dashboard` | Aggregated user dashboard |
| `/api/reports/` | `reports` | PDF progress reports |
| `/api/gyms/` | `gyms` | Gym directory, members, campaigns, conversations |
| `/api/feed/` | `content_feed` | Posts, creators, categories, likes, saves |
| `/api/community/` | `community` | Events, groups, connections, nearby people |
| `/api/news/` | `gym_news` | Fitness news |
| `/api/payments/` | `payments` | Plans, orders, Razorpay webhook |

`/api/docs/` is the authoritative, always-current endpoint reference.

### Permissions

DRF defaults to `IsAuthenticated`. Anything public is explicitly marked
`AllowAny` or `IsAuthenticatedOrReadOnly` on the view. When adding a view,
assume it is private unless you opt out — this default is what closed several
accidental exposures, so don't change it globally.

### Throttling

`anon` 100/day, `user` 1000/day, and an `ai_endpoint` scope at 30/hour for the
expensive AI views. Clients should handle `429`.

## AI backend fallback

`fitness_ai/ai.py` is the single entry point for text and vision generation
(`generate(prompt, image_path=None)` plus `extract_json`). All four AI features
— calorie estimation, fitness plans, posture feedback, report analysis — go
through it.

Backends are built from `AI_PROVIDERS` and tried in order: each Gemini key in
turn, then an OmniRoute gateway if `OMNIROUTE_BASE_URL` is set. Clients are
constructed lazily and cached, so the project boots with nothing configured.

Fallback only happens on **capacity** errors — HTTP 429/503, or
`RESOURCE_EXHAUSTED`, `QUOTA`, `UNAVAILABLE`, `OVERLOADED`, `RATE LIMIT` in the
message. Anything else (a bad key, a malformed request) propagates immediately,
because it would fail identically on every backend and silently burning through
providers would hide the real bug.

Consequences worth knowing: these calls can take a while when they fall through
backends, so clients need generous timeouts, and output quality varies between
backends for identical input. See `frontend_integration.md`.

## Tests

```bash
python manage.py test
python manage.py check
DEBUG=False DJANGO_SECRET_KEY=... python manage.py check --deploy
```

## Deployment (Render)

The service is configured through the Render dashboard. A `render.yaml`
blueprint is included for reference if you ever recreate it.

**Build command** — `collectstatic` is not optional. `STATICFILES_STORAGE` is
WhiteNoise's `CompressedManifestStaticFilesStorage`, so templates that reference
a static file (Django admin, Swagger UI) raise at runtime if the manifest was
never built:

```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start command:**

```
gunicorn fitness_ai.wsgi:application
```

**Environment:** set at minimum `DJANGO_SECRET_KEY`, `DATABASE_URL`, and
`GEMINI_API_KEYS`. Leave `DEBUG` unset. Render exposes environment variables to
the build as well as the runtime, so a missing `DJANGO_SECRET_KEY` fails the
build, not just the boot.

Use the database's **Internal** connection URL — it only resolves from Render
services in the same region, and it keeps traffic off the public internet. The
External URL (`...render.com`) is for connecting from your laptop. Internal
Postgres uses self-signed certificates, so `sslmode=require` is the strongest
mode available; `verify-full` will not work.

Render terminates TLS at its proxy, which is why `SECURE_PROXY_SSL_HEADER` is
set. Without it Django sees plain HTTP behind the proxy and redirect-loops.

### Health check and keeping the free instance warm

`GET /healthz/` returns `{"status": "ok"}`. It is a plain Django view, not DRF,
because the DRF anonymous throttle is 100/day and anything polling more often
than every ~15 minutes would start getting `429`s. It is also intentionally
shallow: it does not touch the database, so a transient database problem cannot
fail Render's health check and send the service into a restart loop.

Free instances spin down after 15 minutes without inbound traffic and take about
a minute to wake. `.github/workflows/keepalive.yml` pings `/healthz/` every 10
minutes to prevent that.

The constraint to respect is that a free workspace gets **750 instance hours per
month, shared across all free services**, and a month is about 730 hours. Pinging
around the clock therefore consumes nearly the whole allowance, and when it runs
out every free service suspends until the next month. The workflow limits itself
to a daily window for that reason. Widen it only if this is the only free service
in the workspace.

A keep-alive is a workaround, not a fix — the paid Starter plan removes spin-down
outright and is the right answer if cold starts matter to users.

### Known production limitations

- **Uploaded media is ephemeral.** `MEDIA_ROOT` is local disk, so food photos,
  posture uploads and progress images are wiped on every deploy. Moving to
  object storage (S3/R2) is the real fix.
- **A local OmniRoute gateway is unreachable from Render.** `OMNIROUTE_BASE_URL`
  must be a publicly resolvable host, so fallback is effectively local-dev-only
  until the gateway is hosted somewhere Render can reach.
- Health data would transit third-party providers if routed through a shared
  gateway. Worth a privacy review before enabling it in production.

### Troubleshooting

| Symptom | Cause |
|---|---|
| `ImproperlyConfigured: DJANGO_SECRET_KEY must be set when DEBUG is off` during build | The variable is not set on the service. Dashboard → Environment → Add. A `PYTHON_VERSION`-style typo in the key name, or setting it on the wrong service or an unlinked environment group, produces the same error. |
| `ValueError: Missing staticfiles manifest entry` | `collectstatic` missing from the build command. |
| Infinite HTTPS redirects | `SECURE_PROXY_SSL_HEADER` lost, or `SECURE_SSL_REDIRECT` on without the proxy header. |
| Data disappears after deploy | Still on SQLite — `DATABASE_URL` is unset. |
| Build uses the wrong Python | A `PYTHON_VERSION` environment variable overrides `.python-version`. Remove it. |
