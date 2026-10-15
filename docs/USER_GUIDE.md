# User guide

> **Language:** English · [Italiano](it/GUIDA_UTENTE.md) · [Back to README](../README.md)

Banca Python is a **terminal-based banking simulator**. The interactive menu and domain commands are in Italian; this guide explains them in English. It is not a real banking application.

## First launch

Complete the [installation steps](../README.md#quick-start), configure a reachable PostgreSQL database and run:

```bash
python main.py
```

On first launch, an empty database receives the application schema automatically. If there is exactly one existing branch, it is selected automatically; with multiple branches you need to choose one.

## Main menu

| Option | Original menu label | Purpose |
| --- | --- | --- |
| 1 | Filiali | Create, select or edit a branch |
| 2 | Clienti | Register, search and update customers |
| 3 | Dipendenti e ATM | Maintain personnel and ATMs |
| 4 | Conti correnti | Open and manage accounts |
| 5 | Operazioni | Deposits and withdrawals |
| 6 | Finanziamenti e investimenti | Financing decisions and investments |
| 7 | Ricerche e report | Record searches and database reports |
| 8 | Import / Export CSV | Manual CSV import and export |
| 9 | Pandas | Data analysis, aggregation and charts |
| 0 | Esci | Exit |

Menu options display their subcommands in the terminal. Use the displayed prompts: the application checks input and reports validation failures.

## A typical workflow

1. Open **Filiali** and create a branch (including the required initial branch details).
2. Open **Clienti** and register a customer.
3. Open **Conti correnti** to open an account for the customer.
4. Open **Operazioni** to make a deposit, then inspect the movement history.
5. Try withdrawing more than the available balance: the application should reject the operation without changing the account balance.
6. Review **Ricerche e report** or open **Pandas** for data analysis.

The application reads and writes directly to PostgreSQL; **there is no Save command**. Database operations are transactional.

## Using the supplied sample dataset

The included 1,400 fictitious records target branch code `FIL001`. To load them, first create/select branch `FIL001`, then import each CSV file from menu **8** in the precise order described in the [dataset guide](DATASETS.md). Use an isolated demo database.

## Pandas and chart exports

Menu **9** exposes customer and account previews, customer segmentation, balance thresholds, data quality checks, aggregated account balances, merged customer/account views, pivot summaries and chart exports.

The chart option writes PNG files under:

```text
data/csv/<BRANCH_CODE>/grafici/
```

Charts include customer segmentation (bar and pie), monthly movement volume (line) and account balances (histogram). This folder contains generated outputs and is ignored by Git.

## CSV import/export rules

- Export is initiated manually and reads the current PostgreSQL records.
- Import asks for the file path and explicit confirmation (`SI`).
- The importer requires exact headers and strict value formats.
- Account balances must not be edited through the exported `saldo` column.
- A rejected import is rolled back as one operation; existing economic operation IDs are not replayed.

See [Synthetic datasets](DATASETS.md) for formats, IDs and import order.

## Common issues

**Connection refused:** make sure PostgreSQL is running, the database exists and all `BANCA_DB_*` variables match your server. If using Docker Compose, use port `5433`, not the default `5432`.

**Schema partially initialized:** use a new empty demo database or investigate the existing schema. Startup intentionally does not delete tables or attempt a destructive repair.

**Data is not visible:** ensure the intended branch is selected and the CSV files were imported into that branch.

**Terminal output disappears:** set `BANCA_NO_CLEAR=1` before starting the program.

**Charts are not created:** check that the selected branch has the required customers, movements and account data.

For development and validation, refer to [Development](DEVELOPMENT.md) and [Architecture](ARCHITECTURE.md).
