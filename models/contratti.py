from __future__ import annotations
from abc import ABC, abstractmethod


class GestioneConto(ABC):

    @abstractmethod
    def apri_conto(self, id_conto, iban, cliente, tipo_conto, data_apertura):
        pass

    @abstractmethod
    def versa(self, id_operazione, conto, importo, tipo_versamento, canale, causale):
        pass

    @abstractmethod
    def preleva(self, id_operazione, conto, importo, canale, causale):
        pass

class GestioneFinanziamenti(ABC):

    @abstractmethod
    def richiedi_prestito(self, id_operazione, data_operazione, importo, conto, durata_mesi, tasso, finalita):
        pass

    @abstractmethod
    def richiedi_mutuo(self, id_operazione, data_operazione, importo, conto, durata_mesi, tasso, finalita):
        pass

class GestioneInvestimenti(ABC):

    @abstractmethod
    def investi(self, id_operazione, data_operazione, importo, conto, prodotto, profilo_rischio, rendimento_atteso):
        pass

class Promozione(ABC):

    @abstractmethod
    def promuovi_a_gestore(self, persona, id_dipendente, data_assunzione):
        pass

    @abstractmethod
    def promuovi_ad_addetto_sicurezza(self, persona, id_dipendente, data_assunzione):
        pass

    @abstractmethod
    def promuovi_a_specialista(self, gestore, specializzazione):
        pass

    @abstractmethod
    def promuovi_a_direttore(self, specialista, liv_autorizzazione):
        pass
