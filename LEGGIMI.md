# Dataset didattici — Banca PostgreSQL (200 record per entità)

I dati sono **interamente sintetici**. Sono costruiti per il progetto Banca MVC/DB-first del corso e rispettano il formato del suo `ServizioCSV`.

## Contenuto

| File | Record | Contenuto |
|---|---:|---|
| `dipendenti.csv` | 200 | Gestori, specialisti, addetti alla sicurezza |
| `atm.csv` | 200 | ATM attivi, in manutenzione e fuori servizio |
| `clienti.csv` | 200 | Anagrafiche, segmenti Standard/Premium/Business |
| `conti.csv` | 200 | Un conto per cliente, saldo iniziale a zero |
| `movimenti.csv` | 200 | 150 versamenti, 50 prelievi |
| `finanziamenti.csv` | 200 | 50 approvati, 75 richiesti, 75 rifiutati |
| `investimenti.csv` | 200 | Investimenti su conti finanziati con saldo disponibile |

**Totale: 1.400 record, sette CSV.** Il file `filiale.csv` non è incluso: il programma non permette di creare filiali importando CSV. Prima bisogna aver creato o selezionato una filiale dall'applicazione.

## 1. Impostare il codice filiale

I CSV già pronti si trovano in `data/csv/FIL001/` e si riferiscono a una filiale chiamata `FIL001`.

Se la filiale esistente nel database ha un altro codice, eseguire nella cartella in cui è presente `genera_dataset.py`:

```bash
python genera_dataset.py --filiale CODICE_REALE
```

Il programma crea `data/csv/CODICE_REALE/` con gli stessi sette file, coerenti fra loro.

Per generare i file direttamente nella cartella del progetto Banca:

```bash
python genera_dataset.py --filiale CODICE_REALE --out PERCORSO_BANCA/data/csv
```

I file di default possono essere importati anche indicando il percorso completo; non è necessario copiarli nel progetto.

## 2. Importazione dall'applicazione

Avviare il progetto Banca, selezionare la **filiale corretta** e usare:

**8. Import / Export CSV → 2. Importa CSV entità**

Ripetere la procedura rispettando **questo ordine**:

1. `dipendenti.csv`
2. `atm.csv`
3. `clienti.csv`
4. `conti.csv`
5. `movimenti.csv`
6. `finanziamenti.csv`
7. `investimenti.csv`

Il programma chiede conferma con `SI` prima di inserire o modificare i dati su PostgreSQL.

**Importante:** non modificare il saldo dei conti nel CSV: viene intenzionalmente impostato a `0,00` e il database lo calcola con le operazioni economiche. Importando prima i movimenti e i finanziamenti si garantiscono i fondi per gli investimenti.

## 3. Identificativi e database già popolato

Gli ID partono da:

- Clienti: `10001`
- Dipendenti: `20001`
- Conti: `30001`
- Operazioni: `40001` per movimenti, `41001` per finanziamenti e `42001` per investimenti.

Se alcuni ID sono già presenti nel DB, **non importare ciecamente**: gli ID coincidenti possono aggiornare record preesistenti (per anagrafiche e conti) oppure essere ignorati (per le operazioni). È consigliabile usare un database didattico di prova o cambiare gli intervalli degli ID:

```bash
python genera_dataset.py --filiale CODICE_REALE --base-clienti 110001 --base-dipendenti 120001 --base-conti 130001 --base-operazioni 140001
```

I codici fiscali sono **segnaposto sintetici**, conformi al controllo del model (16 caratteri alfanumerici), ma non corrispondono a codici fiscali reali. Le email usano `example.com` e i recapiti sono fittizi.

## 4. Formato compatibile con l'importatore

- Codifica: **UTF-8 con BOM** (`utf-8-sig`).
- Separatore: **punto e virgola** (`;`).
- Date: **gg/mm/aaaa**.
- Decimali: **virgola** (`3,50`).
- Booleani: `1` oppure `0`.
- Colonne esattamente nell'ordine richiesto dal repository.

I dati sono stati controllati tramite il parser `ServizioCSV`, le classi Model e una verifica dei saldi simulata. Non è stato eseguito un import reale su PostgreSQL in questo ambiente.

## 5. Verifica in DBeaver

Aprire `VERIFICA_IMPORT.sql`: contiene le query per contare i record, verificare chiavi esterne e saldi dopo l'importazione.

**Nota didattica:** 200 ATM e 200 dipendenti per una sola filiale non sono realistici; servono a testare filtri, elenchi e importazioni con molti record. Se si desidera una popolazione più ridotta, il generatore accetta `--record 20`, `--record 50`, ecc. (minimo 4 record).
