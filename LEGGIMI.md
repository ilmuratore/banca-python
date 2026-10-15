<div align="center">

![Banca Python — gestionale bancario Python e PostgreSQL](assets/banner.svg)

# Banca Python

**Simulatore gestionale bancario da terminale, sviluppato in Python con PostgreSQL e analisi Pandas.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Test](https://github.com/ilmuratore/banca-python/actions/workflows/tests.yml/badge.svg)](https://github.com/ilmuratore/banca-python/actions/workflows/tests.yml)

**[English README](README.md)** · [Architettura](docs/ARCHITECTURE.md) · [Dataset dimostrativi](docs/DATASETS.md)

</div>

## Il progetto

Banca Python è un'applicazione a menu che simula la gestione di una o più filiali bancarie. Il progetto riunisce **programmazione a oggetti, architettura MVC, PostgreSQL, transazioni SQL, file CSV e analisi dei dati con Pandas**.

Il database PostgreSQL è **l'unica fonte persistente dei dati**: ogni lettura avviene dal database e ogni modifica confermata viene salvata immediatamente. I CSV servono esclusivamente per importazioni ed esportazioni richieste dall'utente.

> [!IMPORTANT]
> È un **simulatore per portfolio e apprendimento**. Non è un prodotto bancario operativo e non è progettato per gestire informazioni finanziarie o personali reali.

## Funzionalità

| Modulo | Operazioni disponibili |
| --- | --- |
| Filiali | Creazione, selezione e modifica dei dati di filiale. |
| Clienti | Anagrafiche, ricerca e modifica clienti. |
| Dipendenti e ATM | Gestione del personale e degli sportelli automatici. |
| Conti correnti | Apertura, ricerca e modifica dei conti. |
| Operazioni | Versamenti, prelievi e consultazione dei movimenti. |
| Finanziamenti | Prestiti, mutui e approvazione/rifiuto delle richieste. |
| Investimenti | Registrazione e gestione delle operazioni d'investimento. |
| Import/export | CSV validati con conferma esplicita e transazioni SQL. |
| Pandas | Filtri, raggruppamenti, `merge`, tabelle pivot e grafici PNG. |

Il modulo Pandas produce grafici a barre, a torta, a linee e istogrammi. I grafici vengono salvati in `data/csv/CODICE_FILIALE/grafici/`.

## Tecnologie

**Python 3.11+**, PostgreSQL, psycopg 3, Pandas, Matplotlib e `unittest`.

La struttura del progetto separa `models/`, `views/`, `controllers/`, `repository/`, `services/`, `tests/` e `scripts/`. Il file `schema.sql` rimane nella radice perché è usato all'avvio dal repository PostgreSQL.

## Installazione

Clonare il repository e creare l'ambiente virtuale:

```bash
git clone https://github.com/ilmuratore/banca-python.git
cd banca-python
python -m venv .venv
```

Attivare l'ambiente in **PowerShell**:

```powershell
.\.venv\Scripts\Activate.ps1
```

Oppure in **Linux, macOS o Git Bash**:

```bash
source .venv/bin/activate
```

Installare le librerie:

```bash
python -m pip install -r requirements.txt
```

In PostgreSQL creare un database vuoto:

```sql
CREATE DATABASE banca;
```

Non è necessario eseguire a mano `schema.sql`: viene applicato all'avvio se non esistono ancora le tabelle previste. Uno schema parziale genera invece un errore, senza eliminare i dati esistenti.

### Collegamento a PostgreSQL

Le variabili d'ambiente disponibili sono:

| Variabile | Valore predefinito |
| --- | --- |
| `BANCA_DB_HOST` | `localhost` |
| `BANCA_DB_PORT` | `5432` |
| `BANCA_DB_NAME` | `banca` |
| `BANCA_DB_USER` | `postgres` |
| `BANCA_DB_PASSWORD` | `postgres` |

Impostare la propria password locale e avviare:

```powershell
# PowerShell
$env:BANCA_DB_PASSWORD="password-del-tuo-db"
python main.py
```

```bash
# Git Bash / Linux / macOS
export BANCA_DB_PASSWORD='password-del-tuo-db'
python main.py
```

Il programma **non legge automaticamente** un file `.env`. La variabile `BANCA_NO_CLEAR=1` disattiva la pulizia del terminale.

## Prima esecuzione e demo

1. Creare una filiale oppure selezionarne una già presente. Se la filiale è unica, viene selezionata automaticamente.
2. Creare clienti, dipendenti e conti, oppure usare i CSV sintetici di esempio.
3. Per la demo creare la filiale `FIL001`, poi aprire **8. Import / Export CSV → 2. Importa CSV entità**.
4. Importare nell'ordine `dipendenti`, `atm`, `clienti`, `conti`, `movimenti`, `finanziamenti`, `investimenti`.
5. Aprire il menu **9. Pandas** per analizzare dati e generare i grafici.

I CSV già inclusi in [`data/csv/FIL001/`](data/csv/FIL001/) contengono **1.400 record completamente inventati** (200 per ciascuna delle sette entità). Gli ID possono entrare in conflitto con dati già esistenti: usare un database di prova e fare un backup prima di importare.

Generare ulteriori dataset:

```bash
python scripts/genera_dataset.py --filiale FIL002 --record 200
```

Per formati, intestazioni, import e personalizzazione degli ID consultare [la guida ai dataset](docs/DATASETS.md).

## Test

```bash
python -m unittest discover -s tests -v
```

I test automatici utilizzano principalmente simulatori e non richiedono un database PostgreSQL attivo. Per un collaudo con database reale è necessaria un'ulteriore verifica manuale: consultare [l'architettura](docs/ARCHITECTURE.md) e le [query SQL](docs/sql/VERIFICA_IMPORT.sql).

## Licenza

Il progetto è distribuito con licenza [MIT](LICENSE). © 2026 Simone Iengo.
