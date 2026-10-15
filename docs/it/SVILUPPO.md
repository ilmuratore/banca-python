# Sviluppo e verifica

> **Lingua:** Italiano · [English](../DEVELOPMENT.md) · [Torna al LEGGIMI](../../LEGGIMI.md)

## Requisiti

- Python 3.11+; la CI esegue test su 3.11, 3.12 e 3.13
- PostgreSQL per esecuzione dell'app e collaudi manuali
- Dipendenze Python definite in `requirements.txt`

Il codice si esegue dalla radice della repository e attualmente non è distribuito come pacchetto installabile tramite `pip install .`.

## Ambiente locale

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Attivare l'ambiente come descritto nel [LEGGIMI](../../LEGGIMI.md#installazione).

## Test automatici

```bash
python -m unittest discover -s tests -v
```

I test usano mock e simulatori del database; non occorre avviare PostgreSQL. Verificano controller, validazioni, parsing CSV, query SQL, modifiche ai dipendenti e transazioni simulate.

**Attenzione:** non sostituiscono un collaudo end-to-end su PostgreSQL reale.

Controllare i collegamenti Markdown:

```bash
python scripts/check_docs_links.py
```

GitHub Actions esegue questi controlli su pull request e push verso `main`.

## Collaudo su PostgreSQL

Usare sempre un database **temporaneo**:

1. Avviare su database vuoto e verificare lo schema.
2. Creare filiale, cliente e conto e interrogare PostgreSQL.
3. Registrare un versamento e verificare movimento e saldo.
4. Tentare un prelievo eccessivo e verificare che non ci siano scritture.
5. Richiedere e approvare un finanziamento; una seconda approvazione deve fallire.
6. Importare/esportare CSV e verificare che le operazioni non si duplicano.
7. Riavviare per verificare la persistenza.

Le query SQL di verifica sono in [`VERIFICA_IMPORT.sql`](../sql/VERIFICA_IMPORT.sql).

## Moduli

| Cartella | Compito |
| --- | --- |
| `models/` | Entità, contratti, enum ed eccezioni |
| `views/` | Input/output e menu |
| `controllers/` | Flussi applicativi e validazioni |
| `repository/` | SQL, persistenza e transazioni |
| `services/` | CSV e Pandas |
| `scripts/` | Generatore dataset e controllo documentazione |
| `tests/` | Test di regressione |

Vedere [Architettura](ARCHITETTURA.md) per i dettagli.

## Convenzioni

- Menu e nomi del dominio restano in italiano per coerenza con il progetto.
- La documentazione principale è inglese, con traduzioni complete in `docs/it/`.
- PostgreSQL è l'unica fonte persistente; CSV e oggetti Python non devono costituire un secondo archivio.
- Le operazioni finanziarie devono mantenere transazioni e blocchi sulle righe dei conti.
- Non committare password, dati personali, grafici generati o file locali del database.

Vedere [Contribuire](CONTRIBUIRE.md) e [Sicurezza](SICUREZZA.md).
