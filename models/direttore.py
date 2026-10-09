from __future__ import annotations
from datetime import date
from .addetto_sicurezza import AddettoAllaSicurezza
from .finanziamento import Finanziamento
from .contratti import GestioneInvestimenti
from .gestore import Gestore
from .investimento import Investimento
from .eccezioni import OperazioneNonConsentitaError
from .persona import Persona
from .contratti import Promozione
from .specialista import Specialista
from .enum import Specializzazione
from .enum import StatoRichiesta


class Direttore(Specialista, GestioneInvestimenti, Promozione):

    def __init__(self, nome:str, cognome:str, codice_fiscale:str, recapito:str, id_dipendente:int, data_assunzione:date, specializzazione:Specializzazione, liv_autorizzazione:int):
        super().__init__(nome, cognome, codice_fiscale, recapito, id_dipendente, data_assunzione, specializzazione)
        if not isinstance(liv_autorizzazione, int):
            raise TypeError("Il livello di autorizzazione deve essere un intero")
        if liv_autorizzazione <= 0:
            raise ValueError("Il livello di autorizzazione deve essere maggiore di 0")
        self.liv_autorizzazione = liv_autorizzazione

    def investi(self, id_operazione, data_operazione, importo, conto, prodotto, profilo_rischio, rendimento_atteso):
        return Investimento(id_operazione, data_operazione, importo, conto, prodotto, profilo_rischio, rendimento_atteso)

    def cambia_stato_finanziamento(self, finanziamento, nuovo_stato):
        if not isinstance(finanziamento, Finanziamento):
            raise TypeError("L'oggetto deve essere un Finanziamento")
        if not isinstance(nuovo_stato, StatoRichiesta):
            raise TypeError("Lo stato deve essere un valore di StatoRichiesta")
        if finanziamento.stato != StatoRichiesta.RICHIESTA:
            raise OperazioneNonConsentitaError("Il finanziamento e' gia stato deliberato")
        if nuovo_stato not in (StatoRichiesta.APPROVATA, StatoRichiesta.RIFIUTATA):
            raise OperazioneNonConsentitaError("Il finanziamento puo essere solamente approvato oppure rifiutato")
        finanziamento.stato = nuovo_stato
        return finanziamento

    def promuovi_a_gestore(self, persona, id_dipendente, data_assunzione):
        if not isinstance(persona, Persona):
            raise TypeError("L'oggetto deve essere una Persona")
        if type(persona) is not Persona:
            raise OperazioneNonConsentitaError("Solo una Persona puo essere promossa a Gestore")
        return Gestore(persona.nome, persona.cognome, persona.codice_fiscale, persona.recapito, id_dipendente, data_assunzione)

    def promuovi_ad_addetto_sicurezza(self, persona, id_dipendente, data_assunzione):
        if not isinstance(persona, Persona):
            raise TypeError("L'oggetto deve essere una Persona")
        if type(persona) is not Persona:
            raise OperazioneNonConsentitaError("Solo una Persona puo diventare AddettoAllaSicurezza")
        return AddettoAllaSicurezza(persona.nome, persona.cognome, persona.codice_fiscale, persona.recapito, id_dipendente, data_assunzione)

    def promuovi_a_specialista(self, gestore, specializzazione):
        if type(gestore) is not Gestore:
            raise OperazioneNonConsentitaError("Solo un Gestore puo essere promosso a Specialista")
        return Specialista(gestore.nome, gestore.cognome, gestore.codice_fiscale, gestore.recapito, gestore.id_dipendente, gestore.data_assunzione, specializzazione)

    def promuovi_a_direttore(self, specialista, liv_autorizzazione):
        if type(specialista) is not Specialista:
            raise OperazioneNonConsentitaError("Solo uno Specialista puo essere promosso a Direttore")
        return Direttore(specialista.nome, specialista.cognome, specialista.codice_fiscale, specialista.recapito, specialista.id_dipendente, specialista.data_assunzione, specialista.specializzazione, liv_autorizzazione)

    def __str__(self):
        return f"=== DIRETTORE ===\n{Persona.__str__(self)}ID Dipendente: {self.id_dipendente}\nData assunzione: {self.data_assunzione.strftime('%d/%m/%Y')}\nSpecializzazione: {self.specializzazione.value}\nLivello Autorizzazione: {self.liv_autorizzazione}"
