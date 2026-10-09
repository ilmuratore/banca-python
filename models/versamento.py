from __future__ import annotations
from datetime import date
from .enum import CanaleOperazione
from .conto_corrente import ContoCorrente
from .movimento import MovimentoContoCorrente
from .eccezioni import OperazioneNonConsentitaError
from .enum import TipoVersamento


class Versamento(MovimentoContoCorrente):

    def __init__(self, id_operazione:int, data_operazione:date, importo:float, conto:ContoCorrente, tipo_versamento:TipoVersamento, canale:CanaleOperazione=CanaleOperazione.FILIALE, causale:str="Versamento"):
        super().__init__(id_operazione, data_operazione, importo, conto, canale, causale)
        self.tipo_versamento = tipo_versamento

    @property
    def tipo_versamento(self):
        return self._tipo_versamento

    @tipo_versamento.setter
    def tipo_versamento(self, valore):
        if not isinstance(valore, TipoVersamento):
            raise TypeError("Il tipo di versamento deve essere TipoVersamento.CONTANTI oppure TipoVersamento.ASSEGNO")
        self._tipo_versamento = valore

    def esegui(self):
        self.conto.verifica_operativo()
        if self.tipo_versamento == TipoVersamento.CONTANTI and self.importo > 5_000:
            raise OperazioneNonConsentitaError("Versamento in contanti oltre il limite consentito")
        self.conto._aumenta_saldo(self.importo)
        self.conto.movimenti.append(self)

    def __str__(self):
        return f"--- VERSAMENTO ---\n{super().__str__()}\nTipo: {self.tipo_versamento.value}"
