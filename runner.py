from datetime import date

from models import Filiale, Direttore, ATM, Specializzazione, StatoATM

# =========================
# DATI MODIFICABILI RUNNER
# =========================

CODICE_FILIALE = "FILIALE_DEMO"
NOME_FILIALE = "Filiale Demo"
CITTA = "Roma"
PROVINCIA = "RM"
REGIONE = "Lazio"
DATA_APERTURA = date(2020, 1, 1)

NOME_DIRETTORE = "Mario"
COGNOME_DIRETTORE = "Rossi"
CODICE_FISCALE_DIRETTORE = "RSSMRA80A01H501U"
RECAPITO_DIRETTORE = "0612345678"
DATA_ASSUNZIONE = date(2020, 1, 1)
SPECIALIZZAZIONE = Specializzazione.INVESTIMENTI
LIV_AUTORIZZAZIONE = 3

CODICE_ATM = "ATM01"
DATA_INSTALLAZIONE = date(2020, 1, 1)


def esegui_runner(database):
    if database.esiste_filiale(CODICE_FILIALE):
        return database.carica_filiale(CODICE_FILIALE)

    direttore = Direttore(NOME_DIRETTORE, COGNOME_DIRETTORE, CODICE_FISCALE_DIRETTORE, RECAPITO_DIRETTORE, database.prossimo_id_dipendente(), DATA_ASSUNZIONE, SPECIALIZZAZIONE, LIV_AUTORIZZAZIONE)
    atm = ATM(CODICE_ATM, CODICE_FILIALE, StatoATM.ATTIVO, DATA_INSTALLAZIONE)
    filiale = Filiale(CODICE_FILIALE, NOME_FILIALE, CITTA, PROVINCIA, REGIONE, DATA_APERTURA, direttore, atm)
    database.inserisci_filiale(filiale)
    return database.carica_filiale(CODICE_FILIALE)
