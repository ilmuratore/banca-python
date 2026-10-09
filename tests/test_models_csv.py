import tempfile
import unittest
from datetime import date
from pathlib import Path

from models import *
from services.csv_service import ParserCSV
from services.mapper import MapperBanca, StrutturaFileError


def esempio():
    direttore = Direttore("Mario", "Rossi", "RSSMRA80A01H501U", "333", 1, date(2020, 1, 1), Specializzazione.INVESTIMENTI, 3)
    filiale = Filiale("F1", "Filiale 1", "Roma", "RM", "Lazio", date(2020, 1, 1), direttore, ATM("ATM1", "F1"))
    cliente = Cliente("Luca", "Bianchi", "BNCLCU80A01H501X", "333", 1, "luca@example.it", date(1980, 1, 1), "Roma", date.today(), SegmentoCliente.STANDARD)
    filiale.aggiungi_cliente(cliente)
    conto = direttore.apri_conto(1, "IT60X0542811101000000123456", cliente, TipoConto.CORRENTE, date.today())
    direttore.versa(1, conto, 1000, TipoVersamento.CONTANTI)
    prestito = direttore.richiedi_prestito(2, date.today(), 500, conto, 12, 3, "Spese")
    filiale.aggiungi_finanziamento(prestito)
    return filiale


class TestCSV(unittest.TestCase):

    def test_tutti_gli_otto_csv_indipendenti(self):
        with tempfile.TemporaryDirectory() as cartella:
            filiale = esempio()
            parser = ParserCSV(cartella)
            for entita in parser.ENTITA:
                percorso, totale = parser.esporta_entita(filiale, entita)
                self.assertEqual(len(parser.importa_entita(entita, percorso)), totale)
                self.assertTrue(percorso.is_file())

    def test_ricostruzione_grafo(self):
        filiale = esempio()
        serial = MapperBanca()
        dati = {
            "filiale": serial.prepara_filiale(filiale), "dipendenti": serial.prepara_dipendenti(filiale.dipendenti),
            "atm": serial.prepara_atm(filiale.atm), "clienti": serial.prepara_clienti(filiale.clienti),
            "conti": serial.prepara_conti(filiale.clienti), "movimenti": serial.prepara_movimenti(filiale.clienti),
            "finanziamenti": serial.prepara_finanziamenti(filiale.finanziamenti), "investimenti": serial.prepara_investimenti(filiale.investimenti)
        }
        nuovo = serial.ricostruisci(dati)
        self.assertEqual(nuovo.clienti[0].conti[0].saldo, 1000)
        self.assertEqual(len(nuovo.clienti[0].conti[0].movimenti), 1)
        self.assertEqual(len(nuovo.finanziamenti), 1)
        self.assertEqual(nuovo.codice_filiale, "F1")

    def test_csv_colonne_errate(self):
        with tempfile.TemporaryDirectory() as directory:
            csv = Path(directory) / "clienti.csv"
            csv.write_text("cliente;nome\n1;Mario\n", encoding="utf-8")
            with self.assertRaises(StrutturaFileError): ParserCSV(directory).importa_entita("clienti", csv)

    def test_prelevare_piu_del_saldo_bloccato(self):
        filiale = esempio()
        conto = filiale.clienti[0].conti[0]
        with self.assertRaises(SaldoInsufficienteError): filiale.direttore.preleva(3, conto, 1200)
        self.assertEqual(conto.saldo, 1000)


if __name__ == "__main__": unittest.main()
