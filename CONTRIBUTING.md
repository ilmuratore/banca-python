# Contributing

> **Language:** English · [Italiano](docs/it/CONTRIBUIRE.md)

Banca Python is a personal portfolio project and an educational banking simulation. Small, well-scoped contributions that improve correctness, tests, documentation or usability are welcome.

## Setup and checks

Follow the [README](README.md#quick-start) to install the Python dependencies. Before opening a pull request, run:

```bash
python -m unittest discover -s tests -v
python scripts/check_docs_links.py
```

The unit tests do not need a live PostgreSQL server. Changes to persistence or financial flows should also be tested against a disposable PostgreSQL database using the checklist in [Development](docs/DEVELOPMENT.md).

## Pull requests

- Work in a dedicated branch; keep each pull request focused on one topic.
- Explain what changed and how you validated it.
- Add or update tests when changing behavior.
- Update both the English and Italian documentation when changing documented behavior.
- Never commit passwords, real financial/personal data, locally exported CSVs or generated charts.
- Preserve PostgreSQL as the source of truth; CSV operations are always explicit.

Domain identifiers and the terminal interface are primarily Italian; preserve existing conventions within related modules. See [Architecture](docs/ARCHITECTURE.md) and [Security](SECURITY.md).
