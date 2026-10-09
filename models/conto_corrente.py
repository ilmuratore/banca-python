from __future__ import annotations
from datetime import date
from .cliente import Cliente
from .eccezioni import ClienteNonValidoError
from .eccezioni import OperazioneNonConsentitaError
from .enum import StatoConto
from .enum import TipoConto


class ContoCorrente:

    def __init__(self, id_conto:int, iban:str, intestatario:Cliente, tipo_conto:TipoConto, data_apertura:date, stato:StatoConto=StatoConto.ATTIVO):
        self.id_conto = id_conto
        self.iban = iban
        self.intestatario = intestatario
        self.tipo_conto = tipo_conto
        self.data_apertura = data_apertura
        self.stato = stato
        self._saldo = 0.0
        self.movimenti = []

    @property
    def id_conto(self):
        return self._id_conto

    @id_conto.setter
    def id_conto(self, valore):
        if not isinstance(valore, int):
            raise TypeError("L'ID conto deve essere un intero")
        if valore <= 0:
            raise ValueError("L'ID conto deve essere maggiore di 0")
        self._id_conto = valore

    @property
    def iban(self):
        return self._iban

    @iban.setter
    def iban(self, valore):
        if not isinstance(valore, str):
            raise TypeError("L'IBAN deve essere una stringa")
        valore = valore.replace(" ", "").upper()
        if valore == "":
            raise ValueError("L'IBAN non puo essere vuoto")
        if len(valore) != 27:
            raise ValueError("Un IBAN Italiano deve contenere 27 caratteri")
        if not valore.startswith("IT"):
            raise ValueError("L'IBAN Italiano deve iniziare per IT")
        if not valore.isalnum():
            raise ValueError("L'IBAN contiene caratteri non validi")
        self._iban = valore

    @property
    def intestatario(self):
        return self._intestatario

    @intestatario.setter
    def intestatario(self, valore):
        if not isinstance(valore, Cliente):
            raise ClienteNonValidoError("L'intestatario deve essere un oggetto Cliente")
        self._intestatario = valore

    @property
    def tipo_conto(self):
        return self._tipo_conto

    @tipo_conto.setter
    def tipo_conto(self, valore):
        if not isinstance(valore, TipoConto):
            raise TypeError("Il tipo conto deve essere un valore di TipoConto")
        self._tipo_conto = valore

    @property
    def data_apertura(self):
        return self._data_apertura

    @data_apertura.setter
    def data_apertura(self, valore):
        if not isinstance(valore, date):
            raise TypeError("La data di apertura deve essere un oggetto date")
        if valore > date.today():
            raise ValueError("La data di apertura non puo essere futura")
        self._data_apertura = valore

    @property
    def stato(self):
        return self._stato

    @stato.setter
    def stato(self, valore):
        if not isinstance(valore, StatoConto):
            raise TypeError("Lo stato deve essere un valore di StatoConto")
        self._stato = valore

    @property
    def saldo(self):
        return self._saldo

    def verifica_operativo(self):
        if self.stato != StatoConto.ATTIVO:
            raise OperazioneNonConsentitaError(f"Il conto e' {self.stato.value.lower()} e non puo eseguire operazioni")

    def _aumenta_saldo(self, importo):
        self._saldo += importo

    def _diminuisci_saldo(self, importo):
        self._saldo -= importo

    def _imposta_saldo(self, importo):
        if not isinstance(importo, (int, float)):
            raise TypeError("Il saldo deve essere un numero")
        if importo < 0:
            raise ValueError("Il saldo non puo essere negativo")
        self._saldo = float(importo)

    def __str__(self):
        return f"=== CONTO CORRENTE ===\nID Conto: {self.id_conto}\nIBAN: {self.iban}\nIntestatario: {self.intestatario.nome} {self.intestatario.cognome}\nNumero Cliente: {self.intestatario.numero_cliente}\nTipo: {self.tipo_conto.value}\nData apertura: {self.data_apertura.strftime('%d/%m/%Y')}\nStato: {self.stato.value}\nSaldo: {self.saldo:.2f} euro\nNumero Movimenti: {len(self.movimenti)}"
