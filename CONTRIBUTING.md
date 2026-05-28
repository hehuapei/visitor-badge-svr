# Contributing

Thanks for your interest in this project.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start a local MySQL instance, then configure environment variables from `.env.example`.

Before starting the app, initialize the schema manually:

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p api-svr < schema.sql
```

Run the service:

```bash
python -m app.main
```

## Tests

```bash
pytest
```

## Style

This project keeps the codebase intentionally small and straightforward.

- Prefer small, readable modules over deep abstractions.
- Preserve endpoint behavior unless the change explicitly intends to alter it.
- Update tests and README together when behavior or setup changes.

## Pull requests

Please include:

- a short summary of the change
- the motivation for the change
- how you verified it
