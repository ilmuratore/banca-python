# Synthetic datasets

> **Language:** English · [Italiano](it/DATASET.md) · [Back to README](../README.md)

The repository contains a **fully synthetic dataset** for exploring the application. No real customer identities, financial information or bank accounts are included.

## Included files

All files are available in [`data/csv/FIL001/`](../data/csv/FIL001/).

| File | Rows | Description |
| --- | ---: | --- |
| `dipendenti.csv` | 200 | Bank employees, specialists and security staff |
| `atm.csv` | 200 | ATMs in different operational states |
| `clienti.csv` | 200 | Fictional customers and segments |
| `conti.csv` | 200 | One account per customer, starting balance `0,00` |
| `movimenti.csv` | 200 | Deposits and withdrawals |
| `finanziamenti.csv` | 200 | Loans and mortgages in different approval states |
| `investimenti.csv` | 200 | Investments with different risk profiles |

**Total: 1,400 records in seven CSV files.** Branch records are not part of the demo dataset; create a branch in the application before importing its data.

## Import the sample data

1. Configure PostgreSQL and launch the application with `python main.py`.
2. Create or select a branch with code **`FIL001`**.
3. Select **`8. Import / Export CSV` → `2. Importa CSV entità`**.
4. Import one file at a time, explicitly confirming with `SI`.

**Required order:** `dipendenti` → `atm` → `clienti` → `conti` → `movimenti` → `finanziamenti` → `investimenti`.

The default file path follows `data/csv/FIL001/<entity>.csv`. You can enter another path when prompted.

> [!WARNING]
> An import into an existing database may update matching nonfinancial IDs or skip previously imported financial-operation IDs. Use a disposable demo database and take a backup before importing.

## Generate more data

From the repository root:

```bash
python scripts/genera_dataset.py --filiale BR001 --record 200
```

This writes seven files under `data/csv/BR001/`. Create branch `BR001` in the application before importing them.

Additional examples:

```bash
python scripts/genera_dataset.py --filiale BR001 --record 50 --out data/csv
python scripts/genera_dataset.py --filiale BR001 --base-clienti 110001 --base-dipendenti 120001 --base-conti 130001 --base-operazioni 140001
```

`--record` supports 4–999 rows per file. The generator uses a fixed random seed, making equivalent runs reproducible.

## Identifiers and format

| Entity | First ID |
| --- | ---: |
| Customers | 10001 |
| Employees | 20001 |
| Accounts | 30001 |
| Movements | 40001 |
| Financing | 41001 |
| Investments | 42001 |

- Encoding: UTF-8 with BOM (`utf-8-sig`)
- Delimiter: semicolon (`;`)
- Dates: `dd/mm/yyyy`
- Decimal separator: comma (`120,50`)
- Booleans: `1` or `0`
- Headers: exact column names and order expected by `ServizioCSV`

Fictional fiscal-code placeholders, `example.com` email addresses and synthetic phone numbers are intentional. The size of the sample staff/ATM lists is intended for stress-free demo exploration, not realism.

The `saldo` field in imported account files **does not overwrite balances**. Account balances are produced by financial operations. Financial operations whose IDs already exist are not reapplied.

## Validate the import

Open [`sql/VERIFICA_IMPORT.sql`](sql/VERIFICA_IMPORT.sql) in DBeaver or another PostgreSQL client. The read-only queries inspect record counts, balances, movements and financing states. Replace `FIL001` if using another branch.
