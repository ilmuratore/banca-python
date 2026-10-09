import copy
import sys
import tempfile
import types
import unittest
from datetime import date

try:
    import psycopg
except ImportError:
    fake_psycopg = types.ModuleType("psycopg")
    fake_psycopg.Error = type("Error", (Exception,), {})
    fake_psycopg.sql = types.SimpleNamespace(SQL=lambda s: s, Identifier=lambda s: s, Placeholder=lambda: "%s")
    fake_rows = types.ModuleType("psycopg.rows")
    fake_rows.dict_row = None
    sys.modules["psycopg"] = fake_psycopg
    sys.modules["psycopg.rows"] = fake_rows

from models import *
from controllers.banca_controller import BancaController
from services.csv_service import ParserCSV


class FakeDatabase:
    def __init__(self):
        self.dati = None
        self.letture = 0

    def esiste_filiale(self, codice): return self.dati is not None and self.dati.codice_filiale == codice

    def elenco_filiali(self):
        if self.dati is None: return []
        return [{"codice_filiale": self.dati.codice_filiale, "nome": self.dati.nome, "citta": self.dati.citta, "provincia": self.dati.provincia}]

    def carica_filiale(self, codice):
        self.letture += 1
        return copy.deepcopy(self.dati)

    def prossimo_id_dipendente(self): return 1 + max(([d.id_dipendente for d in self.dati.dipendenti] if self.dati else []) + [0])
    def prossimo_numero_cliente(self): return 1 + max(([d.numero_cliente for d in self.dati.clienti] if self.dati else []) + [0])
    def prossimo_id_conto(self): return 1 + max(([c.id_conto for cl in self.dati.clienti for c in cl.conti] if self.dati else []) + [0])
    def prossimo_id_operazione(self): return 1 + max([m.id_operazione for cl in self.dati.clienti for c in cl.conti for m in c.movimenti] + [f.id_operazione for f in self.dati.finanziamenti] + [i.id_operazione for i in self.dati.investimenti] + [0])

    def inserisci_filiale(self, filiale): self.dati = copy.deepcopy(filiale)
    def aggiorna_filiale(self, filiale):
        for k in ("nome", "citta", "provincia", "regione"): setattr(self.dati, k, getattr(filiale, k))

    def inserisci_cliente(self, codice_filiale, cliente): self.dati.aggiungi_cliente(copy.deepcopy(cliente))

    def aggiorna_cliente(self, cliente):
        for i, c in enumerate(self.dati.clienti):
            if c.numero_cliente == cliente.numero_cliente:
                # Evita perdere i conti caricati dal DB.
                conti = c.conti
                self.dati.clienti[i] = copy.deepcopy(cliente)
                self.dati.clienti[i].conti = conti
                return

    def inserisci_dipendente(self, codice, dipendente): self.dati.aggiungi_dipendente(copy.deepcopy(dipendente))

    def aggiorna_dipendente(self, dipendente):
        for i, d in enumerate(self.dati.dipendenti):
            if d.id_dipendente == dipendente.id_dipendente:
                self.dati.dipendenti[i] = copy.deepcopy(dipendente)
                if self.dati.direttore.id_dipendente == dipendente.id_dipendente: self.dati.direttore = self.dati.dipendenti[i]
                return

    def inserisci_atm(self, atm): self.dati.aggiungi_atm(copy.deepcopy(atm))

    def aggiorna_atm(self, atm):
        for a in self.dati.atm:
            if a.codice_atm == atm.codice_atm: a.stato = atm.stato

    def inserisci_conto(self, conto):
        cliente = next(c for c in self.dati.clienti if c.numero_cliente == conto.intestatario.numero_cliente)
        conto_copy = copy.deepcopy(conto)
        conto_copy.intestatario = cliente
        cliente.conti.append(conto_copy)

    def aggiorna_conto(self, conto):
        for cl in self.dati.clienti:
            for c in cl.conti:
                if c.id_conto == conto.id_conto:
                    c.iban, c.tipo_conto, c.stato = conto.iban, conto.tipo_conto, conto.stato
                    return


class TestController(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = FakeDatabase()
        self.controller = BancaController(self.db, ParserCSV(self.tmp.name))
        d = {"codice_filiale": "F1", "nome": "Filiale", "citta": "Roma", "provincia": "RM", "regione": "Lazio", "data_apertura": date(2020, 1, 1)}
        direttore = {"nome": "Mario", "cognome": "Rossi", "codice_fiscale": "RSSMRA80A01H501U", "recapito": "333", "data_assunzione": date(2020, 1, 1), "liv_autorizzazione": 3}
        self.controller.crea_filiale(d, direttore, {"codice_atm": "ATM1", "data_installazione": date.today()})

    def tearDown(self): self.tmp.cleanup()

    def test_cliente_scritto_su_db_e_letto(self):
        cliente = self.controller.crea_cliente({"nome": "Luigi", "cognome": "Bianchi", "codice_fiscale": "BNCLCU80A01H501X", "recapito": "333", "email": "luigi@example.it", "data_nascita": date(1980, 1, 1), "citta": "Roma", "segmento": SegmentoCliente.STANDARD})
        self.assertEqual(cliente.numero_cliente, 1)
        self.assertEqual(self.db.dati.clienti[0].nome, "Luigi")
        self.assertEqual(self.controller.cliente(1).nome, "Luigi")
        n = self.db.letture
        self.controller.modifica_cliente(1, {"citta": "Milano"})
        self.assertEqual(self.db.dati.clienti[0].citta, "Milano")
        self.assertGreater(self.db.letture, n)

    def test_apertura_conto(self):
        cliente = self.controller.crea_cliente({"nome": "Luigi", "cognome": "Bianchi", "codice_fiscale": "BNCLCU80A01H501X", "recapito": "333", "email": "luigi@example.it", "data_nascita": date(1980, 1, 1), "citta": "Roma", "segmento": SegmentoCliente.STANDARD})
        conto = self.controller.apri_conto(cliente.numero_cliente, "IT60X0542811101000000123456", TipoConto.CORRENTE)
        self.assertEqual(conto.id_conto, 1)
        self.assertEqual(len(self.db.dati.clienti[0].conti), 1)

    def test_export_freschi_da_db(self):
        percorso, n = self.controller.esporta_csv("filiale")
        self.assertEqual(n, 1)
        self.assertEqual(len(self.controller.csv.importa_entita("filiale", percorso)), 1)
        self.assertGreater(self.db.letture, 0)


if __name__ == "__main__": unittest.main()
