# Progetto Banca — MVC e PostgreSQL

Refactor del progetto didattico. **PostgreSQL è l'unica fonte persistente dei dati**: non esiste più la distinzione tra dati caricati in memoria da CSV e dati sul database.

## Struttura

```text
banca_mvc/
├── main.py                          # Avvio e configurazione della connessione
├── runner.py                        # Creazione/selezione della filiale dimostrativa
├── models/                          # Un file per ciascuna classe del dominio
│   ├── persona.py, cliente.py, filiale.py
│   ├── gestore.py, specialista.py, direttore.py
│   ├── addetto_sicurezza.py, atm.py, conto_corrente.py
│   ├── operazione.py, movimento.py, versamento.py, prelievo.py
│   ├── finanziamento.py, prestito.py, mutuo.py, investimento.py
│   ├── contratti.py, enum.py, eccezioni.py
│   └── __init__.py
├── views/menu.py                    # Stampa menu, acquisizione input, presentazione risultati
├── controllers/banca_controller.py  # Flussi applicativi, permessi e coordinamento
├── repository/postgresql.py         # SELECT, INSERT, UPDATE, transazioni PostgreSQL
├── services/mapper.py               # Ricostruzione oggetti Python a partire dai record
├── services/csv_service.py          # Lettura/scrittura file CSV per singola entità
├── schema.sql                       # Schema SQL privo di DROP TABLE
├── requirements.txt
└── tests/                            # Test unitari senza server PostgreSQL
```

**Ruoli MVC:** i Model rappresentano entità, ereditarietà, validazioni e operazioni sugli oggetti; la View gestisce terminale e input; il Controller coordina operazioni e verifiche; il Repository esegue SQL; il servizio CSV gestisce solo import/export. La logica specifica delle transazioni bancarie è nel Repository, perché saldo e registrazione devono essere aggiornati insieme.

## Avvio

Occorrono **Python 3.10+** e **PostgreSQL** attivo, con un database denominato `banca` (crearlo prima in DBeaver/pgAdmin o tramite SQL `CREATE DATABASE banca;`).

Da terminale nella cartella del progetto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

La configurazione utilizza questi parametri predefiniti (come il precedente progetto): `localhost`, database `banca`, utente `postgres`, password `postgres`, porta `5432`. Si possono modificare con le variabili d'ambiente:

```powershell
$env:BANCA_DB_HOST="localhost"
$env:BANCA_DB_NAME="banca"
$env:BANCA_DB_USER="postgres"
$env:BANCA_DB_PASSWORD="la_tua_password"
$env:BANCA_DB_PORT="5432"
python main.py
```

Alla prima esecuzione su un database vuoto il programma crea lo schema. Se le otto tabelle esistono già, **non vengono cancellate né ricreate**. Se soltanto alcune tabelle sono presenti, il programma si ferma e richiede un intervento sullo schema: non elimina i dati.

## Utilizzo

Dal menu `1. Filiale` si può creare una filiale o selezionarne una esistente. Con `9` si crea/seleziona la filiale demo. Si possono poi inserire o modificare clienti, dipendenti, ATM e conti, effettuare operazioni, gestire finanziamenti/investimenti e consultare report.

**Ogni consultazione viene fatta sul database**. Ogni inserimento o modifica chiama il Repository; il risultato viene letto nuovamente dal database. Non serve più usare una voce «Salva nel database» e non esiste più «Carica CSV in memoria».

### CSV per singola entità

Menu `8. Import / Export CSV`:

1. **Esporta una entità:** si seleziona `filiale`, `dipendenti`, `atm`, `clienti`, `conti`, `movimenti`, `finanziamenti` oppure `investimenti`. I dati si leggono dal database e vengono esportati come `data/csv/CODICE_FILIALE/<entita>.csv`.
2. **Importa una entità:** si seleziona una delle stesse otto entità e il percorso del relativo CSV. L'importazione legge il file, verifica le colonne, controlla la filiale, scrive sul database in **una transazione unica** e verifica che gli oggetti restino ricostruibili.
3. **Mostra tracciati:** mostra i nomi dei campi. Il formato delle colonne e il separatore `;` restano compatibili con i CSV precedenti.
4. **Esporta tutte:** crea gli otto CSV individuali con un unico comando, ciascuno tratto dal database.

Le importazioni avvengono **solo per la filiale selezionata**. Per i dati di anagrafica: inserimento se la chiave non esiste, aggiornamento se esiste, **mai eliminazione automatica**. Non è possibile spostare con CSV un record appartenente a un'altra filiale. Per importare una nuova filiale con un suo direttore usare il menu di creazione.

**Regole di sicurezza contabile dei CSV:**
- Il campo `saldo` dei **conti già esistenti** non viene sovrascritto dall'importazione CSV. Per conti nuovi, il saldo del CSV è trattato come saldo iniziale importato.
- Le operazioni **già presenti** (`movimenti`, `finanziamenti`, `investimenti`) sono immutabili: se nel CSV è stato modificato un loro campo, l'importazione viene rifiutata e annullata per intero.
- Le **nuove operazioni storiche** importate via CSV vengono registrate come archivio e **non modificano automaticamente il saldo**. I saldi cambiano per operazioni eseguite dal programma; se si ricostruisce un archivio storico, occorre importare conti e operazioni coerenti tra loro. Non usare l'importazione CSV come sostituto delle operazioni di versamento/prelievo.
- Per nuove operazioni create dal menu, il saldo è aggiornato insieme al record in una **singola transazione SQL**, con blocco del conto (`FOR UPDATE`), verifica dello stato e saldo sufficiente.

**Ordine consigliato per importare dati in un database nuovo:** creare filiale con direttore dal menu, poi `dipendenti`, `atm`, `clienti`, `conti`, `movimenti`, `finanziamenti`, `investimenti`.

## Test

```powershell
python -m unittest discover -s tests -v
```

I test automatici inclusi coprono i modelli, la conversione e ricostruzione dei dati, gli otto CSV, e operazioni di base del Controller con un database simulato. **Non sostituiscono un test su un PostgreSQL reale**, che va eseguito nell'ambiente degli studenti.

## Nota sullo schema esistente

Il refactor mantiene tabelle e colonne dello schema precedente: `filiale`, `dipendente`, `atm`, `cliente`, `conto_corrente`, `movimento`, `finanziamento`, `investimento`. Non è necessario azzerare il database. Prima di collaudare con dati reali è comunque consigliabile eseguire un backup PostgreSQL.
