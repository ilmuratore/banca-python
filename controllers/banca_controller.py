from datetime import date

from models import *
from repository.postgresql import DatabasePostgreSQL
from services.csv_service import ParserCSV


class BancaController:

    def __init__(self, database: DatabasePostgreSQL, csv: ParserCSV):
        self.database = database
        self.csv = csv
        self.codice_filiale = None

    def filiali(self):
        return self.database.elenco_filiali()

    def seleziona_filiale(self, codice):
        codice = codice.strip().upper()
        if not self.database.esiste_filiale(codice):
            raise OperazioneNonConsentitaError(f"Filiale {codice} non trovata")
        self.codice_filiale = codice
        return self.filiale()

    def filiale(self):
        if not self.codice_filiale:
            raise OperazioneNonConsentitaError("Selezionare o configurare prima una filiale")
        return self.database.carica_filiale(self.codice_filiale)

    def crea_filiale(self, dati, direttore_dati, atm_dati):
        codice = dati["codice_filiale"].strip().upper()
        direttore = Direttore(direttore_dati["nome"], direttore_dati["cognome"], direttore_dati["codice_fiscale"], direttore_dati["recapito"], self.database.prossimo_id_dipendente(), direttore_dati["data_assunzione"], Specializzazione.INVESTIMENTI, direttore_dati["liv_autorizzazione"])
        atm = ATM(atm_dati["codice_atm"], codice, StatoATM.ATTIVO, atm_dati["data_installazione"])
        filiale = Filiale(codice, dati["nome"], dati["citta"], dati["provincia"], dati["regione"], dati["data_apertura"], direttore, atm)
        self.database.inserisci_filiale(filiale)
        return self.seleziona_filiale(codice)

    def modifica_filiale(self, modifiche):
        filiale = self.filiale()
        for campo, valore in modifiche.items():
            if campo in ("nome", "citta", "provincia", "regione"): setattr(filiale, campo, valore)
        self.database.aggiorna_filiale(filiale)
        return self.filiale()

    def cliente(self, numero_cliente):
        for cliente in self.filiale().clienti:
            if cliente.numero_cliente == numero_cliente: return cliente
        raise ClienteNonValidoError(f"Cliente numero {numero_cliente} non trovato")

    def dipendente(self, id_dipendente):
        for dipendente in self.filiale().dipendenti:
            if dipendente.id_dipendente == id_dipendente: return dipendente
        raise OperazioneNonConsentitaError(f"Dipendente {id_dipendente} non trovato")

    def atm(self, codice_atm):
        for atm in self.filiale().atm:
            if atm.codice_atm == codice_atm.strip().upper(): return atm
        raise OperazioneNonConsentitaError(f"ATM {codice_atm} non trovato")

    def conto(self, id_conto):
        for cliente in self.filiale().clienti:
            for conto in cliente.conti:
                if conto.id_conto == id_conto: return conto
        raise OperazioneNonConsentitaError(f"Conto {id_conto} non trovato")

    def finanziamento(self, id_operazione):
        for finanziamento in self.filiale().finanziamenti:
            if finanziamento.id_operazione == id_operazione: return finanziamento
        raise OperazioneNonConsentitaError(f"Finanziamento {id_operazione} non trovato")

    def crea_cliente(self, dati):
        cliente = Cliente(dati["nome"], dati["cognome"], dati["codice_fiscale"], dati["recapito"], self.database.prossimo_numero_cliente(), dati["email"], dati["data_nascita"], dati["citta"], date.today(), dati["segmento"])
        filiale = self.filiale()
        filiale.aggiungi_cliente(cliente)
        self.database.inserisci_cliente(filiale.codice_filiale, cliente)
        return self.cliente(cliente.numero_cliente)

    def modifica_cliente(self, numero_cliente, modifiche):
        cliente = self.cliente(numero_cliente)
        for campo, valore in modifiche.items():
            if campo in ("nome", "cognome", "codice_fiscale", "recapito", "email", "citta", "segmento"): setattr(cliente, campo, valore)
        self.database.aggiorna_cliente(cliente)
        return self.cliente(numero_cliente)

    def crea_dipendente(self, ruolo, dati):
        parametri = [dati["nome"], dati["cognome"], dati["codice_fiscale"], dati["recapito"], self.database.prossimo_id_dipendente(), dati["data_assunzione"]]
        match ruolo:
            case "Gestore": dipendente = Gestore(*parametri)
            case "Specialista": dipendente = Specialista(*parametri, dati["specializzazione"])
            case "AddettoAllaSicurezza": dipendente = AddettoAllaSicurezza(*parametri)
            case _: raise ValueError("Ruolo non valido")
        filiale = self.filiale()
        filiale.aggiungi_dipendente(dipendente)
        self.database.inserisci_dipendente(filiale.codice_filiale, dipendente)
        return self.dipendente(dipendente.id_dipendente)

    def modifica_dipendente(self, id_dipendente, modifiche):
        dipendente = self.dipendente(id_dipendente)
        for campo, valore in modifiche.items():
            if campo in ("nome", "cognome", "codice_fiscale", "recapito"): setattr(dipendente, campo, valore)
            if campo == "specializzazione" and isinstance(dipendente, Specialista): dipendente.specializzazione = valore
            if campo == "liv_autorizzazione" and isinstance(dipendente, Direttore):
                if not isinstance(valore, int) or valore <= 0: raise ValueError("Livello autorizzazione non valido")
                dipendente.liv_autorizzazione = valore
        self.database.aggiorna_dipendente(dipendente)
        return self.dipendente(id_dipendente)

    def crea_atm(self, codice_atm, data_installazione):
        filiale = self.filiale()
        atm = ATM(codice_atm, filiale.codice_filiale, StatoATM.ATTIVO, data_installazione)
        filiale.aggiungi_atm(atm)
        self.database.inserisci_atm(atm)
        return self.atm(atm.codice_atm)

    def modifica_atm(self, codice_atm, stato):
        atm = self.atm(codice_atm)
        if not isinstance(stato, StatoATM): raise ValueError("Stato ATM non valido")
        atm.stato = stato
        self.database.aggiorna_atm(atm)
        return self.atm(codice_atm)

    def apri_conto(self, numero_cliente, iban, tipo_conto):
        filiale = self.filiale()
        cliente = next((c for c in filiale.clienti if c.numero_cliente == numero_cliente), None)
        if cliente is None: raise ClienteNonValidoError("Cliente non trovato")
        conto = filiale.direttore.apri_conto(self.database.prossimo_id_conto(), iban, cliente, tipo_conto, date.today())
        self.database.inserisci_conto(conto)
        return self.conto(conto.id_conto)

    def modifica_conto(self, id_conto, iban, tipo_conto, stato):
        conto = self.conto(id_conto)
        conto.iban = iban
        conto.tipo_conto = tipo_conto
        conto.stato = stato
        self.database.aggiorna_conto(conto)
        return self.conto(id_conto)

    def versamento(self, id_conto, importo, tipo, causale):
        filiale = self.filiale()
        conto = next((c for cl in filiale.clienti for c in cl.conti if c.id_conto == id_conto), None)
        if conto is None: raise OperazioneNonConsentitaError("Conto non trovato")
        movimento = filiale.direttore.versa(self.database.prossimo_id_operazione(), conto, importo, tipo, CanaleOperazione.FILIALE, causale)
        self.database.inserisci_movimento(movimento, filiale.codice_filiale)
        return movimento, self.conto(id_conto).saldo

    def prelievo_atm(self, codice_atm, id_conto, importo):
        filiale = self.filiale()
        atm = next((a for a in filiale.atm if a.codice_atm == codice_atm.strip().upper()), None)
        conto = next((c for cl in filiale.clienti for c in cl.conti if c.id_conto == id_conto), None)
        if atm is None or conto is None: raise OperazioneNonConsentitaError("ATM o conto non trovato")
        movimento = atm.preleva(self.database.prossimo_id_operazione(), conto, importo)
        self.database.inserisci_movimento(movimento, filiale.codice_filiale)
        return movimento, self.conto(id_conto).saldo

    def crea_finanziamento(self, tipo, id_conto, importo, durata_mesi, tasso, finalita):
        filiale = self.filiale()
        conto = next((c for cl in filiale.clienti for c in cl.conti if c.id_conto == id_conto), None)
        if conto is None: raise OperazioneNonConsentitaError("Conto non trovato")
        id_operazione = self.database.prossimo_id_operazione()
        match tipo:
            case "Prestito": finanziamento = filiale.direttore.richiedi_prestito(id_operazione, date.today(), importo, conto, durata_mesi, tasso, finalita)
            case "Mutuo": finanziamento = filiale.direttore.richiedi_mutuo(id_operazione, date.today(), importo, conto, durata_mesi, tasso, finalita)
            case _: raise ValueError("Tipo finanziamento non valido")
        filiale.aggiungi_finanziamento(finanziamento)
        self.database.inserisci_finanziamento(finanziamento)
        return self.finanziamento(id_operazione)

    def delibera_finanziamento(self, id_operazione, stato):
        filiale = self.filiale()
        finanziamento = next((f for f in filiale.finanziamenti if f.id_operazione == id_operazione), None)
        if finanziamento is None: raise OperazioneNonConsentitaError("Finanziamento non trovato")
        filiale.direttore.cambia_stato_finanziamento(finanziamento, stato)
        self.database.delibera_finanziamento(id_operazione, stato, filiale.codice_filiale)
        return self.finanziamento(id_operazione)

    def investimento(self, id_conto, importo, prodotto, profilo_rischio, rendimento_atteso):
        filiale = self.filiale()
        conto = next((c for cl in filiale.clienti for c in cl.conti if c.id_conto == id_conto), None)
        if conto is None: raise OperazioneNonConsentitaError("Conto non trovato")
        inv = filiale.direttore.investi(self.database.prossimo_id_operazione(), date.today(), importo, conto, prodotto, profilo_rischio, rendimento_atteso)
        self.database.inserisci_investimento(inv, filiale.codice_filiale)
        return next(i for i in self.filiale().investimenti if i.id_operazione == inv.id_operazione)

    def movimenti(self, id_conto):
        return sorted(self.conto(id_conto).movimenti, key=lambda x: (x.data_operazione, x.id_operazione))

    def movimenti_periodo(self, data_inizio, data_fine):
        if data_fine < data_inizio: raise ValueError("Data finale precedente alla data iniziale")
        filiale = self.filiale()
        return sorted((m for cl in filiale.clienti for c in cl.conti for m in c.movimenti if data_inizio <= m.data_operazione <= data_fine), key=lambda x: (x.data_operazione, x.id_operazione))

    def report(self):
        codice = self.filiale().codice_filiale
        return {
            "saldi": self.database.report_saldi(codice),
            "segmenti": self.database.report_clienti_segmento(codice),
            "canali": self.database.report_operazioni_canale(codice),
            "finanziamenti": self.database.report_finanziamenti_stato(codice)
        }

    def esporta_csv(self, entita, percorso=None):
        return self.csv.esporta_entita(self.filiale(), entita, percorso)

    def importa_csv(self, entita, percorso):
        filiale = self.filiale()
        righe = self.csv.importa_entita(entita, percorso)
        totale = self.database.importa_righe(entita, righe, filiale.codice_filiale)
        self.filiale()  # Verifica ricostruzione completa dopo il commit.
        return totale
