from __future__ import annotations
from datetime import date
from .contratti import GestioneFinanziamenti
from .gestore import Gestore
from .mutuo import Mutuo
from .persona import Persona
from .prestito import Prestito
from .enum import Specializzazione


class Specialista(Gestore, GestioneFinanziamenti):

    def __init__(self, nome:str, cognome:str, codice_fiscale:str, recapito:str, id_dipendente:int, data_assunzione:date, specializzazione:Specializzazione):
        super().__init__(nome, cognome, codice_fiscale, recapito, id_dipendente, data_assunzione)
        if not isinstance(specializzazione, Specializzazione):
            raise TypeError("La specializzazione deve essere un valore di Specializzazione")
        self.specializzazione = specializzazione

    def richiedi_prestito(self, id_operazione, data_operazione, importo, conto, durata_mesi, tasso, finalita):
        return Prestito(id_operazione, data_operazione, importo, conto, durata_mesi, tasso, finalita)

    def richiedi_mutuo(self, id_operazione, data_operazione, importo, conto, durata_mesi, tasso, finalita):
        return Mutuo(id_operazione, data_operazione, importo, conto, durata_mesi, tasso, finalita)

    def __str__(self):
        return f"=== SPECIALISTA ===\n{Persona.__str__(self)}ID Dipendente: {self.id_dipendente}\nData assunzione: {self.data_assunzione.strftime('%d/%m/%Y')}\nSpecializzazione: {self.specializzazione.value}"
