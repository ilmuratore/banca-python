import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _compat

import contextlib
import io
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from controllers.banca_controller import BancaController
from repository.postgresql import DatabasePostgreSQL
from services.csv_service import ServizioCSV, StrutturaFileError
from views.menu import MenuBanca
from models import SegmentoCliente, TipoVersamento, OperazioneNonConsentitaError, SaldoInsufficienteError


class FakeDB:
    def __init__(self, filiali=None):
        self._filiali = filiali if filiali is not None else [{'codice_filiale': 'ROMA01', 'nome': 'Filiale Roma', 'citta': 'Roma', 'provincia': 'RM'}]
        self.queries = []
        self.records = {'clienti': {}, 'conti': {}}

    def filiali(self):
        self.queries.append(('filiali',))
        return self._filiali

    def lista(self, entita, codice):
        self.queries.append(('lista', entita, codice))
        return list(self.records.get(entita, {}).values())

    def dettaglio(self, entita, chiave, codice):
        self.queries.append(('dettaglio', entita, chiave, codice))
        return self.records.get(entita, {}).get(chiave)

    def nuovo_cliente(self, codice, cliente):
        cliente.numero_cliente = len(self.records['clienti']) + 1
        self.records['clienti'][cliente.numero_cliente] = {'numero_cliente': cliente.numero_cliente, 'nome': cliente.nome, 'cognome': cliente.cognome, 'codice_fiscale': cliente.codice_fiscale, 'recapito': cliente.recapito, 'email': cliente.email, 'data_nascita': cliente.data_nascita, 'citta': cliente.citta, 'data_registrazione': cliente.data_registrazione, 'segmento': cliente.segmento.value}
        return self.records['clienti'][cliente.numero_cliente]

    def modifica(self, entita, chiave, codice, modifiche):
        self.records[entita][chiave].update(modifiche)
        return self.records[entita][chiave]


class TestController(unittest.TestCase):

    def setUp(self):
        self.db = FakeDB()
        self.controller = BancaController(self.db, None)

    def dati_cliente(self):
        return {'nome': 'Anna', 'cognome': 'Rossi', 'codice_fiscale': 'RSSNNA90A01H501F', 'recapito': '061122334', 'email': 'anna@esempio.it', 'data_nascita': date(1990, 1, 1), 'citta': 'Roma', 'segmento': SegmentoCliente.STANDARD}

    def test_filiale_unica_selezionata_automaticamente(self):
        self.assertEqual(self.controller.codice_filiale, 'ROMA01')

    def test_molte_filiali_non_seleziona_a_caso(self):
        self.assertIsNone(BancaController(FakeDB([{'codice_filiale': 'F1'}, {'codice_filiale': 'F2'}]), None).codice_filiale)

    def test_nessuna_filiale_non_seleziona(self):
        self.assertIsNone(BancaController(FakeDB([]), None).codice_filiale)

    def test_creazione_cliente_persiste_nel_repo(self):
        cliente = self.controller.crea_cliente(self.dati_cliente())
        self.assertEqual(cliente['numero_cliente'], 1)
        self.assertEqual(cliente['nome'], 'Anna')
        self.assertEqual(self.controller.cliente(1)['nome'], 'Anna')

    def test_validazione_model_blocca_errore_prima_del_db(self):
        dati = self.dati_cliente()
        dati['email'] = 'email non valida'
        with self.assertRaises(ValueError): self.controller.crea_cliente(dati)
        self.assertEqual(self.db.records['clienti'], {})

    def test_ricerca_fa_nuova_query_non_usa_cache(self):
        self.controller.crea_cliente(self.dati_cliente())
        self.controller.elenco('clienti')
        self.controller.elenco('clienti')
        self.assertEqual(sum(q[0] == 'lista' for q in self.db.queries), 2)

    def test_modifica_cliente_effettivamente_delegata_db(self):
        self.controller.crea_cliente(self.dati_cliente())
        aggiornato = self.controller.modifica_cliente(1, {'citta': 'Napoli'})
        self.assertEqual(aggiornato['citta'], 'Napoli')
        self.assertEqual(self.db.records['clienti'][1]['citta'], 'Napoli')

    def test_blocca_operazioni_senza_filiale(self):
        ctrl = BancaController(FakeDB([]), None)
        with self.assertRaises(OperazioneNonConsentitaError): ctrl.elenco('clienti')


