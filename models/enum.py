from __future__ import annotations
from enum import Enum


class TipoVersamento(Enum):
    CONTANTI = "Contanti"
    ASSEGNO = "Assegno"

class StatoRichiesta(Enum):
    RICHIESTA = "Richiesta"
    APPROVATA = "Approvata"
    RIFIUTATA = "Rifiutata"

class Specializzazione(Enum):
    PRESTITI = "Prestiti"
    MUTUI = "Mutui"
    INVESTIMENTI = "Investimenti"

class SegmentoCliente(Enum):
    STANDARD = "Standard"
    PREMIUM = "Premium"
    BUSINESS = "Business"

class TipoConto(Enum):
    CORRENTE = "Corrente"
    RISPARMIO = "Risparmio"

class StatoConto(Enum):
    ATTIVO = "Attivo"
    BLOCCATO = "Bloccato"
    CHIUSO = "Chiuso"

class CanaleOperazione(Enum):
    FILIALE = "Filiale"
    ATM = "ATM"
    ONLINE = "Online"

class ProfiloRischio(Enum):
    BASSO = "Basso"
    MEDIO = "Medio"
    ALTO = "Alto"

class StatoInvestimento(Enum):
    ATTIVO = "Attivo"
    CHIUSO = "Chiuso"

class StatoATM(Enum):
    ATTIVO = "Attivo"
    MANUTENZIONE = "Manutenzione"
    FUORI_SERVIZIO = "Fuori servizio"
