from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from .enum import CanaleOperazione
from .conto_corrente import ContoCorrente


class Operazione(ABC):

    def __init__(self, id_operazione:int, data_operazione:date, importo:float, conto:ContoCorrente, canale:CanaleOperazione, causale:str):
        self.id_operazione = id_operazione
        self.data_operazione = data_operazione
        self.importo = importo
        self.conto = conto
        self.canale = canale
        self.causale = causale

    @property
    def id_operazione(self):
        return self._id_operazione

    @id_operazione.setter
    def id_operazione(self, valore):
        if not isinstance(valore, int):
            raise TypeError("L'ID Operazione deve essere un intero")
        if valore <= 0:
            raise ValueError("L'ID Operazione deve essere maggiore di 0")
        self._id_operazione = valore

    @property
    def data_operazione(self):
        return self._data_operazione

    @data_operazione.setter
    def data_operazione(self, valore):
        if not isinstance(valore, date):
            raise TypeError("La data deve essere un oggetto date")
        if valore > date.today():
            raise ValueError("La data dell'operazione non puo essere futura")
        self._data_operazione = valore

    @property
    def importo(self):
        return self._importo

    @importo.setter
    def importo(self, valore):
        if not isinstance(valore, (int, float)):
            raise TypeError("L'importo deve essere un numero")
        if valore <= 0 or valore >= 10_000_000:
            raise ValueError("Importo oltre i limiti consentiti")
        self._importo = float(valore)

    @property
    def conto(self):
        return self._conto

    @conto.setter
    def conto(self, valore):
        if not isinstance(valore, ContoCorrente):
            raise TypeError("Il conto deve essere un oggetto ContoCorrente")
        self._conto = valore

    @property
    def canale(self):
        return self._canale

    @canale.setter
    def canale(self, valore):
        if not isinstance(valore, CanaleOperazione):
            raise TypeError("Il canale deve essere un valore di CanaleOperazione")
        self._canale = valore

    @property
    def causale(self):
        return self._causale

    @causale.setter
    def causale(self, valore):
        if not isinstance(valore, str) or valore.strip() == "":
            raise ValueError("La causale non puo essere vuota")
        self._causale = valore.strip()

    @abstractmethod
    def esegui(self):
        pass

    def __str__(self):
        return f"ID operazione: {self.id_operazione}\nData: {self.data_operazione.strftime('%d/%m/%Y')}\nImporto: {self.importo:.2f} €\nCanale: {self.canale.value}\nCausale: {self.causale}"
