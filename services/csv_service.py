import csv
from datetime import date
from pathlib import Path
from services.mapper import MapperBanca, StrutturaFileError


class ParserCSV(MapperBanca):

    def __init__(self, cartella="data/csv"):
        self.cartella = Path(cartella)



    def _scrivi_csv(self, percorso, colonne, righe):
        with open(percorso, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=colonne, delimiter=";")
            writer.writeheader()
            for riga in righe:
                riga_da_scrivere = {}
                for chiave, valore in riga.items():
                    if isinstance(valore, date):
                        riga_da_scrivere[chiave] = self.data_in_testo(valore)
                    elif isinstance(valore, bool):
                        riga_da_scrivere[chiave] = 1 if valore else 0
                    elif isinstance(valore, float):
                        riga_da_scrivere[chiave] = f"{valore:.2f}".replace(".", ",")
                    else:
                        riga_da_scrivere[chiave] = valore
                writer.writerow(riga_da_scrivere)

    def _leggi_filiale(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_FILIALE, "filiale")
        for riga in righe:
            riga["data_apertura"] = self.testo_in_data(riga["data_apertura"], "data_apertura")
            riga["direttore_id"] = self.converti_intero(riga["direttore_id"], "direttore_id")
        return righe

    def _leggi_dipendenti(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_DIPENDENTI, "dipendenti")
        for riga in righe:
            riga["id_dipendente"] = self.converti_intero(riga["id_dipendente"], "id_dipendente")
            riga["data_assunzione"] = self.testo_in_data(riga["data_assunzione"], "data_assunzione")
            riga["liv_autorizzazione"] = self.converti_intero(riga["liv_autorizzazione"], "liv_autorizzazione", 0)
        return righe

    def _leggi_atm(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_ATM, "atm")
        for riga in righe:
            riga["data_installazione"] = self.testo_in_data(riga["data_installazione"], "data_installazione")
        return righe

    def _leggi_clienti(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_CLIENTI, "clienti")
        for riga in righe:
            riga["numero_cliente"] = self.converti_intero(riga["numero_cliente"], "numero_cliente")
            riga["data_nascita"] = self.testo_in_data(riga["data_nascita"], "data_nascita")
            riga["data_registrazione"] = self.testo_in_data(riga["data_registrazione"], "data_registrazione")
        return righe

    def _leggi_conti(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_CONTI, "conti")
        for riga in righe:
            riga["id_conto"] = self.converti_intero(riga["id_conto"], "id_conto")
            riga["numero_cliente"] = self.converti_intero(riga["numero_cliente"], "numero_cliente")
            riga["data_apertura"] = self.testo_in_data(riga["data_apertura"], "data_apertura")
            riga["saldo"] = self.converti_float(riga["saldo"], "saldo", 0.0)
        return righe

    def _leggi_movimenti(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_MOVIMENTI, "movimenti")
        for riga in righe:
            riga["id_operazione"] = self.converti_intero(riga["id_operazione"], "id_operazione")
            riga["id_conto"] = self.converti_intero(riga["id_conto"], "id_conto")
            riga["data_operazione"] = self.testo_in_data(riga["data_operazione"], "data_operazione")
            riga["importo"] = self.converti_float(riga["importo"], "importo")
            riga["tipo_versamento"] = riga["tipo_versamento"] or ""
        return righe

    def _leggi_finanziamenti(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_FINANZIAMENTI, "finanziamenti")
        for riga in righe:
            riga["id_operazione"] = self.converti_intero(riga["id_operazione"], "id_operazione")
            riga["id_conto"] = self.converti_intero(riga["id_conto"], "id_conto")
            riga["numero_cliente"] = self.converti_intero(riga["numero_cliente"], "numero_cliente")
            riga["data_operazione"] = self.testo_in_data(riga["data_operazione"], "data_operazione")
            riga["importo"] = self.converti_float(riga["importo"], "importo")
            riga["durata_mesi"] = self.converti_intero(riga["durata_mesi"], "durata_mesi")
            riga["tasso"] = self.converti_float(riga["tasso"], "tasso")
            riga["eseguito"] = self.converti_booleano(riga["eseguito"], "eseguito")
        return righe

    def _leggi_investimenti(self, percorso):
        righe = self._leggi_csv_base(percorso, self.COLONNE_INVESTIMENTI, "investimenti")
        for riga in righe:
            riga["id_operazione"] = self.converti_intero(riga["id_operazione"], "id_operazione")
            riga["id_conto"] = self.converti_intero(riga["id_conto"], "id_conto")
            riga["numero_cliente"] = self.converti_intero(riga["numero_cliente"], "numero_cliente")
            riga["data_operazione"] = self.testo_in_data(riga["data_operazione"], "data_operazione")
            riga["importo"] = self.converti_float(riga["importo"], "importo")
            riga["rendimento_atteso"] = self.converti_float(riga["rendimento_atteso"], "rendimento_atteso")
            riga["eseguito"] = self.converti_booleano(riga["eseguito"], "eseguito")
        return righe

    def _leggi_csv_base(self, percorso, colonne_attese, nome_archivio):
        if not percorso.exists():
            raise FileNotFoundError(f"File non trovato: {percorso}")
        with open(percorso, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file, delimiter=";")
            colonne_presenti = reader.fieldnames
            self.controlla_colonne(colonne_presenti, colonne_attese, nome_archivio)
            righe = []
            for riga in reader:
                if all(valore is None or str(valore).strip() == "" for valore in riga.values()):
                    continue
                righe.append(riga)
            return righe


    # Ogni archivio viene gestito indipendentemente, non e' una fonte dati per l'applicazione.
    ENTITA = ("filiale", "dipendenti", "atm", "clienti", "conti", "movimenti", "finanziamenti", "investimenti")

    def _definizione(self, entita):
        definizioni = {
            "filiale": (self.COLONNE_FILIALE, self.prepara_filiale, self._leggi_filiale),
            "dipendenti": (self.COLONNE_DIPENDENTI, self.prepara_dipendenti, self._leggi_dipendenti),
            "atm": (self.COLONNE_ATM, self.prepara_atm, self._leggi_atm),
            "clienti": (self.COLONNE_CLIENTI, self.prepara_clienti, self._leggi_clienti),
            "conti": (self.COLONNE_CONTI, self.prepara_conti, self._leggi_conti),
            "movimenti": (self.COLONNE_MOVIMENTI, self.prepara_movimenti, self._leggi_movimenti),
            "finanziamenti": (self.COLONNE_FINANZIAMENTI, self.prepara_finanziamenti, self._leggi_finanziamenti),
            "investimenti": (self.COLONNE_INVESTIMENTI, self.prepara_investimenti, self._leggi_investimenti)
        }
        if entita not in definizioni: raise ValueError("Entita' CSV non valida")
        return definizioni[entita]

    def _oggetti(self, filiale, entita):
        if entita == "filiale": return filiale
        if entita == "dipendenti": return filiale.dipendenti
        if entita == "atm": return filiale.atm
        if entita == "clienti": return filiale.clienti
        if entita in ("conti", "movimenti"): return filiale.clienti
        if entita == "finanziamenti": return filiale.finanziamenti
        return filiale.investimenti

    def esporta_entita(self, filiale, entita, percorso=None):
        colonne, preparatore, _ = self._definizione(entita)
        percorso = Path(percorso) if percorso else self.cartella / filiale.codice_filiale / f"{entita}.csv"
        percorso.parent.mkdir(parents=True, exist_ok=True)
        righe = preparatore(self._oggetti(filiale, entita))
        self._scrivi_csv(percorso, colonne, righe)
        return percorso, len(righe)

    def importa_entita(self, entita, percorso):
        _, _, lettore = self._definizione(entita)
        return lettore(Path(percorso))
