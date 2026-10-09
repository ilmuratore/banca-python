from __future__ import annotations
from datetime import date
from .enum import CanaleOperazione
from .cliente import Cliente
from .conto_corrente import ContoCorrente
from .contratti import GestioneConto
from .persona import Persona
from .prelievo import Prelievo
from .enum import TipoConto
from .versamento import Versamento


class Gestore(Persona, GestioneConto):

    def __init__(self, nome:str, cognome:str, codice_fiscale:str, recapito:str, id_dipendente:int, data_assunzione:date):
        super().__init__(nome, cognome, codice_fiscale, recapito)
        self.id_dipendente = id_dipendente
        self.data_assunzione = data_assunzione

    @property
    def id_dipendente(self):
        return self._id_dipendente

    @id_dipendente.setter
    def id_dipendente(self, valore):
        if not isinstance(valore, int):
            raise TypeError("L'ID Dipendente deve essere un intero")
        if valore <= 0:
            raise ValueError("L'ID Dipendente deve essere maggiore di 0")
        self._id_dipendente = valore

    @property
    def data_assunzione(self):
        return self._data_assunzione

    @data_assunzione.setter
    def data_assunzione(self, valore):
        if not isinstance(valore, date):
            raise TypeError("La data di assunzione deve essere un oggetto date")
        if valore > date.today():
            raise ValueError("La data di assunzione non puo essere futura")
        self._data_assunzione = valore

    def apri_conto(self, id_conto, iban, cliente, tipo_conto=TipoConto.CORRENTE, data_apertura=None):
        if not isinstance(cliente, Cliente):
            raise TypeError("Solo un Cliente puo essere intestatario di un conto")
        nuovo_conto = ContoCorrente(id_conto, iban, cliente, tipo_conto, data_apertura or date.today())
        cliente.conti.append(nuovo_conto)
        return nuovo_conto

    def versa(self, id_operazione, conto, importo, tipo_versamento, canale=CanaleOperazione.FILIALE, causale="Versamento"):
        movimento = Versamento(id_operazione, date.today(), importo, conto, tipo_versamento, canale, causale)
        movimento.esegui()
        return movimento

    def preleva(self, id_operazione, conto, importo, canale=CanaleOperazione.FILIALE, causale="Prelievo"):
        movimento = Prelievo(id_operazione, date.today(), importo, conto, canale, causale)
        movimento.esegui()
        return movimento

    def __str__(self):
        return f"=== GESTORE ===\n{super().__str__()}ID Dipendente: {self.id_dipendente}\nData assunzione: {self.data_assunzione.strftime('%d/%m/%Y')}"
