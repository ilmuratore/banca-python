"""Controllo regressioni: numero dei placeholder e dei parametri nelle query SQL."""
import ast
import contextlib
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _compat  # noqa: F401 - fallback per test senza psycopg
from repository import postgresql
from repository.postgresql import DatabasePostgreSQL


class SQLTesto(str):
    def format(self, *args):
        return SQLTesto(super().format(*args))

    def join(self, sequenza):
        return SQLTesto(super().join(sequenza))


def identificatore(nome):
    return SQLTesto('"' + str(nome).replace('"', '""') + '"')


SQL_SIMULATO = SimpleNamespace(SQL=SQLTesto, Identifier=identificatore, Placeholder=lambda: SQLTesto('%s'))


class CursoreSimulato:
    def __init__(self):
        self.query = []
        self.rowcount = 1
        self.risultato = None

    def execute(self, query, parametri=()):
        if parametri is None:
            parametri = ()
        testo = str(query)
        numero = testo.count('%s')
        assert numero == len(parametri), f'Placeholder {numero} != parametri {len(parametri)}: {testo}'
        self.query.append((testo, tuple(parametri)))
        if 'nextval(' in testo:
            self.risultato = {'id': 42}
        elif 'select c.id_conto,c.numero_cliente,c.saldo,c.stato' in testo:
            self.risultato = {'id_conto': 8, 'numero_cliente': 7, 'saldo': 10000, 'stato': 'Attivo'}
        elif 'select 1 from cliente' in testo:
            self.risultato = {'?column?': 1}
        elif testo.startswith('select 1 from'):
            self.risultato = None
        elif 'select codice_filiale from' in testo:
            self.risultato = None
        else:
            self.risultato = None

    def fetchone(self):
        return self.risultato

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ConnessioneSimulata:
    def __init__(self):
        self.cursore = CursoreSimulato()

    @contextlib.contextmanager
    def cursor(self):
        yield self.cursore

    @contextlib.contextmanager
    def transaction(self):
        yield


