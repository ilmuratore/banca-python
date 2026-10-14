from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

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
        return uniti.sort_values('saldo_totale', ascending=False)

    def movimenti_per_mese(self, codice_filiale):
        df = self.tabella('movimenti', codice_filiale)
        colonne = ['mese', 'canale' , 'tipo' , 'numero_operazioni' , 'volume_euro']
        if df.empty : return pd.DataFrame(columns=colonne)
        df['data_operazione'] = pd.to_datetime(df['data_operazione'], errors='coerce')
        df['importo'] = pd.to_numeric(df['importo'], errors='coerce')
        df = df.dropna(subset=['data_operazione' , 'importo']).copy()
        if df.empty : return pd.DataFrame(columns=colonne)
        df['mese'] = df['data_operazione'].dt.strftime('%y-%m')
        return df.groupby(['mese' , 'canale' , 'tipo'], as_index=False).agg(
            numero_operazioni = ('id_operazione', 'count'),
            volume_euro=('importo' , 'sum')
        ).sort_values(['mese' , 'canale' , 'tipo'])

    def genera_grafici(self, codice_filiale, cartella_base):
        destinazione = Path(cartella_base / codice_filiale / 'grafici')
        destinazione.mkdir(parents=True, exist_ok=True)
        percorsi = []

        clienti = self.tabella('clienti' , codice_filiale)
        if not clienti.empty:
            segmenti = clienti['segmento'].value_counts().sort_index()
            fig , ax = plt.subplots(figsize=(7,4))
            segmenti.plot(kind='bar', ax=ax)
            ax.set_title('Clienti per segmento')
            ax.set_xlabel('Segmento')
            ax.set_ylabel('Numero clienti')
            fig.tight_layout()
            percorso = destinazione / 'clienti_per_segmento.png'
            fig.savefig(percorso, dpi=150)
            plt.close(fig)
            percorsi.append(percorso)


            fig , ax = plt.subplots(figsize=(7,4))
            segmenti.plot(kind='pie', ax=ax, autopct='%1.1f%%')
            ax.set_title('Distribuzione clienti per segmento')
            ax.set_ylabel('')
            fig.tight_layout()
            percorso = destinazione / 'distribuzione_segmenti.png'
            fig.savefig(percorso, dpi=150)
            plt.close(fig)
            percorsi.append(percorso)

        movimenti = self.movimenti_per_mese(codice_filiale)
        if not movimenti.empty:
                mensile = movimenti.groupby('mese')['volume_euro'].sum().sort_index()
                fig , ax = plt.subplots(figsize=(7,4))
                mensile.plot(kind='line', marker='o', ax=ax)
                ax.set_title('Volume mensile delle operazioni')
                ax.set_xlabel('Mese')
                ax.set_ylabel('Volume operazioni (euro)')
                fig.tight_layout()
                percorso = destinazione / 'volume_movimenti_mensile.png'
                fig.savefig(percorso, dpi=150)
                plt.close(fig)
                percorsi.append(percorso)

        conti = self.tabella('conti', codice_filiale)
        if not conti.empty:
            saldi = pd.to_numeric(conti['saldo'], errors='coerce').dropna()
            fig , ax = plt.subplots(figsize=(7,4))
            saldi.plot(kind='hist', bins=8, edgecolor='black', ax=ax)
            ax.set_title('Distribuzione dei saldi dei conti')
            ax.set_xlabel('Saldo (euro)')
            ax.set_ylabel('Numero conti')
            fig.tight_layout()
            percorso = destinazione / 'distribuzione_saldi.png'
            fig.savefig(percorso, dpi=150)
            plt.close(fig)
            percorsi.append(percorso)

        return percorsi