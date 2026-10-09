import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _compat

from controllers.banca_controller import BancaController
from repository.postgresql import DatabasePostgreSQL
from models import OperazioneNonConsentitaError, Specializzazione

CF = 'RSSNNA90A01H501F'

def dipendente(ruolo='Gestore', filiale='FI1', specializzazione=None, livello=None):
    return {'id_dipendente': 7, 'codice_filiale': filiale, 'nome': 'Anna', 'cognome': 'Rossi', 'codice_fiscale': CF,
            'recapito': '12345', 'data_assunzione': date(2024,1,1), 'ruolo': ruolo,
            'specializzazione': specializzazione, 'liv_autorizzazione': livello}

class DatabaseFinto:
    def __init__(self, riga):
        self.riga = riga
        self.modifiche = None
    def filiali(self): return [{'codice_filiale': 'FI1'}]
    def dettaglio(self, entita, chiave, codice): return self.riga
    def modifica_dipendente(self, id_dipendente, codice, dati):
        self.modifiche = (id_dipendente, codice, dati)
        return {'id_dipendente': id_dipendente, **dati}

class TestControllerModifica(unittest.TestCase):
    def test_tutti_i_campi_senza_modifica_id(self):
        db = DatabaseFinto(dipendente())
        c = BancaController(db, None)
        modifiche = {'nome': 'Maria', 'cognome': 'Bianchi', 'codice_fiscale': 'BNCMRA90A01H501D',
                    'recapito': '987654', 'data_assunzione': date(2023,1,1), 'ruolo': 'Direttore',
                    'specializzazione': Specializzazione.INVESTIMENTI, 'liv_autorizzazione': 5, 'codice_filiale': ' fi2 '}
        res = c.modifica_dipendente(7, modifiche)
        self.assertEqual(db.modifiche[2]['codice_filiale'], 'FI2')
        self.assertEqual(db.modifiche[2]['specializzazione'], 'Investimenti')
        self.assertEqual(res['ruolo'], 'Direttore')
        self.assertEqual(res['id_dipendente'], 7)
        self.assertEqual(len(db.modifiche[2]), 9)

    def test_demozione_elimina_specializzazione_e_livello(self):
        db = DatabaseFinto(dipendente('Direttore', specializzazione='Mutui', livello=3))
        c = BancaController(db, None)
        c.modifica_dipendente(7, {'ruolo': 'Gestore'})
        self.assertIsNone(db.modifiche[2]['specializzazione'])
        self.assertIsNone(db.modifiche[2]['liv_autorizzazione'])

    def test_promozione_invalida_fermata_prima_db(self):
        db = DatabaseFinto(dipendente())
        c = BancaController(db, None)
        with self.assertRaises(ValueError): c.modifica_dipendente(7, {'ruolo': 'Direttore'})
        self.assertIsNone(db.modifiche)

    def test_id_immutabile(self):
        db = DatabaseFinto(dipendente())
        c = BancaController(db, None)
        with self.assertRaises(ValueError): c.modifica_dipendente(7, {'id_dipendente': 9})

class CursoreFake:
    def __init__(self, riga, direttore_id, target_present=True):
        self.riga = riga
        self.direttore_id = direttore_id
        self.target_present = target_present
        self.calls = []
        self.rowcount = 1
        self.last_query = ''
    def execute(self, query, params=()):
        query = str(query)
        self.last_query = query
        self.calls.append((query, tuple(params)))
        self.rowcount = 1
        self.assert_count(query,params)
    def fetchone(self):
        if self.last_query.startswith('select * from dipendente'):
            return self.riga
        if self.last_query.startswith('select direttore_id from filiale'):
            return {'direttore_id': self.direttore_id} if self.target_present else None
        raise AssertionError(self.last_query)
    @staticmethod
    def assert_count(query,params):
        assert query.count('%s') == len(params), (query,params)

class TestRepositoryModifica(unittest.TestCase):
    def esegui(self, ruolo, destination, assegnato, precedente=None):
        repo = DatabasePostgreSQL.__new__(DatabasePostgreSQL)
        cur = CursoreFake(precedente or dipendente('Direttore',specializzazione='Mutui',livello=3), assegnato)
        repo._scrittura = lambda azione: azione(cur)
        repo.dettaglio = lambda entita, chiave, codice: {'id_dipendente': chiave, 'codice_filiale': codice}
        dati = {**(precedente or dipendente('Direttore',specializzazione='Mutui',livello=3)), 'codice_filiale': destination, 'ruolo': ruolo}
        repo.modifica_dipendente(7, 'FI1', dati)
        return cur.calls

    def test_stesso_direttore_e_filiale_mantiene_nomina(self):
        calls = self.esegui('Direttore','FI1',7)
        self.assertFalse(any('set direttore_id = null' in q for q,_ in calls))
        self.assertTrue(any('set direttore_id = %s' in q for q,_ in calls))

    def test_cambio_filiale_sgancia_direttore_vecchio(self):
        calls = self.esegui('Direttore','FI2',None)
        self.assertTrue(any('set direttore_id = null' in q for q,_ in calls))
        self.assertTrue(any('set direttore_id = %s' in q for q,_ in calls))
        update = [p for q,p in calls if q.startswith('update dipendente')][0]
        self.assertEqual(len(update),11)
        self.assertEqual(update[0], 'FI2')
        self.assertEqual(update[-1], 'FI1')

    def test_demozione_non_nomina_direttore(self):
        calls = self.esegui('Gestore','FI1',7)
        self.assertTrue(any('set direttore_id = null' in q for q,_ in calls))
        self.assertFalse(any('set direttore_id = %s' in q for q,_ in calls))

    def test_nuovo_direttore_non_sovrascrive_quello_in_carica(self):
        calls = self.esegui('Direttore','FI1',88, precedente=dipendente())
        self.assertFalse(any('set direttore_id = %s' in q for q,_ in calls))

    def test_filiale_destinazione_inesistente(self):
        repo = DatabasePostgreSQL.__new__(DatabasePostgreSQL)
        cur = CursoreFake(dipendente(), None, False)
        repo._scrittura = lambda azione: azione(cur)
        dati = dipendente()
        with self.assertRaises(OperazioneNonConsentitaError): repo.modifica_dipendente(7, 'FI1', dati)
        self.assertFalse(any(q.startswith('update') for q,_ in cur.calls))

if __name__ == '__main__': unittest.main()
