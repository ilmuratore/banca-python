from __future__ import annotations
from datetime import date
from .enum import CanaleOperazione
from .eccezioni import OperazioneNonConsentitaError
from .prelievo import Prelievo
from .enum import StatoATM
from .enum import TipoVersamento
from .versamento import Versamento


class ATM:

    def __init__(self, codice_atm:str, filiale:str, stato:StatoATM=StatoATM.ATTIVO, data_installazione:date=None):
        if not isinstance(codice_atm, str) or codice_atm.strip() == "":
            raise ValueError("Il codice ATM non puo essere vuoto")
        if not isinstance(filiale, str) or filiale.strip() == "":
            raise ValueError("La filiale dell'ATM non puo essere vuota")
        if not isinstance(stato, StatoATM):
            raise TypeError("Lo stato ATM deve essere un valore di StatoATM")
        data_installazione = data_installazione or date.today()
        if not isinstance(data_installazione, date):
            raise TypeError("La data di installazione deve essere un oggetto date")
        if data_installazione > date.today():
            raise ValueError("La data di installazione non puo essere futura")
        self.codice_atm = codice_atm.strip().upper()
        self.filiale = filiale.strip().upper()
        self.stato = stato
        self.data_installazione = data_installazione

    def verifica_operativo(self):
        if self.stato != StatoATM.ATTIVO:
            raise OperazioneNonConsentitaError(f"ATM non disponibile: {self.stato.value}")

    def versa(self, id_operazione, conto, importo, tipo_versamento=TipoVersamento.CONTANTI):
        self.verifica_operativo()
        movimento = Versamento(id_operazione, date.today(), importo, conto, tipo_versamento, CanaleOperazione.ATM, f"Versamento ATM {self.codice_atm}")
        movimento.esegui()
        return movimento

    def preleva(self, id_operazione, conto, importo):
        self.verifica_operativo()
        movimento = Prelievo(id_operazione, date.today(), importo, conto, CanaleOperazione.ATM, f"Prelievo ATM {self.codice_atm}")
        movimento.esegui()
        return movimento

    def __str__(self):
        return f"ATM {self.codice_atm} - {self.stato.value} - installato il {self.data_installazione.strftime('%d/%m/%Y')}"
