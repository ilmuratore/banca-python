# Dataset sintetici

> **Lingua:** Italiano · [English](../DATASETS.md) · [Torna al LEGGIMI](../../LEGGIMI.md)

La repository include dati **interamente fittizi** per provare il programma. Non contiene anagrafiche o informazioni bancarie reali.

## File disponibili

La cartella è [`data/csv/FIL001/`](../../data/csv/FIL001/).

| File | Record | Contenuto |
| --- | ---: | --- |
| `dipendenti.csv` | 200 | Gestori, specialisti e addetti alla sicurezza |
| `atm.csv` | 200 | ATM con differenti stati operativi |
| `clienti.csv` | 200 | Clienti inventati e segmenti |
| `conti.csv` | 200 | Un conto per cliente, saldo iniziale `0,00` |
| `movimenti.csv` | 200 | Versamenti e prelievi |
| `finanziamenti.csv` | 200 | Prestiti e mutui con differenti stati |
| `investimenti.csv` | 200 | Investimenti e profili di rischio |

**Totale: 1.400 record in sette CSV.** Non è previsto un file CSV iniziale per la filiale, che deve essere creata dall'applicazione.

## Importazione

1. Configurare PostgreSQL e avviare `python main.py`.
2. Creare o selezionare la filiale **`FIL001`**.
3. Aprire **`8. Import / Export CSV` → `2. Importa CSV entità`**.
4. Importare un file alla volta, confermando con `SI`.

**Ordine obbligatorio:** `dipendenti` → `atm` → `clienti` → `conti` → `movimenti` → `finanziamenti` → `investimenti`.

Il percorso predefinito è `data/csv/FIL001/<entita>.csv`; è possibile indicarne uno diverso.

> [!WARNING]
> Su un database già popolato, ID coincidenti possono aggiornare le anagrafiche o causare il salto di operazioni finanziarie già presenti. Usare un database dimostrativo isolato ed effettuare un backup prima dell'importazione.

## Generare nuovi dati

Dalla radice del progetto:

```bash
python scripts/genera_dataset.py --filiale BR001 --record 200
```

I CSV vengono generati in `data/csv/BR001/`. La filiale `BR001` deve esistere nel database prima dell'importazione.

```bash
python scripts/genera_dataset.py --filiale BR001 --record 50 --out data/csv
python scripts/genera_dataset.py --filiale BR001 --base-clienti 110001 --base-dipendenti 120001 --base-conti 130001 --base-operazioni 140001
```

`--record` accetta valori da 4 a 999. Il generatore usa un seed fisso per ottenere risultati riproducibili.

## ID e formato

| Entità | Primo ID |
| --- | ---: |
| Clienti | 10001 |
| Dipendenti | 20001 |
| Conti | 30001 |
| Movimenti | 40001 |
| Finanziamenti | 41001 |
| Investimenti | 42001 |

- Codifica: UTF-8 con BOM (`utf-8-sig`)
- Separatore: `;`
- Date: `gg/mm/aaaa`
- Decimali: virgola (`120,50`)
- Booleani: `1` e `0`
- Intestazioni: nomi e ordine esatti previsti da `ServizioCSV`

I codici fiscali, i recapiti e le email `example.com` sono sintetici. Il numero di ATM e dipendenti serve a esercitare importazioni e analisi, non a simulare la reale dimensione di una filiale.

Il campo `saldo` dei conti **non aggiorna il saldo nel database**: il saldo dipende dalle operazioni economiche. Le operazioni con ID già esistenti non vengono riapplicate.

## Verifiche SQL

Aprire [`VERIFICA_IMPORT.sql`](../sql/VERIFICA_IMPORT.sql) in DBeaver o in un altro client PostgreSQL. Sono query di sola lettura per controllare conteggi, saldi, movimenti e finanziamenti. Sostituire `FIL001` quando necessario.
