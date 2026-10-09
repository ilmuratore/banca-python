from __future__ import annotations
from datetime import date
from .conto_corrente import ContoCorrente
from .finanziamento import Finanziamento


class Prestito(Finanziamento):

    def __init__(self, id_operazione:int, data_operazione:date, importo:float, conto:ContoCorrente, durata_mesi:int, tasso:float, finalita:str):
        super().__init__(id_operazione, data_operazione, importo, conto, durata_mesi, tasso, finalita)
        self.causale = "Prestito"

    def __str__(self):
        return f"--- PRESTITO ---\n{super().__str__()}"
