from __future__ import annotations
from datetime import date
from .enum import CanaleOperazione
from .conto_corrente import ContoCorrente
from .movimento import MovimentoContoCorrente
from .eccezioni import OperazioneNonConsentitaError
from .eccezioni import SaldoInsufficienteError


class Prelievo(MovimentoContoCorrente):

    def __init__(self, id_operazione:int, data_operazione:date, importo:float, conto:ContoCorrente, canale:CanaleOperazione=CanaleOperazione.FILIALE, causale:str="Prelievo"):
        super().__init__(id_operazione, data_operazione, importo, conto, canale, causale)

    def esegui(self):
        self.conto.verifica_operativo()
        if self.importo > self.conto.saldo:
            raise SaldoInsufficienteError(f"Saldo insufficiente. Disponibile: {self.conto.saldo:.2f} €")
        if self.importo > 5_000:
            raise OperazioneNonConsentitaError("Il prelievo supera il limite consentito")
        self.conto._diminuisci_saldo(self.importo)
        self.conto.movimenti.append(self)

    def __str__(self):
        return f"--- PRELIEVO ---\n{super().__str__()}"
