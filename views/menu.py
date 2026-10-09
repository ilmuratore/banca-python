import os
from datetime import date, datetime

from models import *
from repository.postgresql import DatabaseError
from services.mapper import StrutturaFileError
from services.csv_service import ParserCSV


TRACCIATI = {
    "filiale": "codice_filiale | nome_filiale | citta | provincia | regione | data_apertura | direttore_id",
    "clienti": "numero_cliente | nome | cognome | codice_fiscale | recapito | email | data_nascita | citta | data_registrazione | segmento",
    "dipendenti": "id_dipendente | ruolo | nome | cognome | codice_fiscale | recapito | data_assunzione | specializzazione | liv_autorizzazione",
    "atm": "codice_atm | codice_filiale | stato | data_installazione",
    "conti": "id_conto | iban | numero_cliente | tipo_conto | data_apertura | stato | saldo",
    "movimenti": "id_operazione | id_conto | tipo | data_operazione | importo | canale | causale | tipo_versamento",
    "finanziamenti": "id_operazione | id_conto | numero_cliente | tipo | data_operazione | importo | durata_mesi | tasso | stato | finalita | eseguito",
    "investimenti": "id_operazione | id_conto | numero_cliente | data_operazione | importo | prodotto | profilo_rischio | rendimento_atteso | stato | eseguito"
}


