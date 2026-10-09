import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _compat

import contextlib
import unittest
from repository.postgresql import DatabasePostgreSQL


class ConnessioneSimulata:
    def __init__(self):
        self.commit = 0
        self.rollback = 0
        self.query = []

    @contextlib.contextmanager
    def transaction(self):
        try:
            yield
            self.commit += 1
        except Exception:
            self.rollback += 1
            raise

    @contextlib.contextmanager
    def cursor(self):
        yield self

    def execute(self, query, parametri=()):
        self.query.append((query, parametri))


class TestScritturaAtomica(unittest.TestCase):

    def setUp(self):
        self.database = object.__new__(DatabasePostgreSQL)
        self.conn = ConnessioneSimulata()
        self.database.connessione = self.conn

    def test_successo_commit_automatico(self):
        result = self.database._scrittura(lambda cursore: (cursore.execute('insert into cliente values (...)'), 5)[1])
        self.assertEqual(result, 5)
        self.assertEqual(self.conn.commit, 1)
        self.assertEqual(self.conn.rollback, 0)

    def test_errore_rollback_automatico(self):
        def fallisci(cursore):
            cursore.execute('insert into cliente values (...)')
            raise ValueError('Dati non validi')
        with self.assertRaises(ValueError): self.database._scrittura(fallisci)
        self.assertEqual(self.conn.commit, 0)
        self.assertEqual(self.conn.rollback, 1)

    def test_due_query_in_unica_transazione(self):
        def movimento(cursore):
            cursore.execute('insert into movimento ...')
            cursore.execute('update conto_corrente set saldo = saldo + 5')
        self.database._scrittura(movimento)
        self.assertEqual(self.conn.commit, 1)
        self.assertEqual(len(self.conn.query), 2)


if __name__ == '__main__': unittest.main()
