from __future__ import annotations
from datetime import date
import re
from .persona import Persona
from .enum import SegmentoCliente


class Cliente(Persona):

    def __init__(self, nome:str, cognome:str, codice_fiscale:str, recapito:str, numero_cliente:int, email:str, data_nascita:date, citta:str, data_registrazione:date, segmento:SegmentoCliente):
        super().__init__(nome, cognome, codice_fiscale, recapito)
        self.numero_cliente = numero_cliente
        self.email = email
        self.data_nascita = data_nascita
        self.citta = citta
        self.data_registrazione = data_registrazione
        self.segmento = segmento
        self.conti = []

    @property
    def numero_cliente(self):
        return self._numero_cliente

    @numero_cliente.setter
    def numero_cliente(self, valore):
        if not isinstance(valore, int):
            raise TypeError("Il numero cliente deve essere un intero")
        if valore <= 0:
            raise ValueError("Il numero cliente deve essere maggiore di 0")
        self._numero_cliente = valore

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valore):
        if not isinstance(valore, str):
            raise TypeError("L'email deve essere una stringa")
        valore = valore.strip()
        regex_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if valore == "":
            raise ValueError("L'email non puo essere vuota")
        if not re.match(regex_email, valore):
            raise ValueError("L'indirizzo email non e' valido")
        self._email = valore.lower()

    @property
    def data_nascita(self):
        return self._data_nascita

    @data_nascita.setter
    def data_nascita(self, valore):
        if not isinstance(valore, date):
            raise TypeError("La data di nascita deve essere un oggetto date")
        if valore >= date.today():
            raise ValueError("La data di nascita deve essere precedente a oggi")
        self._data_nascita = valore

    @property
    def citta(self):
        return self._citta

    @citta.setter
    def citta(self, valore):
        if not isinstance(valore, str) or valore.strip() == "":
            raise ValueError("La citta non puo essere vuota")
        self._citta = valore.strip().title()

    @property
    def data_registrazione(self):
        return self._data_registrazione

    @data_registrazione.setter
    def data_registrazione(self, valore):
        if not isinstance(valore, date):
            raise TypeError("La data di registrazione deve essere un oggetto date")
        if valore > date.today():
            raise ValueError("La data di registrazione non puo essere futura")
        self._data_registrazione = valore

    @property
    def segmento(self):
        return self._segmento

    @segmento.setter
    def segmento(self, valore):
        if not isinstance(valore, SegmentoCliente):
            raise TypeError("Il segmento deve essere un valore di SegmentoCliente")
        self._segmento = valore

    def __str__(self):
        return f"--- CLIENTE ---\n{super().__str__()}Numero Cliente: {self.numero_cliente}\nEmail: {self.email}\nData nascita: {self.data_nascita.strftime('%d/%m/%Y')}\nCitta: {self.citta}\nRegistrato il: {self.data_registrazione.strftime('%d/%m/%Y')}\nSegmento: {self.segmento.value}\nNumero Conti: {len(self.conti)}"
