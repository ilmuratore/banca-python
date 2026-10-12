import pandas as pd

from repository.postgresql import DatabasePostgreSQL

class AnalisiPandas:
    
    def __init__(self, database: DatabasePostgreSQL):
        self.database = database

    def tabella(self, entita, codice_filiale):
        if entita not in DatabasePostgreSQL.COLONNE: raise ValueError("Entita' non disponibile per analisi")
        righe = self.database.lista(entita, codice_filiale)
        return pd.DataFrame(righe, columns=list(DatabasePostgreSQL.COLONNE[entita]))