class MenuBanca:

    def __init__(self, controller):
        self.controller = controller

    def pausa(self):
        input("\nPremi INVIO per continuare...")

    def pulisci(self):
        if os.environ.get("BANCA_NO_CLEAR") == "1": return
        if os.name == "nt" and not (os.environ.get("MSYSTEM") or os.environ.get("WT_SESSION") or os.environ.get("TERM")):
            os.system("cls")
        else:
            print("\033[2J\033[H", end="", flush=True)

    def schermata(self, titolo):
        self.pulisci()
        print(f"\n=== {titolo.upper()} ===")

    def scelta_menu(self, titolo, voci):
        self.schermata(titolo)
        print(f"Filiale selezionata: {self.controller.codice_filiale or 'nessuna'}\n")
        for numero, voce in enumerate(voci, 1): print(f"{numero}. {voce}")
        print("0. Indietro")
        scelta = input("\nScelta: ").strip()
        if scelta != "0":
            titoli = {str(numero): voce for numero, voce in enumerate(voci, 1)}
            self.schermata(titoli.get(scelta, "Scelta non valida"))
        return scelta

    def errore(self, errore):
        if isinstance(errore, SaldoInsufficienteError): titolo = "SALDO INSUFFICIENTE"
        elif isinstance(errore, OperazioneNonConsentitaError): titolo = "OPERAZIONE NON CONSENTITA"
        elif isinstance(errore, ClienteNonValidoError): titolo = "CLIENTE NON VALIDO"
        elif isinstance(errore, StrutturaFileError): titolo = "ERRORE CSV"
        elif isinstance(errore, DatabaseError): titolo = "ERRORE POSTGRESQL"
        elif isinstance(errore, ValueError): titolo = "VALORE NON VALIDO"
        elif isinstance(errore, TypeError): titolo = "TIPO NON VALIDO"
        elif isinstance(errore, FileNotFoundError): titolo = "FILE NON TROVATO"
        else: titolo = type(errore).__name__.upper()
        print(f"\n{titolo}: {errore}")

    def leggi_data(self, messaggio, default=None):
        testo = input(messaggio).strip()
        if not testo and default is not None: return default
        return datetime.strptime(testo, "%d/%m/%Y").date()

    def leggi_intero(self, messaggio):
        return int(input(messaggio).strip())

    def leggi_importo(self, messaggio):
        return float(input(messaggio).strip().replace(",", "."))

    def leggi_testo(self, campo, attuale=None):
        if attuale is None: return input(f"{campo}: ").strip()
        testo = input(f"{campo} [{attuale}]: ").strip()
        return testo if testo else attuale

    def enum(self, tipo, default=None):
        valori = list(tipo)
        for numero, elemento in enumerate(valori, 1): print(f"{numero}. {elemento.value}")
        testo = input(f"Scelta{' [INVIO: mantieni]' if default else ''}: ").strip()
        if not testo and default is not None: return default
        numero = int(testo)
        if numero not in range(1, len(valori) + 1): raise ValueError("Scelta non valida")
        return valori[numero - 1]

    def persona(self, attuale=None):
        return {
            "nome": self.leggi_testo("Nome", attuale.nome if attuale else None),
            "cognome": self.leggi_testo("Cognome", attuale.cognome if attuale else None),
            "codice_fiscale": self.leggi_testo("Codice fiscale", attuale.codice_fiscale if attuale else None),
            "recapito": self.leggi_testo("Recapito", attuale.recapito if attuale else None)
        }

    def tracciato(self, entita):
        print(f"\n=== RECORD {entita.upper()} ===\n{TRACCIATI[entita]}\n")

    def elenco(self, oggetti, titolo):
        print(f"\n=== {titolo} ===")
        if not oggetti:
            print("Nessun record presente")
            return
        for oggetto in oggetti: print(f"\n{oggetto}")

    def scegli_filiale(self):
        filiali = self.controller.filiali()
        if not filiali:
            print("Nessuna filiale presente: crearne una dal menu Filiale")
            return
        print("\nCODICE | NOME | CITTA | PROVINCIA")
        for f in filiali: print(f"{f['codice_filiale']} | {f['nome']} | {f['citta']} | {f['provincia']}")
        codice = input("\nCodice filiale: ").strip()
        print(self.controller.seleziona_filiale(codice))

    def nuova_filiale(self):
        self.tracciato("filiale")
        dati = {
            "codice_filiale": self.leggi_testo("Codice filiale"),
            "nome": self.leggi_testo("Nome filiale"),
            "citta": self.leggi_testo("Citta"),
            "provincia": self.leggi_testo("Provincia"),
            "regione": self.leggi_testo("Regione"),
            "data_apertura": self.leggi_data("Data apertura [gg/mm/aaaa]: ")
        }
        self.tracciato("dipendenti")
        print("=== DIRETTORE INIZIALE ===")
        direttore = self.persona()
        direttore["data_assunzione"] = self.leggi_data("Data assunzione [gg/mm/aaaa]: ", date.today())
        direttore["liv_autorizzazione"] = self.leggi_intero("Livello autorizzazione: ")
        self.tracciato("atm")
        atm = {"codice_atm": self.leggi_testo("Codice ATM"), "data_installazione": self.leggi_data("Data installazione [gg/mm/aaaa]: ", date.today())}
        print(self.controller.crea_filiale(dati, direttore, atm))

    def sezione_filiale(self):
        while True:
            scelta = self.scelta_menu("FILIALE", ("Nuova filiale", "Seleziona filiale", "Riepilogo filiale", "Modifica filiale", "Elenco filiali"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1": self.nuova_filiale()
                    case "2": self.scegli_filiale()
                    case "3": print(self.controller.filiale())
                    case "4":
                        filiale = self.controller.filiale()
                        self.tracciato("filiale")
                        modifiche = {campo: self.leggi_testo(campo.title(), getattr(filiale, campo)) for campo in ("nome", "citta", "provincia", "regione")}
                        print(self.controller.modifica_filiale(modifiche))
                    case "5":
                        for filiale in self.controller.filiali(): print(f"{filiale['codice_filiale']} | {filiale['nome']} | {filiale['citta']}")
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def sezione_clienti(self):
        while True:
            scelta = self.scelta_menu("CLIENTI", ("Inserisci cliente", "Modifica cliente", "Elenco clienti", "Cerca cliente"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1":
                        self.tracciato("clienti")
                        dati = self.persona()
                        dati["email"] = self.leggi_testo("Email")
                        dati["data_nascita"] = self.leggi_data("Data nascita [gg/mm/aaaa]: ")
                        dati["citta"] = self.leggi_testo("Citta")
                        dati["segmento"] = self.enum(SegmentoCliente)
                        print(self.controller.crea_cliente(dati))
                    case "2":
                        cliente = self.controller.cliente(self.leggi_intero("Numero cliente: "))
                        self.tracciato("clienti")
                        print(cliente)
                        modifiche = self.persona(cliente)
                        modifiche["email"] = self.leggi_testo("Email", cliente.email)
                        modifiche["citta"] = self.leggi_testo("Citta", cliente.citta)
                        modifiche["segmento"] = self.enum(SegmentoCliente, cliente.segmento)
                        print(self.controller.modifica_cliente(cliente.numero_cliente, modifiche))
                    case "3": self.elenco(self.controller.filiale().clienti, "CLIENTI")
                    case "4": print(self.controller.cliente(self.leggi_intero("Numero cliente: ")))
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def sezione_personale(self):
        while True:
            scelta = self.scelta_menu("DIPENDENTI E ATM", ("Inserisci dipendente", "Modifica dipendente", "Aggiungi ATM", "Modifica stato ATM", "Elenco dipendenti", "Elenco ATM", "Cerca dipendente"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1":
                        self.tracciato("dipendenti")
                        ruoli = {"1": "Gestore", "2": "Specialista", "3": "AddettoAllaSicurezza"}
                        print("1. Gestore\n2. Specialista\n3. Addetto alla sicurezza")
                        ruolo = ruoli.get(input("Ruolo: ").strip())
                        if ruolo is None: raise ValueError("Ruolo non valido")
                        dati = self.persona()
                        dati["data_assunzione"] = self.leggi_data("Data assunzione [gg/mm/aaaa]: ", date.today())
                        if ruolo == "Specialista": dati["specializzazione"] = self.enum(Specializzazione)
                        print(self.controller.crea_dipendente(ruolo, dati))
                    case "2":
                        dipendente = self.controller.dipendente(self.leggi_intero("ID dipendente: "))
                        print(dipendente)
                        dati = self.persona(dipendente)
                        if isinstance(dipendente, Specialista): dati["specializzazione"] = self.enum(Specializzazione, dipendente.specializzazione)
                        if isinstance(dipendente, Direttore): dati["liv_autorizzazione"] = int(self.leggi_testo("Livello autorizzazione", dipendente.liv_autorizzazione))
                        print(self.controller.modifica_dipendente(dipendente.id_dipendente, dati))
                    case "3":
                        self.tracciato("atm")
                        codice = self.leggi_testo("Codice ATM")
                        data_installazione = self.leggi_data("Data installazione [gg/mm/aaaa]: ", date.today())
                        print(self.controller.crea_atm(codice, data_installazione))
                    case "4":
                        atm = self.controller.atm(self.leggi_testo("Codice ATM"))
                        print(atm)
                        print(self.controller.modifica_atm(atm.codice_atm, self.enum(StatoATM, atm.stato)))
                    case "5": self.elenco(self.controller.filiale().dipendenti, "DIPENDENTI")
                    case "6": self.elenco(self.controller.filiale().atm, "ATM")
                    case "7": print(self.controller.dipendente(self.leggi_intero("ID dipendente: ")))
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def sezione_conti(self):
        while True:
            scelta = self.scelta_menu("CONTI CORRENTI", ("Apri conto", "Modifica conto", "Elenco conti", "Cerca conto"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1":
                        self.tracciato("conti")
                        cliente = self.leggi_intero("Numero cliente: ")
                        iban = self.leggi_testo("IBAN")
                        tipo = self.enum(TipoConto)
                        print(self.controller.apri_conto(cliente, iban, tipo))
                    case "2":
                        conto = self.controller.conto(self.leggi_intero("ID conto: "))
                        print(conto)
                        iban = self.leggi_testo("IBAN", conto.iban)
                        tipo = self.enum(TipoConto, conto.tipo_conto)
                        stato = self.enum(StatoConto, conto.stato)
                        print(self.controller.modifica_conto(conto.id_conto, iban, tipo, stato))
                    case "3":
                        filiale = self.controller.filiale()
                        self.elenco([c for cl in filiale.clienti for c in cl.conti], "CONTI")
                    case "4": print(self.controller.conto(self.leggi_intero("ID conto: ")))
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def sezione_operazioni(self):
        while True:
            scelta = self.scelta_menu("OPERAZIONI", ("Versa contanti", "Versa assegno", "Prelievo ATM", "Movimenti di un conto"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1" | "2":
                        self.tracciato("movimenti")
                        id_conto = self.leggi_intero("ID conto: ")
                        importo = self.leggi_importo("Importo: ")
                        tipo = TipoVersamento.CONTANTI if scelta == "1" else TipoVersamento.ASSEGNO
                        causale = input("Causale [Versamento]: ").strip() or "Versamento"
                        movimento, saldo = self.controller.versamento(id_conto, importo, tipo, causale)
                        print(f"{movimento}\nSaldo aggiornato: {saldo:.2f} euro")
                    case "3":
                        self.tracciato("movimenti")
                        atm = self.leggi_testo("Codice ATM")
                        id_conto = self.leggi_intero("ID conto: ")
                        importo = self.leggi_importo("Importo prelievo: ")
                        movimento, saldo = self.controller.prelievo_atm(atm, id_conto, importo)
                        print(f"{movimento}\nSaldo aggiornato: {saldo:.2f} euro")
                    case "4": self.elenco(self.controller.movimenti(self.leggi_intero("ID conto: ")), "MOVIMENTI")
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def sezione_finanziamenti(self):
        while True:
            scelta = self.scelta_menu("FINANZIAMENTI E INVESTIMENTI", ("Richiesta prestito", "Richiesta mutuo", "Approva finanziamento", "Rifiuta finanziamento", "Nuovo investimento", "Elenco finanziamenti", "Elenco investimenti"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1" | "2":
                        self.tracciato("finanziamenti")
                        tipo = "Prestito" if scelta == "1" else "Mutuo"
                        conto = self.leggi_intero("ID conto: ")
                        importo = self.leggi_importo("Importo finanziamento: ")
                        durata = self.leggi_intero("Durata in mesi: ")
                        tasso = self.leggi_importo("Tasso percentuale: ")
                        finalita = self.leggi_testo("Finalita")
                        print(self.controller.crea_finanziamento(tipo, conto, importo, durata, tasso, finalita))
                    case "3" | "4":
                        filiale = self.controller.filiale()
                        self.elenco([f for f in filiale.finanziamenti if f.stato == StatoRichiesta.RICHIESTA], "FINANZIAMENTI IN ATTESA")
                        id_operazione = self.leggi_intero("ID finanziamento: ")
                        stato = StatoRichiesta.APPROVATA if scelta == "3" else StatoRichiesta.RIFIUTATA
                        print(self.controller.delibera_finanziamento(id_operazione, stato))
                    case "5":
                        self.tracciato("investimenti")
                        conto = self.leggi_intero("ID conto: ")
                        importo = self.leggi_importo("Importo investimento: ")
                        prodotto = self.leggi_testo("Prodotto")
                        profilo = self.enum(ProfiloRischio)
                        rendimento = self.leggi_importo("Rendimento atteso (%): ")
                        print(self.controller.investimento(conto, importo, prodotto, profilo, rendimento))
                    case "6": self.elenco(self.controller.filiale().finanziamenti, "FINANZIAMENTI")
                    case "7": self.elenco(self.controller.filiale().investimenti, "INVESTIMENTI")
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def sezione_report(self):
        while True:
            scelta = self.scelta_menu("RICERCHE E REPORT", ("Cerca cliente", "Cerca dipendente", "Cerca conto", "Cerca finanziamento", "Movimenti per periodo", "Report SQL filiale"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1": print(self.controller.cliente(self.leggi_intero("Numero cliente: ")))
                    case "2": print(self.controller.dipendente(self.leggi_intero("ID dipendente: ")))
                    case "3": print(self.controller.conto(self.leggi_intero("ID conto: ")))
                    case "4": print(self.controller.finanziamento(self.leggi_intero("ID operazione: ")))
                    case "5":
                        inizio = self.leggi_data("Data iniziale [gg/mm/aaaa]: ")
                        fine = self.leggi_data("Data finale [gg/mm/aaaa]: ")
                        self.elenco(self.controller.movimenti_periodo(inizio, fine), "MOVIMENTI NEL PERIODO")
                    case "6":
                        report = self.controller.report()
                        saldi = report["saldi"]
                        print(f"Conti: {saldi['numero_conti']} | Saldo totale: {float(saldi['saldo_totale']):.2f} euro | Saldo medio: {float(saldi['saldo_medio']):.2f} euro")
                        for categoria, righe in report.items():
                            if categoria == "saldi": continue
                            print(f"\n{categoria.upper()}")
                            for riga in righe: print(" | ".join(f"{chiave}: {valore}" for chiave, valore in riga.items()))
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def sezione_csv(self):
        while True:
            scelta = self.scelta_menu("IMPORT / EXPORT CSV", ("Esporta una entita'", "Importa una entita'", "Mostra tracciati", "Esporta tutte le entita'"))
            if scelta == "0": return
            try:
                match scelta:
                    case "1" | "2":
                        entita = self.scegli_entita()
                        if scelta == "1":
                            percorso, righe = self.controller.esporta_csv(entita)
                            print(f"Esportate {righe} righe in {percorso}")
                        else:
                            filiale = self.controller.filiale()
                            default = self.controller.csv.cartella / filiale.codice_filiale / f"{entita}.csv"
                            percorso = input(f"Percorso CSV [{default}]: ").strip() or str(default)
                            numero = self.controller.importa_csv(entita, percorso)
                            print(f"Importazione completata: {numero} record inseriti/aggiornati (nessuna cancellazione)")
                    case "3":
                        for entita in ParserCSV.ENTITA: self.tracciato(entita)
                    case "4":
                        for entita in ParserCSV.ENTITA:
                            percorso, righe = self.controller.esporta_csv(entita)
                            print(f"{entita}: {righe} record -> {percorso}")
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore: self.errore(errore)
            self.pausa()

    def scegli_entita(self):
        entita = list(ParserCSV.ENTITA)
        for posizione, nome in enumerate(entita, 1): print(f"{posizione}. {nome}")
        scelta = self.leggi_intero("Entita': ")
        if scelta not in range(1, len(entita) + 1): raise ValueError("Entita' non valida")
        return entita[scelta - 1]

    def avvia(self):
        while True:
            self.pulisci()
            codice = self.controller.codice_filiale or "nessuna"
            print(f"\n====================\n        BANCA\n====================\nPersistenza: PostgreSQL\nFiliale selezionata: {codice}")
            print("1. Filiale\n2. Clienti\n3. Dipendenti e ATM\n4. Conti correnti\n5. Operazioni\n6. Finanziamenti e investimenti\n7. Ricerche e report\n8. Import / Export CSV\n9. Inizializza o seleziona filiale demo\n0. Esci")
            scelta = input("\nScelta: ").strip()
            if scelta == "0":
                print("Programma terminato")
                return
            try:
                match scelta:
                    case "1": self.sezione_filiale()
                    case "2": self.sezione_clienti()
                    case "3": self.sezione_personale()
                    case "4": self.sezione_conti()
                    case "5": self.sezione_operazioni()
                    case "6": self.sezione_finanziamenti()
                    case "7": self.sezione_report()
                    case "8": self.sezione_csv()
                    case "9":
                        self.schermata("Filiale dimostrativa")
                        from runner import esegui_runner
                        filiale = esegui_runner(self.controller.database)
                        self.controller.seleziona_filiale(filiale.codice_filiale)
                        print(filiale)
                        self.pausa()
                    case _: raise ValueError("Scelta non valida")
            except Exception as errore:
                self.errore(errore)
                self.pausa()
