import os
from pathlib import Path

from controllers.banca_controller import BancaController
from repository.postgresql import DatabasePostgreSQL
from services.csv_service import ParserCSV
from views.menu import MenuBanca


def main():
    cartella = Path(__file__).resolve().parent
    database = DatabasePostgreSQL(host=os.getenv("BANCA_DB_HOST", "localhost"), dbname=os.getenv("BANCA_DB_NAME", "banca"), user=os.getenv("BANCA_DB_USER", "postgres"), password=os.getenv("BANCA_DB_PASSWORD", "postgres"), port=int(os.getenv("BANCA_DB_PORT", "5432")))
    try:
        database.inizializza_schema()
        csv = ParserCSV(cartella / "data" / "csv")
        controller = BancaController(database, csv)
        MenuBanca(controller).avvia()
    finally:
        database.chiudi()


if __name__ == "__main__":
    main()
