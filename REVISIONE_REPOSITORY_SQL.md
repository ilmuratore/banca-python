# Revisione SQL del repository

- In `nuovo_dipendente()` sono previste 10 colonne e 10 argomenti Python: la query nel file inviato dall’utente usa gia **10 placeholder `%s`**, ed e corretta.
- Il repository originale aveva **11** placeholder, mentre il file inviato per la revisione ne contiene gia **10**, corretti.
- Aggiunti test automatici in `tests/test_repository_sql_audit.py`: controllano i conteggi nelle query statiche e simulano le query dinamiche delle principali funzioni.
- Le query `INSERT` a stringa costante sono state controllate anche nel numero di colonne/valori. Il file `schema.sql` resta invariato.

## Avvio test

Dalla cartella `banca`:

```bash
python -m unittest discover -s tests -v
```

## Nota

Il controllo non include un'istanza PostgreSQL reale. Verificare in DBeaver la creazione di un dipendente e le altre operazioni di scrittura prima di usare il progetto con gli studenti.
