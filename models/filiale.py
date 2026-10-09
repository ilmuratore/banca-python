from __future__ import annotations
from datetime import date
from .atm import ATM
from .addetto_sicurezza import AddettoAllaSicurezza
from .cliente import Cliente
from .eccezioni import ClienteNonValidoError
from .direttore import Direttore
from .finanziamento import Finanziamento
from .gestore import Gestore
from .investimento import Investimento
from .eccezioni import OperazioneNonConsentitaError
from .specialista import Specialista


class Filiale:

    def __init__(self, codice_filiale:str, nome:str, citta:str, provincia:str, regione:str, data_apertura:date, direttore:Direttore, atm:ATM=None):
        if not isinstance(codice_filiale, str) or codice_filiale.strip() == "":
            raise ValueError("Il codice filiale non puo essere vuoto")
        if not isinstance(nome, str) or nome.strip() == "":
            raise ValueError("Il nome della filiale non puo essere vuoto")
        if not isinstance(citta, str) or citta.strip() == "":
            raise ValueError("La citta della filiale non puo essere vuota")
        if not isinstance(provincia, str) or provincia.strip() == "":
            raise ValueError("La provincia della filiale non puo essere vuota")
        if not isinstance(regione, str) or regione.strip() == "":
            raise ValueError("La regione della filiale non puo essere vuota")
        if not isinstance(data_apertura, date):
            raise TypeError("La data di apertura deve essere un oggetto date")
        if data_apertura > date.today():
            raise ValueError("La data di apertura non puo essere futura")
        if not isinstance(direttore, Direttore):
            raise TypeError("Il direttore deve essere un oggetto Direttore")
        self.codice_filiale = codice_filiale.strip().upper()
        self.nome = nome.strip()
        self.citta = citta.strip().title()
        self.provincia = provincia.strip().upper()
        self.regione = regione.strip().title()
        self.data_apertura = data_apertura
        self.direttore = direttore
        self.clienti = []
        self.dipendenti = [direttore]
        self.atm = []
        self.finanziamenti = []
        self.investimenti = []
        if atm is not None:
            self.aggiungi_atm(atm)

    def aggiungi_cliente(self, cliente):
        if not isinstance(cliente, Cliente):
            raise TypeError("L'oggetto deve essere un Cliente")
        if any(c.numero_cliente == cliente.numero_cliente for c in self.clienti):
            raise ClienteNonValidoError("Numero cliente gia presente")
        if any(c.codice_fiscale == cliente.codice_fiscale for c in self.clienti):
            raise ClienteNonValidoError("Codice fiscale cliente gia presente")
        self.clienti.append(cliente)

    def aggiungi_dipendente(self, dipendente):
        if not isinstance(dipendente, (Gestore, Specialista, Direttore, AddettoAllaSicurezza)):
            raise TypeError("L'oggetto deve essere un dipendente valido")
        if any(d.id_dipendente == dipendente.id_dipendente for d in self.dipendenti):
            raise OperazioneNonConsentitaError("ID dipendente gia presente")
        if any(d.codice_fiscale == dipendente.codice_fiscale for d in self.dipendenti):
            raise OperazioneNonConsentitaError("Codice fiscale dipendente gia presente")
        self.dipendenti.append(dipendente)

    def aggiungi_atm(self, atm):
        if not isinstance(atm, ATM):
            raise TypeError("L'oggetto deve essere un ATM")
        if atm.filiale != self.codice_filiale:
            raise ValueError("L'ATM deve appartenere alla stessa filiale")
        if any(a.codice_atm == atm.codice_atm for a in self.atm):
            raise OperazioneNonConsentitaError("Codice ATM gia presente")
        self.atm.append(atm)

    def aggiungi_finanziamento(self, finanziamento):
        if not isinstance(finanziamento, Finanziamento):
            raise TypeError("L'oggetto deve essere un Finanziamento")
        if any(f.id_operazione == finanziamento.id_operazione for f in self.finanziamenti):
            raise OperazioneNonConsentitaError("ID finanziamento gia presente")
        self.finanziamenti.append(finanziamento)

    def aggiungi_investimento(self, investimento):
        if not isinstance(investimento, Investimento):
            raise TypeError("L'oggetto deve essere un Investimento")
        if any(i.id_operazione == investimento.id_operazione for i in self.investimenti):
            raise OperazioneNonConsentitaError("ID investimento gia presente")
        self.investimenti.append(investimento)

    def __str__(self):
        return f"=== FILIALE ===\nCodice: {self.codice_filiale}\nNome: {self.nome}\nSede: {self.citta} ({self.provincia}) - {self.regione}\nData apertura: {self.data_apertura.strftime('%d/%m/%Y')}\nDirettore: {self.direttore.nome} {self.direttore.cognome}\nDipendenti: {len(self.dipendenti)}\nATM: {len(self.atm)}\nClienti: {len(self.clienti)}\nFinanziamenti: {len(self.finanziamenti)}\nInvestimenti: {len(self.investimenti)}"
