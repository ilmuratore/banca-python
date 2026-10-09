from __future__ import annotations
from datetime import date
from .enum import CanaleOperazione
from .conto_corrente import ContoCorrente
from .operazione import Operazione
from .eccezioni import OperazioneNonConsentitaError
from .enum import ProfiloRischio
from .eccezioni import SaldoInsufficienteError
from .enum import StatoInvestimento


class Investimento(Operazione):

    def __init__(self, id_operazione:int, data_operazione:date, importo:float, conto:ContoCorrente, prodotto:str, profilo_rischio:ProfiloRischio, rendimento_atteso:float):
        super().__init__(id_operazione, data_operazione, importo, conto, CanaleOperazione.FILIALE, "Investimento")
        self.prodotto = prodotto
        self.profilo_rischio = profilo_rischio
        self.rendimento_atteso = rendimento_atteso
        self.stato = StatoInvestimento.ATTIVO
        self.eseguito = False

    @property
    def prodotto(self):
        return self._prodotto

    @prodotto.setter
    def prodotto(self, valore):
        if not isinstance(valore, str) or valore.strip() == "":
            raise ValueError("Il prodotto non puo essere vuoto")
        self._prodotto = valore.strip()

    @property
    def profilo_rischio(self):
        return self._profilo_rischio

    @profilo_rischio.setter
    def profilo_rischio(self, valore):
        if not isinstance(valore, ProfiloRischio):
            raise TypeError("Il profilo rischio deve essere un valore di ProfiloRischio")
        self._profilo_rischio = valore

    @property
    def rendimento_atteso(self):
        return self._rendimento_atteso

    @rendimento_atteso.setter
    def rendimento_atteso(self, valore):
        if not isinstance(valore, (int, float)):
            raise TypeError("Il rendimento atteso deve essere un numero")
        if valore < -100 or valore > 100:
            raise ValueError("Il rendimento atteso deve essere compreso tra -100 e 100")
        self._rendimento_atteso = float(valore)

    def esegui(self):
        self.conto.verifica_operativo()
        if self.eseguito:
            raise OperazioneNonConsentitaError("L'investimento e' gia stato eseguito")
        if self.importo > self.conto.saldo:
            raise SaldoInsufficienteError(f"Saldo insufficiente. Disponibile: {self.conto.saldo:.2f} €")
        self.conto._diminuisci_saldo(self.importo)
        self.conto.movimenti.append(self)
        self.eseguito = True

    def __str__(self):
        return f"--- INVESTIMENTO ---\n{super().__str__()}\nProdotto: {self.prodotto}\nProfilo rischio: {self.profilo_rischio.value}\nRendimento atteso: {self.rendimento_atteso:.2f}%\nStato: {self.stato.value}"
