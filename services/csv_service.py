import csv
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from repository.postgresql import DatabasePostgreSQL


class StrutturaFileError(ValueError):
    pass


class ServizioCSV:
    ENTITA = tuple(DatabasePostgreSQL.CHIAVI)
    COLONNE = DatabasePostgreSQL.COLONNE
    CAMPI_INTERI = {'id_dipendente', 'direttore_id', 'numero_cliente', 'id_conto', 'id_operazione', 'durata_mesi', 'liv_autorizzazione'}
    CAMPI_NUMERICI = {'saldo', 'importo', 'tasso', 'rendimento_atteso'}
    CAMPI_DATA = {'data_apertura', 'data_assunzione', 'data_nascita', 'data_registrazione', 'data_installazione', 'data_operazione'}
    CAMPI_BOOLEANI = {'eseguito'}
    CAMPI_NULL = {'tipo_versamento', 'specializzazione', 'liv_autorizzazione'}

    def __init__(self, cartella='data/csv'):
        self.cartella = Path(cartella)

    def percorso(self, entita, codice):
        return self.cartella / codice / f'{entita}.csv'

    def _colonne(self, entita):
        if entita not in self.COLONNE: raise ValueError('Entita CSV inesistente')
        return self.COLONNE[entita]

    def esporta_entita(self, entita, righe, codice, percorso=None):
        colonne = self._colonne(entita)
        destinazione = Path(percorso) if percorso else self.percorso(entita, codice)
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        with destinazione.open('w', newline='', encoding='utf-8-sig') as file:
            scrittore = csv.DictWriter(file, delimiter=';', fieldnames=colonne)
            scrittore.writeheader()
            for riga in righe:
                valori = {}
                for campo in colonne:
                    valore = riga.get(campo)
                    if valore is None: valore = ''
                    elif isinstance(valore, bool): valore = '1' if valore else '0'
                    elif isinstance(valore, date): valore = valore.strftime('%d/%m/%Y')
                    elif isinstance(valore, Decimal): valore = format(valore, 'f').replace('.', ',')
                    valori[campo] = valore
                scrittore.writerow(valori)
        return destinazione, len(righe)

    def _converti(self, campo, valore, linea):
        valore = valore.strip()
        if not valore and campo in self.CAMPI_NULL: return None
        if not valore: raise StrutturaFileError(f'Riga {linea}: campo {campo} vuoto')
        try:
            if campo in self.CAMPI_INTERI: return int(valore)
            if campo in self.CAMPI_NUMERICI: return Decimal(valore.replace(',', '.'))
            if campo in self.CAMPI_DATA:
                giorno = datetime.strptime(valore, '%d/%m/%Y').date()
                if giorno > date.today(): raise StrutturaFileError(f'Riga {linea}: data futura in {campo}')
                return giorno
            if campo in self.CAMPI_BOOLEANI:
                if valore not in ('0', '1'): raise ValueError()
                return valore == '1'
            return valore
        except (ValueError, InvalidOperation) as errore:
            raise StrutturaFileError(f'Riga {linea}: valore non valido per {campo}: {valore}') from errore

    def importa_entita(self, entita, percorso):
        colonne = self._colonne(entita)
        origine = Path(percorso)
        if not origine.is_file(): raise FileNotFoundError(f'CSV non trovato: {origine}')
        with origine.open(newline='', encoding='utf-8-sig') as file:
            lettore = csv.DictReader(file, delimiter=';')
            if lettore.fieldnames != list(colonne):
                raise StrutturaFileError(f'Intestazioni CSV errate per {entita}. Attese: {";".join(colonne)}')
            risultato = []
            for numero, riga in enumerate(lettore, 2):
                if None in riga or any(v is None for v in riga.values()): raise StrutturaFileError(f'Riga {numero}: numero di colonne errato')
                if all(not v.strip() for v in riga.values()): continue
                risultato.append({campo: self._converti(campo, riga[campo], numero) for campo in colonne})
            return risultato
