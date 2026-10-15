# Guida all'utilizzo

> **Lingua:** Italiano · [English](../USER_GUIDE.md) · [Torna al LEGGIMI](../../LEGGIMI.md)

Banca Python è un **simulatore bancario da terminale**. Non è un servizio bancario reale.

## Primo avvio

Dopo aver seguito le istruzioni di [installazione](../../LEGGIMI.md#installazione), configurare PostgreSQL e avviare:

```bash
python main.py
```

Su un database vuoto lo schema viene creato automaticamente. Se è presente una sola filiale viene selezionata; con più filiali è necessario sceglierne una dal menu.

## Menu principale

| Scelta | Menu | Funzione |
| --- | --- | --- |
| 1 | Filiali | Creare, selezionare, modificare una filiale |
| 2 | Clienti | Registrare, cercare e modificare clienti |
| 3 | Dipendenti e ATM | Gestire personale e sportelli |
| 4 | Conti correnti | Aprire e amministrare conti |
| 5 | Operazioni | Versamenti e prelievi |
| 6 | Finanziamenti e investimenti | Richieste, delibere e investimenti |
| 7 | Ricerche e report | Consultare record e report SQL |
| 8 | Import / Export CSV | Importare o esportare manualmente |
| 9 | Pandas | Analisi, raggruppamenti e grafici |
| 0 | Esci | Terminare il programma |

I sottomenu mostrano direttamente le azioni. Seguire le richieste di input: il programma valida i dati e mostra gli eventuali errori.

## Esempio di utilizzo

1. Da **Filiali**, creare una filiale inserendo i dati richiesti.
2. Da **Clienti**, registrare un cliente.
3. Da **Conti correnti**, aprire un conto per il cliente.
4. Da **Operazioni**, effettuare un versamento e consultare i movimenti.
5. Provare un prelievo superiore al saldo: il programma deve rifiutarlo senza modificare il database.
6. Consultare **Ricerche e report** e il menu **Pandas**.

Non esiste un pulsante o comando **Salva**: le modifiche confermate vengono registrate in PostgreSQL tramite transazioni.

## Caricare la demo

I 1.400 record inclusi fanno riferimento alla filiale `FIL001`. Creare/selezionare `FIL001`, aprire **8 → 2** e importare i sette file seguendo l'ordine indicato in [Dataset](DATASET.md). Usare un database separato dai propri dati personali.

## Analisi e grafici

Il menu **9** permette di mostrare tabelle clienti/conti/movimenti, filtrare segmenti e saldi, controllare la qualità dei dati, aggregare conti, collegare clienti e conti, produrre pivot ed esportare grafici.

I PNG sono salvati in:

```text
data/csv/<CODICE_FILIALE>/grafici/
```

Sono disponibili grafici a barre e a torta sui segmenti, linea sul volume mensile delle operazioni e istogramma dei saldi. I file generati sono esclusi da Git.

## Regole CSV

- L'esportazione manuale legge i dati correnti dal database.
- L'importazione richiede file, percorso e conferma `SI`.
- Intestazioni e formati devono rispettare il tracciato richiesto.
- Il campo `saldo` non aggiorna il conto in importazione.
- Gli errori causano il rollback; gli ID delle operazioni economiche già registrate non vengono riapplicati.

Vedere [Dataset](DATASET.md) per i formati precisi.

## Problemi comuni

**Connessione rifiutata:** controllare PostgreSQL e le variabili `BANCA_DB_*`. Con il Docker Compose opzionale la porta è `5433`, non `5432`.

**Schema parziale:** lavorare su un database di prova vuoto oppure esaminare lo schema esistente. Il programma non elimina le tabelle per ripararlo.

**Dati non visibili:** selezionare la filiale corretta e verificare di avere eseguito le importazioni.

**Il terminale si ripulisce:** impostare `BANCA_NO_CLEAR=1` prima di avviare.

**Grafici non prodotti:** controllare che esistano dati sufficienti per la filiale selezionata.

Per approfondire consultare [Sviluppo](SVILUPPO.md) e [Architettura](ARCHITETTURA.md).
