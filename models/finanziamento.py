from __future__ import annotations
from abc import ABC
from datetime import date
from .enum import CanaleOperazione
from .conto_corrente import ContoCorrente
from .operazione import Operazione
from .eccezioni import OperazioneNonConsentitaError
from .enum import StatoRichiesta


class Finanziamento(Operazione, ABC):

    def __init__(self, id_operazione:int, data_operazione:date, importo:float, conto:ContoCorrente, durata_mesi:int, tasso:float, finalita:str):
        super().__init__(id_operazione, data_operazione, importo, conto, CanaleOperazione.FILIALE, "Richiesta finanziamento")
        self.durata_mesi = durata_mesi
        self.tasso = tasso
        self.finalita = finalita
        self.stato = StatoRichiesta.RICHIESTA
        self.eseguito = False

    @property
    def durata_mesi(self):
        return self._durata_mesi

    @durata_mesi.setter
    def durata_mesi(self, valore):
        if not isinstance(valore, int):
            raise TypeError("La durata deve essere un intero")
        if valore <= 0 or valore > 480:
            raise ValueError("La durata deve essere compresa tra 1 e 480 mesi")
        self._durata_mesi = valore

    @property
    def tasso(self):
        return self._tasso

    @tasso.setter
    def tasso(self, valore):
        if not isinstance(valore, (int, float)):
            raise TypeError("Il tasso deve essere un numero")
        if valore < 0 or valore > 30:
            raise ValueError("Il tasso deve essere compreso tra 0 e 30")
        self._tasso = float(valore)

    @property
    def finalita(self):
        return self._finalita

    @finalita.setter
    def finalita(self, valore):
        if not isinstance(valore, str) or valore.strip() == "":
            raise ValueError("La finalita non puo essere vuota")
        self._finalita = valore.strip()

    def esegui(self):
        self.conto.verifica_operativo()
        if self.stato != StatoRichiesta.APPROVATA:
            raise OperazioneNonConsentitaError("Il finanziamento deve essere approvato prima dell'esecuzione")
        if self.eseguito:
            raise OperazioneNonConsentitaError("Il finanziamento e' gia stato erogato")
        self.conto._aumenta_saldo(self.importo)
        self.conto.movimenti.append(self)
        self.eseguito = True

    def __str__(self):
        return f"{super().__str__()}\nCliente: {self.conto.intestatario.nome} {self.conto.intestatario.cognome}\nDurata: {self.durata_mesi} mesi\nTasso: {self.tasso:.2f}%\nFinalita: {self.finalita}\nStato: {self.stato.value}\nErogato: {'Si' if self.eseguito else 'No'}"
