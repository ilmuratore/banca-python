import os
import sys
from pathlib import Path

from controllers.banca_controller import BancaController
from repository.postgresql import DatabasePostgreSQL, DatabaseError
from services.csv_service import ServizioCSV
from views.menu import MenuBanca


def main():
    try:
        database = DatabasePostgreSQL(host=os.getenv('BANCA_DB_HOST', 'localhost'), dbname=os.getenv('BANCA_DB_NAME', 'banca'), user=os.getenv('BANCA_DB_USER', 'postgres'), password=os.getenv('BANCA_DB_PASSWORD', 'postgres'), port=int(os.getenv('BANCA_DB_PORT', '5432')))
        try:
            database.inizializza_schema()
            csv = ServizioCSV(Path(__file__).resolve().parent / 'data' / 'csv')
            controller = BancaController(database, csv)
            MenuBanca(controller).avvia()
        finally:
            database.chiudi()
    except (DatabaseError, ValueError) as errore:
        print(f'Avvio interrotto: {errore}')
        sys.exit(1)


if __name__ == '__main__':
    main()
