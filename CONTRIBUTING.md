# Contributing

This repository is a portfolio project and an educational banking simulation. Small, focused contributions that improve correctness, tests, documentation or usability are welcome.

## Local setup

Follow the [README](README.md) to create a virtual environment and install dependencies.

Run the unit tests before submitting a change:

```bash
python -m unittest discover -s tests -v
```

The unit test suite does not require a PostgreSQL server. Changes to SQL persistence or financial workflows should also be checked against a disposable PostgreSQL database, using the checklist in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Pull requests

- Create a dedicated branch and keep each PR limited to one topic.
- Describe what changes and how you validated it.
- Add or update tests when changing behavior.
- Never commit passwords, production financial data, locally exported CSVs or generated charts.
- Preserve the distinction between the PostgreSQL source of truth and explicit CSV import/export.

The codebase currently uses Italian names for most domain objects and menus. Respect existing naming conventions within related modules.
