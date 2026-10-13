import pandas as pd

from repository.postgresql import DatabasePostgreSQL

class AnalisiPandas:
    
    def __init__(self, database: DatabasePostgreSQL):
        self.database = database

    def tabella(self, entita, codice_filiale):
        if entita not in DatabasePostgreSQL.COLONNE: raise ValueError("Entita' non disponibile per analisi")
        righe = self.database.lista(entita, codice_filiale)
        return pd.DataFrame(righe, columns=list(DatabasePostgreSQL.COLONNE[entita]))

    def clienti_per_segmento(self, codice_filiale, segmento):
        df = self.tabella('clienti', codice_filiale)
        colonne = ['numero_cliente', 'nome' , 'cognome', 'citta', 'segmento']
        return df.loc[df['segmento'] == segmento, colonne].copy()

    def conti_sopra_soglia(self, codice_filiale, minimo):
        df = self.tabella('conti', codice_filiale)
        df['saldo'] = pd.to_numeric(df['saldo'], errors='coerce')
        risultato = df.loc[df['saldo'] >= minimo, ['id_conto' , 'numero_cliente', 'tipo_conto' , 'stato' , 'saldo']].copy()
        return risultato.sort_values('saldo' , ascending=False)

    def qualita_clienti(self, codice_filiale):
        df = self.tabella('clienti' , codice_filiale)
        email = df['email'].astype('string').str.strip()
        mancanti_email = email.isna() | email.eq('')
        duplicati_id = df.duplicated(subset=['numero_cliente']).sum()
        return {'totale clienti' : len(df), 'email_mancanti_o_vuote' : int(mancanti_email.sum()), 'id_duplicati' : int(duplicati_id)}

