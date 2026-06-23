# Parkinson's Digest

A Django app that aggregates Parkinson's disease clinical trials, research papers, and news into a single filterable feed.

**Live site:** https://parkinsonsdigest.org/

## Local setup

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/), and a PostgreSQL database with the PostGIS extension. The `docker compose` step below is the easy way to get one. If you already run Postgres+PostGIS locally, skip it and point `DATABASE_URL` at your own database.

```bash
docker compose up -d        # optional: PostGIS on localhost:5433
uv sync
cp .env.example .env        # then fill in values (see below)
cp config/settings_local.example.py config/settings_local.py   # optional local overrides
uv run manage.py migrate
uv run manage.py runserver
```

### Environment

`.env`

```
DATABASE_URL=postgres://postgres:postgres@localhost:5433/parkinsons_digest
OPEN_WEATHER_API_KEY=...     # OpenWeather Geocoding API, for zip-code -> lat/lon
```

`OPEN_WEATHER_API_KEY` is only needed for the zip-code trial-location filter. Get a free key from [OpenWeather](https://openweathermap.org/api/geocoding-api).

## Sources & ingesting data

Each source ingests into its own model (`Trial`, `Paper`, `Article`), unified by a `FeedItem` row so the feed can sort and paginate across all three.

| Source | What | Command |
| --- | --- | --- |
| **Clinical trials** | [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api) | `uv run manage.py ingest_trials` |
| **Research papers** | PubMed ([NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)) | `uv run manage.py ingest_papers` |
| **News/blogs** | a fixed list of RSS feeds (see `ingest/management/commands/ingest_rss.py`) | `uv run manage.py ingest_rss` |

```bash
uv run manage.py ingest    # runs all three
```

These are idempotent, so they're safe to run on a schedule.

## Tests

```bash
uv run manage.py test
```

## Linting & formatting

[Ruff](https://docs.astral.sh/ruff/) for Python, [djLint](https://djlint.com/) for templates:

```bash
uv run ruff check .
uv run ruff format .
uv run djlint feed --reformat
```
