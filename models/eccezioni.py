from __future__ import annotations


class ClienteNonValidoError(Exception):
    pass

class OperazioneNonConsentitaError(Exception):
    pass

class SaldoInsufficienteError(Exception):
    pass
