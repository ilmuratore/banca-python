# Banca — applicazione terminale con PostgreSQL (DB-first)

## Principio di funzionamento

L'applicazione usa PostgreSQL come **unica fonte dei dati**. Non usa CSV o liste Python come archivi permanenti.

1. All'avvio si collega a PostgreSQL: se non riesce a connettersi, il programma **non parte**.
2. Se mancano tutte le tabelle, esegue `schema.sql` **senza eliminare dati esistenti**. Se mancano solo alcune tabelle, si interrompe e segnala uno schema parziale.
3. Legge le filiali presenti nel database. Se ce n'è una sola, la seleziona automaticamente. Se ci sono più filiali, sceglierne una dal menu **Filiali**. Se non ci sono filiali, crearne una.
4. A ogni comando la view chiede i dati al controller; il controller interroga il repository SQL. Nessuna lettura parte da CSV o da cache in memoria.
5. Le creazioni/modifiche e operazioni economiche vengono registrate direttamente nel database, con `COMMIT` per ogni operazione completata e `ROLLBACK` in caso di errore. **Non esiste un comando Salva**.
6. I CSV sono soltanto una funzione manuale e separata di import/export per entità.

## Struttura

```
banca/
  main.py
  requirements.txt
  schema.sql
  models/                         # classi didattiche, proprietà e validazioni
  views/menu.py                   # menu di terminale, lettura input, stampe
  controllers/banca_controller.py # azioni applicative e oggetti dei model
  repository/postgresql.py       # select/insert/update e transazioni
  services/csv_service.py        # file CSV, solo su comando esplicito
  tests/                          # verifiche automatiche
  data/csv/                       # cartella generata solo quando si esporta
```

## Preparazione ambiente

Usare Python 3.11+ e PostgreSQL avviato. In Windows, PowerShell o Git Bash:

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

Creare **il database `banca`**, non serve creare le tabelle manualmente:

```sql
CREATE DATABASE banca;
```

Le credenziali sono definite tramite variabili di ambiente con questi default: `BANCA_DB_HOST=localhost`, `BANCA_DB_PORT=5432`, `BANCA_DB_NAME=banca`, `BANCA_DB_USER=postgres`, `BANCA_DB_PASSWORD=postgres`.

Ad esempio in PowerShell:

```powershell
$env:BANCA_DB_HOST="localhost"
$env:BANCA_DB_NAME="banca"
$env:BANCA_DB_USER="postgres"
$env:BANCA_DB_PASSWORD="LA_TUA_PASSWORD"
python main.py
```

In Git Bash:

```bash
export BANCA_DB_PASSWORD='LA_TUA_PASSWORD'
python main.py
```

Per disabilitare la pulizia dello schermo durante test via pipe: `BANCA_NO_CLEAR=1`.

## Verifiche manuali indispensabili

1. Avviare `python main.py`, creare una filiale e un cliente, aprire un conto.
2. Verificare i nuovi record in DBeaver con `SELECT * FROM cliente;` e `SELECT * FROM conto_corrente;` **senza chiudere l'app**.
3. Eseguire un versamento di 100 euro, quindi `SELECT saldo FROM conto_corrente WHERE id_conto = ...;` e `SELECT * FROM movimento ORDER BY id_operazione DESC;`.
4. Uscire dal programma e riavviarlo: la filiale unica è selezionata automaticamente e i dati sono ancora presenti nei menu.
5. Provare un prelievo maggiore del saldo: deve fallire **senza** creare movimenti o alterare il saldo.
6. Creare una richiesta prestito, approvarla una volta, verificare l'aumento del saldo. Una seconda approvazione deve fallire.
7. Esportare una entità CSV e reimportarla per verificare che non crei duplicati. Provare un CSV malformato per verificare il rollback dell'intera importazione.

## Import/export CSV

CSV: UTF-8 con BOM, separatore `;`, date `gg/mm/aaaa`, decimali con `,`, booleani `1` / `0`.

Le entità sono: filiale, dipendenti, atm, clienti, conti, movimenti, finanziamenti, investimenti.

L'esportazione usa sempre `SELECT` PostgreSQL. L'importazione non è automatica: dal menu si sceglie entità, file e conferma con `SI`.

- Filiali: modificano solo i dati della filiale selezionata, **non** il direttore associato.
- Anagrafiche, personale, ATM, conti: nuovi record inseriti e record esistenti aggiornati; nessuna cancellazione automatica.
- Conti: il saldo del CSV **non** viene mai importato. Per nuovi conti il saldo iniziale è zero. Il saldo è gestito soltanto da operazioni economiche.
- Movimenti, finanziamenti, investimenti: ID già presenti sono saltati, **non riapplicati**; i nuovi record economici vengono applicati al conto con transazione SQL e relativi controlli. Per ricostruire un archivio da zero, importare nell'ordine: filiale creata dal menu, dipendenti, ATM, clienti, conti, movimenti, finanziamenti, investimenti. Alcuni investimenti storici potrebbero richiedere che i crediti precedenti siano già stati importati.
- Importazione di dati non validi: **rollback** di tutte le righe del file corrente, nessuna importazione parziale.
- L'esportazione dei conti riflette il saldo corrente in PostgreSQL; non modificare manualmente i saldi CSV per tentare di aggiornarlo.

**Attenzione:** i dati reali non devono essere importati in un ambiente didattico. Eseguire una copia di backup del database prima di importare CSV con operazioni economiche.

## Nota sui model

I `models` originali sono conservati come classi di dominio e validazione. Il controller costruisce istanze per validare input e regole didattiche, **senza** usare i loro attributi come stato persistente o riapplicare localmente gli effetti monetari. I saldi sono modificati esclusivamente nel repository PostgreSQL sotto `SELECT ... FOR UPDATE`, per evitare che due operazioni concorrenti consumino lo stesso saldo.

## Test

```bash
python -m unittest discover -s tests -v
```

I test automatici senza database coprono model, view, CSV e alcune regole di transazione tramite simulatori. Il collaudo su PostgreSQL reale è separato, come indicato nella sezione Verifiche manuali.