class TestCSV(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv = ServizioCSV(Path(self.temp.name))

    def test_esportazione_intestazioni_otto_entita(self):
        for entita in ServizioCSV.ENTITA:
            percorso, n = self.csv.esporta_entita(entita, [], 'FIL01')
            self.assertEqual(n, 0)
            self.assertEqual(len(percorso.read_text(encoding='utf-8-sig').split(';')), len(ServizioCSV.COLONNE[entita]))
            self.assertEqual(self.csv.importa_entita(entita, percorso), [])

    def test_roundtrip_csv_clienti(self):
        riga = {'numero_cliente': 1, 'nome': 'Anna', 'cognome': 'Rossi', 'codice_fiscale': 'RSSNNA90A01H501F', 'recapito': '333', 'email': 'anna@esempio.it', 'data_nascita': date(1990,1,1), 'citta': 'Roma', 'data_registrazione': date.today(), 'segmento': 'Standard'}
        percorso, _ = self.csv.esporta_entita('clienti', [riga], 'FIL01')
        righe = self.csv.importa_entita('clienti', percorso)
        self.assertEqual(righe[0]['data_nascita'], riga['data_nascita'])
        self.assertEqual(righe[0]['numero_cliente'], 1)

    def test_decimali_booleani_dati(self):
        riga = {'id_operazione': 23, 'id_conto': 2, 'numero_cliente': 1, 'data_operazione': date.today(), 'importo': Decimal('50.20'), 'prodotto': 'Titoli', 'profilo_rischio': 'Basso', 'rendimento_atteso': Decimal('1.75'), 'stato': 'Attivo', 'eseguito': True}
        percorso, _ = self.csv.esporta_entita('investimenti', [riga], 'FIL01')
        risultato = self.csv.importa_entita('investimenti', percorso)[0]
        self.assertEqual(risultato['importo'], Decimal('50.20'))
        self.assertIs(risultato['eseguito'], True)

    def test_intestazione_non_valida(self):
        percorso = Path(self.temp.name) / 'nonvalido.csv'
        percorso.write_text('nome;codice\nTest;F1\n', encoding='utf-8')
        with self.assertRaises(StrutturaFileError): self.csv.importa_entita('filiale', percorso)

    def test_file_assente(self):
        with self.assertRaises(FileNotFoundError): self.csv.importa_entita('clienti', 'non_esiste_123.csv')


class FakeCursor:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=()):
        self.queries.append((str(query), tuple(params)))


class TestTransazioni(unittest.TestCase):
    def setUp(self):
        self.repo = object.__new__(DatabasePostgreSQL)
        self.cursor = FakeCursor()
        self.repo._prossimo = lambda cur, tipo: 101
        self.repo._conto_bloccato = lambda cur, codice, idconto, richiedi_attivo=True: {'id_conto': idconto, 'saldo': Decimal('400.00'), 'stato': 'Attivo', 'numero_cliente': 33}

    def dati(self, tipo, importo):
        return {'tipo': tipo, 'id_conto': 3, 'data_operazione': date.today(), 'importo': importo, 'canale': 'Filiale', 'causale': 'Test', 'tipo_versamento': 'Contanti' if tipo == 'Versamento' else None}

    def test_versamento_inserisce_movimento_e_aggiorna_saldo(self):
        ident = self.repo._registra_movimento(self.cursor, 'ROMA01', self.dati('Versamento', 30))
        self.assertEqual(ident, 101)
        self.assertIn('insert into movimento', self.cursor.queries[0][0])
        self.assertIn('update conto_corrente set saldo', self.cursor.queries[1][0])
        self.assertEqual(self.cursor.queries[1][1][0], Decimal('30.00'))

    def test_prelievo_diminuisce_saldo(self):
        self.repo._registra_movimento(self.cursor, 'ROMA01', self.dati('Prelievo', 30))
        self.assertEqual(self.cursor.queries[1][1][0], Decimal('-30.00'))

    def test_prelievo_senza_saldo_nessuna_scrittura(self):
        with self.assertRaises(SaldoInsufficienteError): self.repo._registra_movimento(self.cursor, 'ROMA01', self.dati('Prelievo', 500))
        self.assertFalse(self.cursor.queries)

    def test_importi_con_troppi_decimali(self):
        with self.assertRaises(ValueError): self.repo._importo('5.123')

    def test_investimento_registra_addebito(self):
        dati = {'id_conto': 3, 'numero_cliente': 33, 'data_operazione': date.today(), 'importo': 90, 'prodotto': 'BTP', 'profilo_rischio': 'Basso', 'rendimento_atteso': 2, 'stato': 'Attivo', 'eseguito': True}
        self.repo._registra_investimento(self.cursor, 'ROMA01', dati)
        self.assertEqual(self.cursor.queries[-1][1][0], Decimal('90.00'))
        self.assertIn('saldo = saldo -', self.cursor.queries[-1][0])

    def test_finanziamento_approvato_registra_accredito(self):
        dati = {'id_conto': 3, 'numero_cliente': 33, 'tipo': 'Prestito', 'data_operazione': date.today(), 'importo': 100, 'durata_mesi': 12, 'tasso': 3, 'stato': 'Approvata', 'finalita': 'Studio', 'eseguito': True}
        self.repo._registra_finanziamento(self.cursor, 'ROMA01', dati)
        self.assertIn('saldo = saldo +', self.cursor.queries[-1][0])

    def test_finanziamento_incoerente_non_scrive(self):
        dati = {'id_conto': 3, 'numero_cliente': 33, 'tipo': 'Prestito', 'data_operazione': date.today(), 'importo': 100, 'durata_mesi': 12, 'tasso': 3, 'stato': 'Approvata', 'finalita': 'Studio', 'eseguito': False}
        with self.assertRaises(ValueError): self.repo._registra_finanziamento(self.cursor, 'ROMA01', dati)
        self.assertFalse(self.cursor.queries)


class TestView(unittest.TestCase):
    def test_menu_mostra_etichette_e_torna(self):
        view = MenuBanca(type('C', (), {'codice_filiale': 'ROMA01'})())
        buffer = io.StringIO()
        with patch.dict(os.environ, {'BANCA_NO_CLEAR': '1'}), patch('builtins.input', return_value='0'), contextlib.redirect_stdout(buffer):
            view.ciclo('Prova', {'1': ('Nuovo cliente', lambda: 1)})
        self.assertIn('1. Nuovo cliente', buffer.getvalue())
        self.assertNotIn('function', buffer.getvalue())


if __name__ == '__main__': unittest.main()
