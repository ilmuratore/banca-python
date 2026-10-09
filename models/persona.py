from __future__ import annotations


class Persona:

    def __init__(self, nome:str, cognome:str, codice_fiscale:str, recapito:str):
        self.nome = nome
        self.cognome = cognome
        self.codice_fiscale = codice_fiscale
        self.recapito = recapito

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valore):
        if not isinstance(valore, str):
            raise TypeError("Il nome deve essere una stringa")
        valore = valore.strip()
        if valore == "":
            raise ValueError("Il nome non puo essere vuoto")
        if not valore.replace(" ", "").isalpha():
            raise ValueError("Il nome deve contenere solamente lettere")
        self._nome = valore.title()

    @property
    def cognome(self):
        return self._cognome

    @cognome.setter
    def cognome(self, valore):
        if not isinstance(valore, str):
            raise TypeError("Il cognome deve essere una stringa")
        valore = valore.strip()
        if valore == "":
            raise ValueError("Il cognome non puo essere vuoto")
        if not valore.replace(" ", "").isalpha():
            raise ValueError("Il cognome deve contenere solamente lettere")
        self._cognome = valore.title()

    @property
    def codice_fiscale(self):
        return self._codice_fiscale

    @codice_fiscale.setter
    def codice_fiscale(self, valore):
        if not isinstance(valore, str):
            raise TypeError("Il codice fiscale deve essere una stringa")
        valore = valore.strip().upper()
        if len(valore) != 16:
            raise ValueError("Il codice fiscale deve avere 16 caratteri")
        if not valore.isalnum():
            raise ValueError("Il codice fiscale deve contenere solamente lettere e numeri")
        self._codice_fiscale = valore

    @property
    def recapito(self):
        return self._recapito

    @recapito.setter
    def recapito(self, valore):
        if not isinstance(valore, str):
            raise TypeError("Il recapito deve essere una stringa")
        if valore.strip() == "":
            raise ValueError("Il recapito non puo essere vuoto")
        self._recapito = valore.strip()

    def __str__(self):
        return f"Nome: {self.nome}\nCognome: {self.cognome}\nCodice Fiscale: {self.codice_fiscale}\nRecapito: {self.recapito}\n"
