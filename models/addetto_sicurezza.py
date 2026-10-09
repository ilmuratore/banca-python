from __future__ import annotations
from datetime import date
from .persona import Persona


class AddettoAllaSicurezza(Persona):

    def __init__(self, nome:str, cognome:str, codice_fiscale:str, recapito:str, id_dipendente:int, data_assunzione:date):
        super().__init__(nome, cognome, codice_fiscale, recapito)
        if not isinstance(id_dipendente, int):
            raise TypeError("L'ID Dipendente deve essere un intero")
        if id_dipendente <= 0:
            raise ValueError("L'ID Dipendente deve essere maggiore di 0")
        if not isinstance(data_assunzione, date):
            raise TypeError("La data di assunzione deve essere un oggetto date")
        if data_assunzione > date.today():
            raise ValueError("La data di assunzione non puo essere futura")
        self.id_dipendente = id_dipendente
        self.data_assunzione = data_assunzione

    def __str__(self):
        return f"=== ADDETTO ALLA SICUREZZA ===\n{super().__str__()}ID Dipendente: {self.id_dipendente}\nData assunzione: {self.data_assunzione.strftime('%d/%m/%Y')}"
