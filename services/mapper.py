from datetime import date, datetime
from models import *


class StrutturaFileError(Exception):
    pass


class MapperBanca:

    COLONNE_FILIALE = ["codice_filiale", "nome_filiale", "citta", "provincia", "regione", "data_apertura", "direttore_id"]
    COLONNE_DIPENDENTI = ["id_dipendente", "ruolo", "nome", "cognome", "codice_fiscale", "recapito", "data_assunzione", "specializzazione", "liv_autorizzazione"]
    COLONNE_ATM = ["codice_atm", "codice_filiale", "stato", "data_installazione"]
    COLONNE_CLIENTI = ["numero_cliente", "nome", "cognome", "codice_fiscale", "recapito", "email", "data_nascita", "citta", "data_registrazione", "segmento"]
    COLONNE_CONTI = ["id_conto", "iban", "numero_cliente", "tipo_conto", "data_apertura", "stato", "saldo"]
    COLONNE_MOVIMENTI = ["id_operazione", "id_conto", "tipo", "data_operazione", "importo", "canale", "causale", "tipo_versamento"]
    COLONNE_FINANZIAMENTI = ["id_operazione", "id_conto", "numero_cliente", "tipo", "data_operazione", "importo", "durata_mesi", "tasso", "stato", "finalita", "eseguito"]
    COLONNE_INVESTIMENTI = ["id_operazione", "id_conto", "numero_cliente", "data_operazione", "importo", "prodotto", "profilo_rischio", "rendimento_atteso", "stato", "eseguito"]

    def ricostruisci(self, dati):
        dipendenti = self._ricostruisci_dipendenti(dati["dipendenti"])
        filiale = self._ricostruisci_filiale(dati["filiale"], dipendenti)

        for dipendente in dipendenti.values():
            if dipendente.id_dipendente != filiale.direttore.id_dipendente:
                filiale.aggiungi_dipendente(dipendente)

        for riga in dati["atm"]:
            if riga["codice_filiale"] != filiale.codice_filiale:
                raise StrutturaFileError(f"ATM {riga['codice_atm']} associato a una filiale diversa")
            filiale.aggiungi_atm(ATM(riga["codice_atm"], riga["codice_filiale"], StatoATM(riga["stato"]), riga["data_installazione"]))

        clienti_per_id = {}
        for riga in dati["clienti"]:
            cliente = Cliente(riga["nome"], riga["cognome"], riga["codice_fiscale"], riga["recapito"], riga["numero_cliente"], riga["email"], riga["data_nascita"], riga["citta"], riga["data_registrazione"], SegmentoCliente(riga["segmento"]))
            filiale.aggiungi_cliente(cliente)
            clienti_per_id[cliente.numero_cliente] = cliente

        conti_per_id = {}
        for riga in dati["conti"]:
            cliente = clienti_per_id.get(riga["numero_cliente"])
            if cliente is None:
                raise StrutturaFileError(f"Cliente {riga['numero_cliente']} non trovato per il conto {riga['id_conto']}")
            conto = ContoCorrente(riga["id_conto"], riga["iban"], cliente, TipoConto(riga["tipo_conto"]), riga["data_apertura"], StatoConto(riga["stato"]))
            conto._imposta_saldo(riga["saldo"])
            cliente.conti.append(conto)
            if conto.id_conto in conti_per_id:
                raise StrutturaFileError(f"ID conto duplicato: {conto.id_conto}")
            conti_per_id[conto.id_conto] = conto

        for riga in dati["movimenti"]:
            conto = conti_per_id.get(riga["id_conto"])
            if conto is None:
                raise StrutturaFileError(f"Conto {riga['id_conto']} non trovato per il movimento {riga['id_operazione']}")
            movimento = self._crea_movimento(riga, conto)
            conto.movimenti.append(movimento)

        for riga in dati["finanziamenti"]:
            conto = conti_per_id.get(riga["id_conto"])
            if conto is None:
                raise StrutturaFileError(f"Conto {riga['id_conto']} non trovato per il finanziamento {riga['id_operazione']}")
            if conto.intestatario.numero_cliente != riga["numero_cliente"]:
                raise StrutturaFileError(f"Cliente non coerente per il finanziamento {riga['id_operazione']}")
            finanziamento = self._crea_finanziamento(riga, conto)
            filiale.aggiungi_finanziamento(finanziamento)
            if finanziamento.eseguito:
                conto.movimenti.append(finanziamento)

        for riga in dati["investimenti"]:
            conto = conti_per_id.get(riga["id_conto"])
            if conto is None:
                raise StrutturaFileError(f"Conto {riga['id_conto']} non trovato per l'investimento {riga['id_operazione']}")
            if conto.intestatario.numero_cliente != riga["numero_cliente"]:
                raise StrutturaFileError(f"Cliente non coerente per l'investimento {riga['id_operazione']}")
            investimento = Investimento(riga["id_operazione"], riga["data_operazione"], riga["importo"], conto, riga["prodotto"], ProfiloRischio(riga["profilo_rischio"]), riga["rendimento_atteso"])
            investimento.stato = StatoInvestimento(riga["stato"])
            investimento.eseguito = riga["eseguito"]
            filiale.aggiungi_investimento(investimento)
            if investimento.eseguito:
                conto.movimenti.append(investimento)

        return filiale

    def prepara_filiale(self, filiale):
        return [{
            "codice_filiale": filiale.codice_filiale,
            "nome_filiale": filiale.nome,
            "citta": filiale.citta,
            "provincia": filiale.provincia,
            "regione": filiale.regione,
            "data_apertura": filiale.data_apertura,
            "direttore_id": filiale.direttore.id_dipendente
        }]

    def prepara_dipendenti(self, dipendenti):
        righe = []
        for dipendente in dipendenti:
            ruolo = self._ruolo_dipendente(dipendente)
            specializzazione = dipendente.specializzazione.value if isinstance(dipendente, Specialista) else ""
            liv_autorizzazione = dipendente.liv_autorizzazione if isinstance(dipendente, Direttore) else ""
            righe.append({
                "id_dipendente": dipendente.id_dipendente,
                "ruolo": ruolo,
                "nome": dipendente.nome,
                "cognome": dipendente.cognome,
                "codice_fiscale": dipendente.codice_fiscale,
                "recapito": dipendente.recapito,
                "data_assunzione": dipendente.data_assunzione,
                "specializzazione": specializzazione,
                "liv_autorizzazione": liv_autorizzazione
            })
        return righe

    def prepara_atm(self, atms):
        return [{
            "codice_atm": atm.codice_atm,
            "codice_filiale": atm.filiale,
            "stato": atm.stato.value,
            "data_installazione": atm.data_installazione
        } for atm in atms]

    def prepara_clienti(self, clienti):
        righe = []
        for cliente in clienti:
            righe.append({
                "numero_cliente": cliente.numero_cliente,
                "nome": cliente.nome,
                "cognome": cliente.cognome,
                "codice_fiscale": cliente.codice_fiscale,
                "recapito": cliente.recapito,
                "email": cliente.email,
                "data_nascita": cliente.data_nascita,
                "citta": cliente.citta,
                "data_registrazione": cliente.data_registrazione,
                "segmento": cliente.segmento.value
            })
        return righe

    def prepara_conti(self, clienti):
        righe = []
        for cliente in clienti:
            for conto in cliente.conti:
                righe.append({
                    "id_conto": conto.id_conto,
                    "iban": conto.iban,
                    "numero_cliente": cliente.numero_cliente,
                    "tipo_conto": conto.tipo_conto.value,
                    "data_apertura": conto.data_apertura,
                    "stato": conto.stato.value,
                    "saldo": float(conto.saldo)
                })
        return righe

    def prepara_movimenti(self, clienti):
        righe = []
        for cliente in clienti:
            for conto in cliente.conti:
                for movimento in conto.movimenti:
                    if not isinstance(movimento, (Versamento, Prelievo)):
                        continue
                    righe.append({
                        "id_operazione": movimento.id_operazione,
                        "id_conto": conto.id_conto,
                        "tipo": type(movimento).__name__,
                        "data_operazione": movimento.data_operazione,
                        "importo": float(movimento.importo),
                        "canale": movimento.canale.value,
                        "causale": movimento.causale,
                        "tipo_versamento": movimento.tipo_versamento.value if isinstance(movimento, Versamento) else ""
                    })
        return righe

    def prepara_finanziamenti(self, finanziamenti):
        righe = []
        for finanziamento in finanziamenti:
            righe.append({
                "id_operazione": finanziamento.id_operazione,
                "id_conto": finanziamento.conto.id_conto,
                "numero_cliente": finanziamento.conto.intestatario.numero_cliente,
                "tipo": type(finanziamento).__name__,
                "data_operazione": finanziamento.data_operazione,
                "importo": float(finanziamento.importo),
                "durata_mesi": finanziamento.durata_mesi,
                "tasso": float(finanziamento.tasso),
                "stato": finanziamento.stato.value,
                "finalita": finanziamento.finalita,
                "eseguito": finanziamento.eseguito
            })
        return righe

    def prepara_investimenti(self, investimenti):
        righe = []
        for investimento in investimenti:
            righe.append({
                "id_operazione": investimento.id_operazione,
                "id_conto": investimento.conto.id_conto,
                "numero_cliente": investimento.conto.intestatario.numero_cliente,
                "data_operazione": investimento.data_operazione,
                "importo": float(investimento.importo),
                "prodotto": investimento.prodotto,
                "profilo_rischio": investimento.profilo_rischio.value,
                "rendimento_atteso": float(investimento.rendimento_atteso),
                "stato": investimento.stato.value,
                "eseguito": investimento.eseguito
            })
        return righe

    def _ruolo_dipendente(self, dipendente):
        if isinstance(dipendente, Direttore):
            return "Direttore"
        if isinstance(dipendente, Specialista):
            return "Specialista"
        if isinstance(dipendente, Gestore):
            return "Gestore"
        if isinstance(dipendente, AddettoAllaSicurezza):
            return "AddettoAllaSicurezza"
        raise TypeError("Tipo dipendente non riconosciuto")

    def _ricostruisci_dipendenti(self, righe):
        dipendenti = {}
        for riga in righe:
            match riga["ruolo"]:
                case "Direttore":
                    dipendente = Direttore(riga["nome"], riga["cognome"], riga["codice_fiscale"], riga["recapito"], riga["id_dipendente"], riga["data_assunzione"], Specializzazione(riga["specializzazione"]), riga["liv_autorizzazione"])
                case "Specialista":
                    dipendente = Specialista(riga["nome"], riga["cognome"], riga["codice_fiscale"], riga["recapito"], riga["id_dipendente"], riga["data_assunzione"], Specializzazione(riga["specializzazione"]))
                case "Gestore":
                    dipendente = Gestore(riga["nome"], riga["cognome"], riga["codice_fiscale"], riga["recapito"], riga["id_dipendente"], riga["data_assunzione"])
                case "AddettoAllaSicurezza":
                    dipendente = AddettoAllaSicurezza(riga["nome"], riga["cognome"], riga["codice_fiscale"], riga["recapito"], riga["id_dipendente"], riga["data_assunzione"])
                case _:
                    raise StrutturaFileError(f"Ruolo dipendente non riconosciuto: {riga['ruolo']}")
            if dipendente.id_dipendente in dipendenti:
                raise StrutturaFileError(f"ID dipendente duplicato: {dipendente.id_dipendente}")
            dipendenti[dipendente.id_dipendente] = dipendente
        return dipendenti

    def _ricostruisci_filiale(self, righe, dipendenti):
        if len(righe) == 0:
            raise StrutturaFileError("Nessuna filiale presente")
        if len(righe) > 1:
            raise StrutturaFileError("Sono presenti piu filiali")
        riga = righe[0]
        direttore = dipendenti.get(riga["direttore_id"])
        if not isinstance(direttore, Direttore):
            raise StrutturaFileError("Il direttore indicato nella filiale non esiste o non e' un Direttore")
        return Filiale(riga["codice_filiale"], riga["nome_filiale"], riga["citta"], riga["provincia"], riga["regione"], riga["data_apertura"], direttore)

    def _crea_movimento(self, riga, conto):
        match riga["tipo"]:
            case "Versamento":
                if riga["tipo_versamento"] == "":
                    raise StrutturaFileError("Tipo versamento mancante")
                return Versamento(riga["id_operazione"], riga["data_operazione"], riga["importo"], conto, TipoVersamento(riga["tipo_versamento"]), CanaleOperazione(riga["canale"]), riga["causale"])
            case "Prelievo":
                return Prelievo(riga["id_operazione"], riga["data_operazione"], riga["importo"], conto, CanaleOperazione(riga["canale"]), riga["causale"])
            case _:
                raise StrutturaFileError(f"Tipo movimento non riconosciuto: {riga['tipo']}")

    def _crea_finanziamento(self, riga, conto):
        match riga["tipo"]:
            case "Prestito":
                finanziamento = Prestito(riga["id_operazione"], riga["data_operazione"], riga["importo"], conto, riga["durata_mesi"], riga["tasso"], riga["finalita"])
            case "Mutuo":
                finanziamento = Mutuo(riga["id_operazione"], riga["data_operazione"], riga["importo"], conto, riga["durata_mesi"], riga["tasso"], riga["finalita"])
            case _:
                raise StrutturaFileError(f"Tipo finanziamento non riconosciuto: {riga['tipo']}")
        finanziamento.stato = StatoRichiesta(riga["stato"])
        finanziamento.eseguito = riga["eseguito"]
        return finanziamento

    def data_in_testo(self, valore):
        if not isinstance(valore, date):
            raise TypeError("Il valore deve essere un oggetto date")
        return valore.isoformat()

    def testo_in_data(self, valore, campo):
        if isinstance(valore, datetime):
            return valore.date()
        if isinstance(valore, date):
            return valore
        if not isinstance(valore, str) or valore.strip() == "":
            raise StrutturaFileError(f"Il campo {campo} non puo essere vuoto")
        valore = valore.strip()
        for formato in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(valore, formato).date()
            except ValueError:
                continue
        raise StrutturaFileError(f"Data non valida nel campo {campo}: {valore}")

    def converti_intero(self, valore, campo, valore_default=None):
        if valore is None or str(valore).strip() == "":
            if valore_default is not None:
                return valore_default
            raise StrutturaFileError(f"Il campo {campo} non puo essere vuoto")
        try:
            numero = float(str(valore).strip().replace(",", "."))
        except ValueError as errore:
            raise StrutturaFileError(f"Il campo {campo} deve contenere un numero intero: {valore}") from errore
        if not numero.is_integer():
            raise StrutturaFileError(f"Il campo {campo} deve contenere un numero intero: {valore}")
        return int(numero)

    def converti_float(self, valore, campo, valore_default=None):
        if valore is None or str(valore).strip() == "":
            if valore_default is not None:
                return valore_default
            raise StrutturaFileError(f"Il campo {campo} non puo essere vuoto")
        if isinstance(valore, str):
            valore = valore.strip().replace(",", ".")
        try:
            return float(valore)
        except (TypeError, ValueError) as errore:
            raise StrutturaFileError(f"Il campo {campo} deve contenere un numero valido: {valore}") from errore

    def converti_booleano(self, valore, campo):
        testo = str(valore).strip().lower()
        if testo in ("1", "true", "si", "sì"):
            return True
        if testo in ("0", "false", "no"):
            return False
        raise StrutturaFileError(f"Il campo {campo} deve contenere 1/0 oppure true/false")

    def controlla_colonne(self, colonne_presenti, colonne_attese, nome_archivio):
        if colonne_presenti != colonne_attese:
            raise StrutturaFileError(f"Struttura non valida per {nome_archivio}. Attese: {colonne_attese} - Trovate: {colonne_presenti}")

