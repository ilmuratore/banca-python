import os
from datetime import date, datetime
from decimal import Decimal

from models import *
from services.csv_service import ServizioCSV


class MenuBanca:

    def __init__(self, controller):
        self.controller = controller

    def pulisci(self):
        if os.getenv('BANCA_NO_CLEAR') == '1': return
        print('\033[3J\033[2J\033[H', end='', flush=True)

    def schermata(self, titolo):
        self.pulisci()
        print(f'\n==============================\n{titolo.upper()}\n==============================')
        print(f'Filiale attiva: {self.controller.codice_filiale or "nessuna"}\n')

    def pausa(self):
        input('\nPremi INVIO per continuare...')

    def scelta(self, titolo, voci):
        self.schermata(titolo)
        for n, voce in enumerate(voci, 1): print(f'{n}. {voce}')
        print('0. Indietro')
        return input('\nScelta: ').strip()

    def ciclo(self, titolo, azioni):
        while True:
            scelta = self.scelta(titolo, tuple(valore[0] for valore in azioni.values()))
            if scelta == '0': return
            try:
                if scelta not in azioni: raise ValueError('Scelta non valida')
                self.schermata(azioni[scelta][0])
                azioni[scelta][1]()
            except Exception as errore:
                print(f'\nERRORE ({type(errore).__name__}): {errore}')
            self.pausa()

    def testo(self, nome, attuale=None):
        if attuale is None: return input(f'{nome}: ').strip()
        valore = input(f'{nome} [{attuale}]: ').strip()
        return valore if valore else attuale

    def intero(self, nome):
        return int(self.testo(nome))

    def importo(self, nome):
        return float(self.testo(nome).replace(',', '.'))

    def data(self, nome, predefinita=None):
        suggerimento = f' [INVIO: {predefinita.strftime("%d/%m/%Y")}]' if predefinita else ''
        valore = input(f'{nome} [gg/mm/aaaa]{suggerimento}: ').strip()
        if not valore and predefinita is not None: return predefinita
        return datetime.strptime(valore, '%d/%m/%Y').date()

    def enum(self, tipo, attuale=None):
        valori = list(tipo)
        for n, valore in enumerate(valori, 1): print(f'{n}. {valore.value}')
        testo = input(f'Scelta{(" [INVIO: " + attuale.value + "]") if attuale else ""}: ').strip()
        if not testo and attuale is not None: return attuale
        scelta = int(testo)
        if not 1 <= scelta <= len(valori): raise ValueError('Valore non valido')
        return valori[scelta - 1]

    def persona(self, attuale=None):
        return {campo: self.testo(campo.replace('_', ' ').title(), attuale[campo] if attuale else None) for campo in ('nome', 'cognome', 'codice_fiscale', 'recapito')}

    def formato(self, valore):
        if isinstance(valore, date): return valore.strftime('%d/%m/%Y')
        if isinstance(valore, Decimal): return f'{valore:.2f}'
        if isinstance(valore, bool): return 'Si' if valore else 'No'
        return '' if valore is None else str(valore)

    def mostra(self, riga):
        if not riga:
            print('Nessun record trovato')
            return
        print('\n' + '-' * 45)
        for campo, valore in riga.items(): print(f'{campo.replace("_", " ").title():24} {self.formato(valore)}')

    def elenco(self, entita, righe=None):
        righe = self.controller.elenco(entita) if righe is None else righe
        print(f'\n{entita.upper()} - {len(righe)} record')
        for riga in righe: self.mostra(riga)

    def cerca(self, entita, descrizione):
        valore = self.testo(descrizione)
        if entita not in ('filiale', 'atm'): valore = int(valore)
        self.mostra(self.controller.dettaglio(entita, valore))

    def nuova_filiale(self):
        dati = {'codice_filiale': self.testo('Codice filiale'), 'nome': self.testo('Nome filiale'), 'citta': self.testo('Citta'), 'provincia': self.testo('Provincia'), 'regione': self.testo('Regione'), 'data_apertura': self.data('Data apertura')}
        print('\nDIRETTORE INIZIALE')
        direttore = self.persona()
        direttore['data_assunzione'] = self.data('Data assunzione', date.today())
        direttore['liv_autorizzazione'] = self.intero('Livello autorizzazione')
        print('\nATM INIZIALE')
        atm = {'codice_atm': self.testo('Codice ATM'), 'data_installazione': self.data('Data installazione', date.today())}
        self.mostra(self.controller.crea_filiale(dati, direttore, atm))

    def scegli_filiale(self):
        elenco = self.controller.filiali()
        self.elenco('filiale', elenco)
        self.mostra(self.controller.seleziona_filiale(self.testo('Codice filiale')))

    def modifica_filiale(self):
        riga = self.controller.filiale()
        self.mostra(riga)
        modifiche = {campo: self.testo(campo.title(), riga[campo]) for campo in ('nome', 'citta', 'provincia', 'regione')}
        self.mostra(self.controller.modifica_filiale(modifiche))

    def menu_filiale(self):
        self.ciclo('Filiali', {'1': ('Nuova filiale', self.nuova_filiale), '2': ('Seleziona filiale', self.scegli_filiale), '3': ('Riepilogo filiale', lambda: self.mostra(self.controller.filiale())), '4': ('Modifica filiale', self.modifica_filiale), '5': ('Elenco filiali', lambda: self.elenco('filiale', self.controller.filiali()))})

    def nuovo_cliente(self):
        dati = self.persona()
        dati['email'] = self.testo('Email')
        dati['data_nascita'] = self.data('Data nascita')
        dati['citta'] = self.testo('Citta')
        dati['segmento'] = self.enum(SegmentoCliente)
        self.mostra(self.controller.crea_cliente(dati))

    def modifica_cliente(self):
        chiave = self.intero('Numero cliente')
        riga = self.controller.cliente(chiave)
        self.mostra(riga)
        modifiche = self.persona(riga)
        modifiche['email'] = self.testo('Email', riga['email'])
        modifiche['citta'] = self.testo('Citta', riga['citta'])
        modifiche['segmento'] = self.enum(SegmentoCliente, SegmentoCliente(riga['segmento']))
        self.mostra(self.controller.modifica_cliente(chiave, modifiche))

    def menu_clienti(self):
        self.ciclo('Clienti', {'1': ('Inserisci cliente', self.nuovo_cliente), '2': ('Modifica cliente', self.modifica_cliente), '3': ('Elenco clienti', lambda: self.elenco('clienti')), '4': ('Cerca cliente', lambda: self.cerca('clienti', 'Numero cliente'))})

    def nuovo_dipendente(self):
        print('1. Gestore\n2. Specialista\n3. Addetto alla sicurezza')
        ruolo = {'1': 'Gestore', '2': 'Specialista', '3': 'AddettoAllaSicurezza'}.get(self.testo('Ruolo'))
        if ruolo is None: raise ValueError('Ruolo non valido')
        dati = self.persona()
        dati['data_assunzione'] = self.data('Data assunzione', date.today())
        if ruolo == 'Specialista': dati['specializzazione'] = self.enum(Specializzazione)
        self.mostra(self.controller.crea_dipendente(ruolo, dati))

    def modifica_dipendente(self):
        chiave = self.intero('ID dipendente')
        riga = self.controller.dipendente(chiave)
        self.mostra(riga)

        modifiche = self.persona(riga)
        modifiche['data_assunzione'] = self.data('Data assunzione', riga['data_assunzione'])

        print('\nFILIALI DISPONIBILI')
        self.elenco('filiale', self.controller.filiali())
        modifiche['codice_filiale'] = self.testo('Codice filiale', riga['codice_filiale']).upper()

        ruoli = ('Gestore', 'Specialista', 'Direttore', 'AddettoAllaSicurezza')
        print('\nRUOLI DISPONIBILI')
        for numero, ruolo in enumerate(ruoli, 1): print(f'{numero}. {ruolo}')
        scelta = self.testo('Nuovo ruolo (1-4; INVIO mantiene)')
        if scelta:
            if not scelta.isdigit() or not 1 <= int(scelta) <= len(ruoli): raise ValueError('Ruolo non valido')
            modifiche['ruolo'] = ruoli[int(scelta) - 1]
        else:
            modifiche['ruolo'] = riga['ruolo']

        if modifiche['ruolo'] in ('Specialista', 'Direttore'):
            attuale = Specializzazione(riga['specializzazione']) if riga['specializzazione'] else None
            modifiche['specializzazione'] = self.enum(Specializzazione, attuale)
        else:
            modifiche['specializzazione'] = None

        if modifiche['ruolo'] == 'Direttore':
            livello = riga['liv_autorizzazione']
            modifiche['liv_autorizzazione'] = int(self.testo('Livello autorizzazione', livello)) if livello is not None else self.intero('Livello autorizzazione')
        else:
            modifiche['liv_autorizzazione'] = None

        if riga['ruolo'] == 'Direttore' and (modifiche['ruolo'] != 'Direttore' or modifiche['codice_filiale'] != riga['codice_filiale']):
            print('\nATTENZIONE: se dirige una filiale, verra rimossa la precedente assegnazione come direttore.')

        self.mostra(self.controller.modifica_dipendente(chiave, modifiche))

    def nuovo_atm(self):
        self.mostra(self.controller.crea_atm(self.testo('Codice ATM'), self.data('Data installazione', date.today())))

    def modifica_atm(self):
        codice = self.testo('Codice ATM')
        atm = self.controller.atm(codice)
        self.mostra(atm)
        self.mostra(self.controller.modifica_atm(codice, self.enum(StatoATM, StatoATM(atm['stato']))))

    def menu_personale(self):
        self.ciclo('Dipendenti e ATM', {'1': ('Inserisci dipendente', self.nuovo_dipendente), '2': ('Modifica dipendente', self.modifica_dipendente), '3': ('Aggiungi ATM', self.nuovo_atm), '4': ('Modifica stato ATM', self.modifica_atm), '5': ('Elenco dipendenti', lambda: self.elenco('dipendenti')), '6': ('Elenco ATM', lambda: self.elenco('atm')), '7': ('Cerca dipendente', lambda: self.cerca('dipendenti', 'ID dipendente'))})

    def nuovo_conto(self):
        numero = self.intero('Numero cliente')
        iban = self.testo('IBAN')
        tipo = self.enum(TipoConto)
        self.mostra(self.controller.apri_conto(numero, iban, tipo))

    def modifica_conto(self):
        identificativo = self.intero('ID conto')
        conto = self.controller.conto(identificativo)
        self.mostra(conto)
        iban = self.testo('IBAN', conto['iban'])
        tipo = self.enum(TipoConto, TipoConto(conto['tipo_conto']))
        stato = self.enum(StatoConto, StatoConto(conto['stato']))
        self.mostra(self.controller.modifica_conto(identificativo, iban, tipo, stato))

    def menu_conti(self):
        self.ciclo('Conti correnti', {'1': ('Apri conto', self.nuovo_conto), '2': ('Modifica conto', self.modifica_conto), '3': ('Elenco conti', lambda: self.elenco('conti')), '4': ('Cerca conto', lambda: self.cerca('conti', 'ID conto'))})

    def nuovo_versamento(self, tipo):
        riga, saldo = self.controller.versamento(self.intero('ID conto'), self.importo('Importo'), tipo, self.testo('Causale [Versamento]') or 'Versamento')
        self.mostra(riga)
        print(f'\nSALDO DB AGGIORNATO: {saldo:.2f} euro')

    def nuovo_prelievo(self):
        atm_disponibili = self.controller.elenco('atm')
        if not atm_disponibili:
            print('Nessun ATM registrato nella filiale selezionata')
            return
        print('\nATM DELLA FILIALE')
        print(f'{"CODICE ATM":<20} {"STATO":<16} DATA INSTALLAZIONE')
        print('-' * 60)
        for riga_atm in atm_disponibili:
            print(f'{riga_atm["codice_atm"]:<20} {riga_atm["stato"]:<16} {self.formato(riga_atm["data_installazione"])}')
        attivi = {riga_atm['codice_atm'].upper() for riga_atm in atm_disponibili if riga_atm['stato'] == 'Attivo'}
        if not attivi:
            print('Nessun ATM attivo disponibile per il prelievo')
            return
        atm = self.testo('Codice ATM').upper()
        if atm not in attivi: raise ValueError('Selezionare il codice di un ATM attivo presente nella filiale')
        conto = self.intero('ID conto')
        riga, saldo = self.controller.prelievo_atm(atm, conto, self.importo('Importo'))
        self.mostra(riga)
        print(f'\nSALDO DB AGGIORNATO: {saldo:.2f} euro')

    def mostra_movimenti(self):
        self.elenco('movimenti', self.controller.movimenti(self.intero('ID conto')))

    def menu_operazioni(self):
        self.ciclo('Operazioni', {'1': ('Versamento contanti', lambda: self.nuovo_versamento(TipoVersamento.CONTANTI)), '2': ('Versamento assegno', lambda: self.nuovo_versamento(TipoVersamento.ASSEGNO)), '3': ('Prelievo ATM', self.nuovo_prelievo), '4': ('Movimenti di un conto', self.mostra_movimenti)})

    def nuovo_finanziamento(self, tipo):
        conto = self.intero('ID conto')
        importo = self.importo('Importo')
        mesi = self.intero('Durata mesi')
        tasso = self.importo('Tasso (%)')
        self.mostra(self.controller.crea_finanziamento(tipo, conto, importo, mesi, tasso, self.testo('Finalita')))

    def delibera(self, stato):
        self.elenco('finanziamenti', [f for f in self.controller.elenco('finanziamenti') if f['stato'] == 'Richiesta'])
        self.mostra(self.controller.delibera_finanziamento(self.intero('ID operazione'), stato))

    def nuovo_investimento(self):
        conto = self.intero('ID conto')
        importo = self.importo('Importo')
        prodotto = self.testo('Prodotto')
        profilo = self.enum(ProfiloRischio)
        self.mostra(self.controller.investimento(conto, importo, prodotto, profilo, self.importo('Rendimento atteso (%)')))

    def menu_finanziamenti(self):
        self.ciclo('Finanziamenti e investimenti', {'1': ('Richiesta prestito', lambda: self.nuovo_finanziamento('Prestito')), '2': ('Richiesta mutuo', lambda: self.nuovo_finanziamento('Mutuo')), '3': ('Approva finanziamento', lambda: self.delibera(StatoRichiesta.APPROVATA)), '4': ('Rifiuta finanziamento', lambda: self.delibera(StatoRichiesta.RIFIUTATA)), '5': ('Nuovo investimento', self.nuovo_investimento), '6': ('Elenco finanziamenti', lambda: self.elenco('finanziamenti')), '7': ('Elenco investimenti', lambda: self.elenco('investimenti'))})

    def cerca_periodo(self):
        inizio, fine = self.data('Dal'), self.data('Al')
        self.elenco('movimenti', self.controller.movimenti_periodo(inizio, fine))

    def report(self):
        for categoria, dati in self.controller.report().items():
            print(f'\n--- {categoria.upper()} ---')
            if isinstance(dati, dict): self.mostra(dati)
            else: self.elenco(categoria, dati)

    def menu_report(self):
        self.ciclo('Ricerche e report', {'1': ('Cerca cliente', lambda: self.cerca('clienti', 'Numero cliente')), '2': ('Cerca dipendente', lambda: self.cerca('dipendenti', 'ID dipendente')), '3': ('Cerca conto', lambda: self.cerca('conti', 'ID conto')), '4': ('Cerca finanziamento', lambda: self.cerca('finanziamenti', 'ID operazione')), '5': ('Movimenti per periodo', self.cerca_periodo), '6': ('Report SQL', self.report)})

    def scegli_entita(self):
        for n, entita in enumerate(ServizioCSV.ENTITA, 1): print(f'{n}. {entita}')
        n = self.intero('Entita')
        if n not in range(1, len(ServizioCSV.ENTITA) + 1): raise ValueError('Entita non valida')
        return ServizioCSV.ENTITA[n - 1]

    def esporta_csv(self):
        entita = self.scegli_entita()
        percorso, quanti = self.controller.esporta_csv(entita)
        print(f'Esportati {quanti} record dal DB: {percorso}')

    def importa_csv(self):
        entita = self.scegli_entita()
        percorso = self.controller.csv.percorso(entita, self.controller._codice())
        print(f'\nATTENZIONE: i dati saranno scritti subito nel DB. Le modifiche CSV non sono una sincronizzazione automatica.')
        file = self.testo('Percorso CSV', str(percorso))
        if self.testo('Confermi importazione? (SI/NO)').upper() != 'SI':
            print('Importazione annullata')
            return
        quanti = self.controller.importa_csv(entita, file)
        print(f'Importazione terminata: {quanti} record inseriti/aggiornati; nessuna eliminazione automatica')

    def esporta_tutto(self):
        for entita in ServizioCSV.ENTITA:
            percorso, quanti = self.controller.esporta_csv(entita)
            print(f'{entita}: {quanti} record -> {percorso}')

    def menu_csv(self):
        self.ciclo('CSV (solo manuale)', {'1': ('Esporta CSV entita', self.esporta_csv), '2': ('Importa CSV entita', self.importa_csv), '3': ('Esporta tutti i CSV', self.esporta_tutto), '4': ('Mostra tracciati CSV', lambda: [print(f'{entita}: {";".join(ServizioCSV.COLONNE[entita])}') for entita in ServizioCSV.ENTITA])})

    def avvia(self):
        while True:
            self.schermata('BANCA - POSTGRESQL')
            database = self.controller.database.stato_database()
            print(f'Database: {database["database"]} | utente: {database["utente"]}')
            if self.controller.codice_filiale:
                filiale = self.controller.filiale()
                print(f'Filiale: {filiale["nome"]} | Clienti DB: {filiale["totale_clienti"]} | Dipendenti DB: {filiale["totale_dipendenti"]} | ATM DB: {filiale["totale_atm"]}')
            else:
                print(f'Filiali presenti nel DB: {len(self.controller.filiali())} (selezionarne una per operare)')
            print('\n1. Filiali\n2. Clienti\n3. Dipendenti e ATM\n4. Conti correnti\n5. Operazioni\n6. Finanziamenti e investimenti\n7. Ricerche e report\n8. Import / Export CSV\n0. Esci')
            scelta = input('\nScelta: ').strip()
            if scelta == '0': return
            sezioni = {'1': self.menu_filiale, '2': self.menu_clienti, '3': self.menu_personale, '4': self.menu_conti, '5': self.menu_operazioni, '6': self.menu_finanziamenti, '7': self.menu_report, '8': self.menu_csv}
            try:
                if scelta not in sezioni: raise ValueError('Scelta non valida')
                sezioni[scelta]()
            except Exception as errore:
                print(f'\nERRORE ({type(errore).__name__}): {errore}')
                self.pausa()
