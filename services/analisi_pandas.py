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

    def clienti_citta_uniformata(self, codice_filiale):
        df = self.tabella('clienti' , codice_filiale)
        df['citta'] = df['citta'].astype('string').str.strip().str.title()
        return df[['numero_cliente' , 'nome' , 'cognome' , 'citta']]

    def clienti_anno_registrazione(self, codice_filiale):
        df = self.tabella('clienti', codice_filiale)
        df['data_registrazione'] = pd.to_datetime(df['data_registrazione'], errors='coerce')
        df['data_registrazione'] = df['data_registrazione'].dt.year
        return df[['numero_cliente' , 'data_registrazione']]

    def conteggio_segmenti(self, codice_filiale):
        df = self.tabella('clienti' , codice_filiale)
        if df.empty : return pd.DataFrame(columns=['segmento' , 'numero_clienti'])
        risultato = df.groupby('segmento' , dropna=False).size().reset_index(name='numero_clienti')
        return risultato.sort_values('numero_clienti', ascending=False)

    def saldo_per_cliente(self, codice_filiale):
        df = self.tabella('conti' , codice_filiale)
        if df.empty : return pd.DataFrame(columns=['numero_cliente' , 'numero_conti' , 'saldo_totale' , 'saldo_medio'])
        df['saldo'] = pd.to_numeric(df['saldo'] , errors='coerce')
        return df.groupby('numero_cliente', as_index=False).agg(
            numero_conti=('id_conto' , 'count'),
            saldo_totale=('saldo' , 'sum'),
            saldo_medio=('saldo' , 'mean')
        )

    # #crosstab
    # def incrocio_movimenti(self, codice_filiale):
    #     df = self.tabella('movimenti', codice_filiale)
    #     if df.empty : return pd.DataFrame()
    #     return pd.crosstab(df['canale'], df['tipo'])

    #pivot_table
    def incrocio_movimenti(self, codice_filiale):
        movimenti = self.tabella('movimenti', codice_filiale)
        movimenti['importo'] = pd.to_numeric(movimenti['importo'], errors='coerce')
        riepilogo = movimenti.pivot_table(index='canale' , columns='tipo', values='importo', aggfunc='sum', fill_value=0, dropna=True)
        return riepilogo

    def clienti_e_conti(self, codice_filiale):
        clienti = self.tabella('clienti', codice_filiale)
        saldi = self.saldo_per_cliente(codice_filiale)
        anagrafica = clienti[[
            'numero_cliente', 'nome' , 'cognome', 'segmento'
        ]].copy()
        uniti = anagrafica.merge(saldi, on='numero_cliente' , how='left', validate='one_to_one')
        uniti['numero_conti'] = uniti['numero_conti'].fillna(0).astype(int)
        uniti['saldo_totale'] = uniti['saldo_totale'].fillna(0.0).astype(float)
        uniti['saldo_medio'] = uniti['saldo_medio'].fillna(0.0).astype(float)
        return uniti.sort_values('numero_cliente')

    