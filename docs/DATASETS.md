# Dataset dimostrativi (CSV sintetici)

La repository include un set di CSV **completamente fittizi** destinati a esplorare le funzionalità del simulatore. Non contiene dati personali o bancari reali.

## File inclusi

I file si trovano in [`../data/csv/FIL001/`](../data/csv/FIL001/).

| File | Record | Contenuto |
| --- | ---: | --- |
| `dipendenti.csv` | 200 | Gestori, specialisti e addetti alla sicurezza |
| `atm.csv` | 200 | ATM con stati differenti |
| `clienti.csv` | 200 | Clienti e segmenti |
| `conti.csv` | 200 | Un conto per cliente, saldo iniziale `0,00` |
| `movimenti.csv` | 200 | Versamenti e prelievi |
| `finanziamenti.csv` | 200 | Richieste, approvazioni e rifiuti |
| `investimenti.csv` | 200 | Investimenti con profili di rischio diversi |

**Totale: 1.400 righe su sette file.** La filiale non è inclusa: va creata dall'applicazione, non mediante CSV.

## Importazione dei dati inclusi

1. Avviare `python main.py` con PostgreSQL configurato.
2. Creare o selezionare la filiale identificata da **`FIL001`**.
3. Aprire **8. Import / Export CSV → 2. Importa CSV entità**.
4. Importare una per volta le entità nell'ordine indicato sotto, confermando con `SI`.

Ordine consigliato: **dipendenti → atm → clienti → conti → movimenti → finanziamenti → investimenti**.

Il menu propone come percorso predefinito `data/csv/FIL001/<entita>.csv`. Per una filiale diversa è possibile indicare un percorso personalizzato.

**Importante:** importare dati su un database già popolato può aggiornare record con ID coincidenti o ignorare operazioni già presenti. Usare un database di demo isolato ed eseguire un backup prima dell'importazione.

## Generare un nuovo dataset

Eseguire dalla directory principale della repository:

```bash
python scripts/genera_dataset.py --filiale BR001 --record 200
```

I file vengono scritti in `data/csv/BR001/`. La filiale `BR001` deve esistere già nel database per consentire l'importazione.

Parametri utili:

```bash
python scripts/genera_dataset.py --filiale BR001 --record 50 --out data/csv
python scripts/genera_dataset.py --filiale BR001 --base-clienti 110001 --base-dipendenti 120001 --base-conti 130001 --base-operazioni 140001
```

Il parametro `--record` accetta valori da 4 a 999. Il generatore usa un seed deterministico nel codice, così la produzione degli stessi dati risulta riproducibile.

## Identificativi e sicurezza dei dati

I dati predefiniti iniziano con:

| Tipo | Primo ID |
| --- | ---: |
| Clienti | 10001 |
| Dipendenti | 20001 |
| Conti | 30001 |
| Movimenti | 40001 |
| Finanziamenti | 41001 |
| Investimenti | 42001 |

I codici fiscali sono segnaposto alfanumerici sintetici; le email terminano in `example.com` e i recapiti sono inventati. **Non sono identità reali.** I 200 ATM e 200 dipendenti in una sola filiale sono volutamente sovradimensionati per esercitare import, query e analisi.

## Formato CSV

- Codifica: `utf-8-sig` (UTF-8 con BOM)
- Separatore: `;`
- Date: `gg/mm/aaaa`
- Decimali: `,` (es. `120,50`)
- Booleani: `1` e `0`
- Intestazioni: ordine e nomi esattamente previsti da `ServizioCSV`

Il saldo del conto contenuto nel CSV non viene applicato all'importazione; viene ricostruito dalle operazioni economiche. Gli ID di operazioni già presenti vengono ignorati, non riaccreditati o riaddebitati.

## Verifica in SQL

Aprire [`sql/VERIFICA_IMPORT.sql`](sql/VERIFICA_IMPORT.sql) in DBeaver oppure nel proprio client PostgreSQL. Le query sono in sola lettura e verificano conteggi, saldi, movimenti e stati dei finanziamenti. Sostituire il codice `FIL001` nelle query se si usa un'altra filiale.