class TestRepositorySQL(unittest.TestCase):
    def setUp(self):
        self.conn = ConnessioneSimulata()
        self.db = object.__new__(DatabasePostgreSQL)
        self.db.connessione = self.conn
        self.patcher = patch.object(postgresql, 'sql', SQL_SIMULATO)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_placeholder_statici_execute_e_lettura(self):
        """Ogni chiamata SQL a stringa costante deve avere parametri corrispondenti."""
        sorgente = Path(postgresql.__file__).read_text(encoding='utf-8')
        albero = ast.parse(sorgente)
        verificate = 0
        for nodo in ast.walk(albero):
            if not isinstance(nodo, ast.Call) or not isinstance(nodo.func, ast.Attribute):
                continue
            if nodo.func.attr not in ('execute', '_lettura') or not nodo.args:
                continue
            if not isinstance(nodo.args[0], ast.Constant) or not isinstance(nodo.args[0].value, str):
                continue
            query = nodo.args[0].value
            if nodo.func.attr == '_lettura':
                param = nodo.args[1] if len(nodo.args) > 1 else None
            else:
                param = nodo.args[1] if len(nodo.args) > 1 else None
            if param is None:
                quanti = 0
            elif isinstance(param, (ast.Tuple, ast.List)) and not any(isinstance(e, ast.Starred) for e in param.elts):
                quanti = len(param.elts)
            else:
                continue
            self.assertEqual(query.count('%s'), quanti, f'Riga {nodo.lineno}: {query}')
            if query.lower().startswith('insert into'):
                m = re.search(r'insert\s+into\s+\w+\s*\((.*?)\)\s*values\s*\((.*?)\)', query, re.IGNORECASE | re.DOTALL)
                if m:
                    self.assertEqual(len(m.group(1).split(',')), len(m.group(2).split(',')), f'Colonne/valori alla riga {nodo.lineno}')
            verificate += 1
        self.assertGreaterEqual(verificate, 25)

    def test_creazione_filiale_tutte_le_query(self):
        reg = lambda **d: SimpleNamespace(**d)
        f = reg(codice_filiale='FI1', nome='Prova', citta='Roma', provincia='RM', regione='Lazio', data_apertura='2020-01-01')
        d = reg(id_dipendente=1, nome='Luca', cognome='Rossi', codice_fiscale='AA', recapito='123', data_assunzione='2020-01-01', specializzazione=reg(value='Prestiti'), liv_autorizzazione=2)
        a = reg(codice_atm='ATM1', filiale='FI1', stato=reg(value='Attivo'), data_installazione='2020-01-01')
        with patch.object(self.db, 'filiale', return_value={'codice_filiale': 'FI1'}):
            self.db.nuova_filiale(f, d, a)
        self.assertEqual(len(self.conn.cursore.query), 5)  # nextval + 4 scritture

    def test_creazione_cliente_dipendente_atm_conto(self):
        reg = lambda **d: SimpleNamespace(**d)
        cliente = reg(numero_cliente=1, nome='Luca', cognome='Rossi', codice_fiscale='ABC', recapito='123', email='a@b.it', data_nascita='2000-01-01', citta='Roma', data_registrazione='2020-01-01', segmento=reg(value='Standard'))
        dipendente = reg(id_dipendente=1, nome='Luca', cognome='Rossi', codice_fiscale='ABC', recapito='123', data_assunzione='2020-01-01', specializzazione=reg(value='Mutui'))
        atm = reg(codice_atm='ATM-1', filiale='FI1', stato=reg(value='Attivo'), data_installazione='2020-01-01')
        conto = reg(id_conto=1, iban='IT1', intestatario=reg(numero_cliente=7), tipo_conto=reg(value='Corrente'), data_apertura='2020-01-01', stato=reg(value='Attivo'))
        with patch.object(self.db, 'dettaglio', return_value={'id': 42}):
            self.db.nuovo_cliente('FI1', cliente)
            for ruolo in ('Specialista', 'Gestore'):
                self.db.nuovo_dipendente('FI1', dipendente, ruolo)
            self.db.nuovo_atm(atm)
            self.db.nuovo_conto('FI1', conto)
        self.assertGreaterEqual(len(self.conn.cursore.query), 10)

    def test_modifica_sql_dinamico(self):
        with patch.object(self.db, 'dettaglio', return_value={'nome': 'A'}):
            self.db.modifica('clienti', 3, 'FI1', {'nome': 'B', 'recapito': '123'})
        self.assertIn('"nome" = %s', self.conn.cursore.query[0][0])

    def test_movimento_finanziamento_investimento(self):
        mov = {'id_conto': 8, 'tipo': 'Versamento', 'importo': 100, 'tipo_versamento': 'Contanti', 'data_operazione': '2020-01-01', 'canale': 'Filiale', 'causale': 'test'}
        fin = {'id_conto': 8, 'numero_cliente': 7, 'tipo': 'Prestito', 'data_operazione': '2020-01-01', 'importo': 150, 'durata_mesi': 12, 'tasso': 3, 'stato': 'Richiesta', 'finalita': 'test', 'eseguito': False}
        inv = {'id_conto': 8, 'numero_cliente': 7, 'data_operazione': '2020-01-01', 'importo': 150, 'prodotto': 'Obbligazione', 'profilo_rischio': 'Basso', 'rendimento_atteso': 5, 'stato': 'Attivo', 'eseguito': True}
        with patch.object(self.db, 'dettaglio', return_value={'saldo': 100}):
            self.db.nuovo_movimento('FI1', mov)
            self.db.nuovo_finanziamento('FI1', fin)
            self.db.nuovo_investimento('FI1', inv)
        self.assertGreaterEqual(len(self.conn.cursore.query), 11)

    def test_importazione_csv_upsert_dinamico(self):
        dati = {'numero_cliente': 5, 'nome': 'Luca', 'cognome': 'Rossi', 'codice_fiscale': 'ABC', 'recapito': '123', 'email': 'a@b.it', 'data_nascita': '2000-01-01', 'citta': 'Roma', 'data_registrazione': '2020-01-01', 'segmento': 'Standard'}
        with patch.object(self.db, 'dettaglio', return_value=None), patch.object(self.db, '_allinea_sequenza'):
            self.assertEqual(self.db.importa('clienti', [dati], 'FI1'), 1)
        self.assertTrue(any('on conflict' in q for q, _ in self.conn.cursore.query))


    def test_tutti_gli_elenchi_e_dettagli(self):
        for entita in self.db.CHIAVI:
            with self.subTest(entita=entita):
                self.db.lista(entita, 'FI1')
                self.db.dettaglio(entita, 1, 'FI1')
        self.assertEqual(len(self.conn.cursore.query), 16)

    def test_report_periodi_e_letture(self):
        self.db.stato_database()
        self.db.filiali()
        self.db.filiale('FI1')
        self.db.report('FI1')
        self.db.movimenti_periodo('FI1', '2020-01-01', '2020-12-31')
        self.db.movimenti_conto('FI1', 6)
        self.assertEqual(len(self.conn.cursore.query), 9)

    def test_csv_upsert_per_tutte_le_entita_anagrafiche(self):
        righe = {
            'clienti': {'numero_cliente': 5, 'nome': 'Luca', 'cognome': 'Rossi', 'codice_fiscale': 'ABC', 'recapito': '123', 'email': 'a@b.it', 'data_nascita': '2000-01-01', 'citta': 'Roma', 'data_registrazione': '2020-01-01', 'segmento': 'Standard'},
            'dipendenti': {'id_dipendente': 3, 'ruolo': 'Gestore', 'nome': 'Anna', 'cognome': 'Rossi', 'codice_fiscale': 'DEF', 'recapito': '123', 'data_assunzione': '2020-01-01', 'specializzazione': None, 'liv_autorizzazione': None},
            'atm': {'codice_atm': 'A1', 'codice_filiale': 'FI1', 'stato': 'Attivo', 'data_installazione': '2020-01-01'},
            'conti': {'id_conto': 8, 'iban': 'IT01', 'numero_cliente': 7, 'tipo_conto': 'Corrente', 'data_apertura': '2020-01-01', 'stato': 'Attivo', 'saldo': 300}
        }
        with patch.object(self.db, 'dettaglio', return_value=None), patch.object(self.db, '_allinea_sequenza'):
            for entita, riga in righe.items():
                with self.subTest(entita=entita):
                    self.assertEqual(self.db.importa(entita, [riga], 'FI1'), 1)
        self.assertEqual(sum('on conflict' in q for q, _ in self.conn.cursore.query), 4)

    def test_query_allineamento_sequenza(self):
        cur = self.conn.cursore
        old_execute = cur.execute
        def execute(query, parametri=()):
            old_execute(query, parametri)
            if 'select coalesce(max(' in str(query): cur.risultato = {'massimo': 15}
            elif 'select last_value, is_called' in str(query): cur.risultato = {'last_value': 20, 'is_called': True}
        with patch.object(cur, 'execute', side_effect=execute):
            self.db._allinea_sequenza(cur, 'clienti', 'select coalesce(max(numero_cliente),0) as massimo from cliente')
        self.assertEqual(len(cur.query), 3)

    def test_csv_filiale_update(self):
        prima = {'direttore_id': 5}
        riga = {'codice_filiale': 'FI1', 'nome_filiale': 'Filiale', 'citta': 'Roma', 'provincia': 'RM', 'regione': 'Lazio', 'data_apertura': '2020-01-01', 'direttore_id': 5}
        with patch.object(self.db, 'dettaglio', return_value=prima):
            self.assertEqual(self.db.importa('filiale', [riga], 'FI1'), 1)
        self.assertEqual(len(self.conn.cursore.query), 1)

    def test_csv_operazioni_nuovi_id(self):
        mov = {'id_operazione': 100, 'id_conto': 8, 'tipo': 'Versamento', 'importo': 20, 'tipo_versamento': 'Contanti', 'data_operazione': '2020-01-01', 'canale': 'Filiale', 'causale': 'test'}
        fin = {'id_operazione': 101, 'id_conto': 8, 'numero_cliente': 7, 'tipo': 'Prestito', 'data_operazione': '2020-01-01', 'importo': 150, 'durata_mesi': 12, 'tasso': 3, 'stato': 'Richiesta', 'finalita': 'test', 'eseguito': False}
        inv = {'id_operazione': 102, 'id_conto': 8, 'numero_cliente': 7, 'data_operazione': '2020-01-01', 'importo': 150, 'prodotto': 'Obbligazione', 'profilo_rischio': 'Basso', 'rendimento_atteso': 5, 'stato': 'Attivo', 'eseguito': True}
        with patch.object(self.db, 'dettaglio', return_value=None), patch.object(self.db, '_allinea_sequenza'):
            for nome, riga in [('movimenti', mov), ('finanziamenti', fin), ('investimenti', inv)]:
                with self.subTest(nome=nome):
                    self.assertEqual(self.db.importa(nome, [riga], 'FI1'), 1)
        self.assertGreaterEqual(len(self.conn.cursore.query), 12)


if __name__ == '__main__':
    unittest.main()
