# Development and validation

> **Language:** English · [Italiano](it/SVILUPPO.md) · [Back to README](../README.md)

## Supported environment

- Python 3.11+ (the CI suite runs on 3.11, 3.12 and 3.13)
- PostgreSQL for interactive/manual integration testing
- Python dependencies installed from `requirements.txt`

The source tree is run directly from the repository root: it is not currently packaged as a `pip install`-able distribution.

## Local setup

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Activate `.venv` for your operating system as documented in the [README](../README.md#quick-start).

## Test suite

```bash
python -m unittest discover -s tests -v
```

The automated suite uses stubs and simulated PostgreSQL behavior, so it does not require a live database. It covers controller behavior, model validation, CSV parsing, SQL construction, employee edits and transaction handling.

**Test scope:** these are unit tests and mocks, *not* an automated end-to-end check against a real PostgreSQL server.

Validate Markdown relative links with the dependency-free checker:

```bash
python scripts/check_docs_links.py
```

GitHub Actions runs both checks on pull requests and pushes to `main`.

## Manual PostgreSQL verification

Use a dedicated throwaway database; never run destructive tests against real records.

1. Initialize an empty database through `python main.py`.
2. Create a branch, customer and account; confirm the records exist using SQL while the app is open.
3. Deposit funds and verify the new movement and updated balance.
4. Attempt an overdraft and verify there is no committed movement or balance change.
5. Create and approve financing, then verify a second approval is rejected.
6. Import and export sample data, inspect counts and verify no repeated financial events.
7. Restart the application to verify persistence.

Additional read-only SQL checks: [`sql/VERIFICA_IMPORT.sql`](sql/VERIFICA_IMPORT.sql).

## Module ownership

| Package | Responsibility |
| --- | --- |
| `models/` | Domain entities, contracts, enums and exceptions |
| `views/` | Console input/output and navigation |
| `controllers/` | Workflow coordination and validation |
| `repository/` | SQL queries, persistence and transactions |
| `services/` | CSV import/export and Pandas analysis |
| `scripts/` | Dataset generation and documentation checks |
| `tests/` | Regression tests |

See [Architecture](ARCHITECTURE.md) for the request flow and invariants.

## Conventions

- The console and domain model names remain in Italian for consistency with existing code.
- New public-facing documentation is written in English, with complete Italian translations under `docs/it/`.
- Do not treat CSV files or in-memory models as independent persistent stores.
- Changes to financial operations should preserve database transactions and account row locking.
- Never commit secrets, customer data, exported charts or local DB files.

See [Contributing](../CONTRIBUTING.md) and [Security](../SECURITY.md).
