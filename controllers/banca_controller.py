from datetime import date

from models import *
from repository.postgresql import DatabasePostgreSQL
from services.csv_service import ServizioCSV


class BancaController:

    def __init__(self, database: DatabasePostgreSQL, csv: ServizioCSV):
        self.database = database
        self.csv = csv
        filiali = database.filiali()
        self.codice_filiale = filiali[0]['codice_filiale'] if len(filiali) == 1 else None

    def _codice(self):
        if not self.codice_filiale: raise OperazioneNonConsentitaError('Selezionare una filiale dal menu Filiali')
        return self.codice_filiale

    def filiali(self):
        return self.database.filiali()

    def seleziona_filiale(self, codice):
        codice = codice.strip().upper()
        filiale = self.database.filiale(codice)
        if not filiale: raise OperazioneNonConsentitaError(f'Filiale {codice} non trovata nel database')
        self.codice_filiale = codice
        return filiale

    def filiale(self):
        filiale = self.database.filiale(self._codice())
        if filiale is None: raise OperazioneNonConsentitaError('La filiale selezionata non esiste piu')
        return filiale

    def elenco(self, entita):
        return self.database.lista(entita, self._codice())

    def dettaglio(self, entita, identificativo):
        risultato = self.database.dettaglio(entita, identificativo, self._codice())
        if risultato is None: raise OperazioneNonConsentitaError(f'{entita}: record {identificativo} non trovato')
        return risultato

    def cliente(self, numero_cliente):
        return self.dettaglio('clienti', numero_cliente)

    def dipendente(self, id_dipendente):
        return self.dettaglio('dipendenti', id_dipendente)

    def atm(self, codice_atm):
        return self.dettaglio('atm', codice_atm.strip().upper())

    def conto(self, id_conto):
        return self.dettaglio('conti', id_conto)

    def finanziamento(self, id_operazione):
        return self.dettaglio('finanziamenti', id_operazione)

    def _oggetto_cliente(self, riga):
        return Cliente(riga['nome'], riga['cognome'], riga['codice_fiscale'], riga['recapito'], riga['numero_cliente'], riga['email'], riga['data_nascita'], riga['citta'], riga['data_registrazione'], SegmentoCliente(riga['segmento']))

    def _oggetto_dipendente(self, riga):
        argomenti = [riga['nome'], riga['cognome'], riga['codice_fiscale'], riga['recapito'], riga['id_dipendente'], riga['data_assunzione']]
        match riga['ruolo']:
            case 'Gestore': return Gestore(*argomenti)
            case 'AddettoAllaSicurezza': return AddettoAllaSicurezza(*argomenti)
            case 'Specialista': return Specialista(*argomenti, Specializzazione(riga['specializzazione']))
            case 'Direttore': return Direttore(*argomenti, Specializzazione(riga['specializzazione']), riga['liv_autorizzazione'])
            case _: raise ValueError('Ruolo dipendente non valido nel database')

    def _oggetto_conto(self, id_conto):
        riga = self.conto(id_conto)
        cliente = self._oggetto_cliente(self.cliente(riga['numero_cliente']))
        conto = ContoCorrente(riga['id_conto'], riga['iban'], cliente, TipoConto(riga['tipo_conto']), riga['data_apertura'], StatoConto(riga['stato']))
        conto._imposta_saldo(float(riga['saldo']))
        return conto

    def crea_filiale(self, dati, direttore_dati, atm_dati):
        direttore = Direttore(direttore_dati['nome'], direttore_dati['cognome'], direttore_dati['codice_fiscale'], direttore_dati['recapito'], 1, direttore_dati['data_assunzione'], Specializzazione.INVESTIMENTI, direttore_dati['liv_autorizzazione'])
        codice = dati['codice_filiale'].strip().upper()
        atm = ATM(atm_dati['codice_atm'], codice, StatoATM.ATTIVO, atm_dati['data_installazione'])
        filiale = Filiale(codice, dati['nome'], dati['citta'], dati['provincia'], dati['regione'], dati['data_apertura'], direttore, atm)
        risultato = self.database.nuova_filiale(filiale, direttore, atm)
        self.codice_filiale = codice
        return risultato

    def modifica_filiale(self, modifiche):
        attuale = self.filiale()
        direttore = self._oggetto_dipendente(self.dipendente(attuale['direttore_id']))
        dati = {campo: modifiche.get(campo, attuale[campo]) for campo in ('nome','citta','provincia','regione')}
        validata = Filiale(attuale['codice_filiale'], dati['nome'], dati['citta'], dati['provincia'], dati['regione'], attuale['data_apertura'], direttore)
        valori = {campo: getattr(validata, campo) for campo in dati}
        return self.database.modifica('filiale', self._codice(), self._codice(), valori)

    def crea_cliente(self, dati):
        cliente = Cliente(dati['nome'], dati['cognome'], dati['codice_fiscale'], dati['recapito'], 1, dati['email'], dati['data_nascita'], dati['citta'], date.today(), dati['segmento'])
        return self.database.nuovo_cliente(self._codice(), cliente)

    def modifica_cliente(self, numero_cliente, modifiche):
        cliente = self._oggetto_cliente(self.cliente(numero_cliente))
        for campo, valore in modifiche.items(): setattr(cliente, campo, valore)
        valori = {campo: getattr(cliente, campo).value if campo == 'segmento' else getattr(cliente, campo) for campo in modifiche}
        return self.database.modifica('clienti', numero_cliente, self._codice(), valori)

    def crea_dipendente(self, ruolo, dati):
        args = [dati['nome'], dati['cognome'], dati['codice_fiscale'], dati['recapito'], 1, dati['data_assunzione']]
        match ruolo:
            case 'Gestore': dipendente = Gestore(*args)
            case 'Specialista': dipendente = Specialista(*args, dati['specializzazione'])
            case 'AddettoAllaSicurezza': dipendente = AddettoAllaSicurezza(*args)
            case _: raise ValueError('Ruolo non valido')
        return self.database.nuovo_dipendente(self._codice(), dipendente, ruolo)

    def modifica_dipendente(self, id_dipendente, modifiche):
        dipendente = self._oggetto_dipendente(self.dipendente(id_dipendente))
        for campo, valore in modifiche.items():
            if campo == 'specializzazione' and not isinstance(dipendente, Specialista): raise ValueError('Ruolo senza specializzazione')
            if campo == 'liv_autorizzazione' and not isinstance(dipendente, Direttore): raise ValueError('Solo il direttore ha un livello di autorizzazione')
            if campo == 'liv_autorizzazione' and (type(valore) is not int or valore <= 0): raise ValueError('Livello autorizzazione non valido')
            setattr(dipendente, campo, valore)
        valori = {campo: getattr(dipendente, campo).value if campo == 'specializzazione' else getattr(dipendente, campo) for campo in modifiche}
        return self.database.modifica('dipendenti', id_dipendente, self._codice(), valori)

    def crea_atm(self, codice_atm, data_installazione):
        return self.database.nuovo_atm(ATM(codice_atm, self._codice(), StatoATM.ATTIVO, data_installazione))

    def modifica_atm(self, codice_atm, stato):
        riga = self.atm(codice_atm)
        atm = ATM(riga['codice_atm'], riga['codice_filiale'], StatoATM(riga['stato']), riga['data_installazione'])
        if not isinstance(stato, StatoATM): raise TypeError('Stato ATM non valido')
        atm.stato = stato
        return self.database.modifica('atm', atm.codice_atm, self._codice(), {'stato': atm.stato.value})

    def apri_conto(self, numero_cliente, iban, tipo_conto):
        cliente = self._oggetto_cliente(self.cliente(numero_cliente))
        conto = ContoCorrente(1, iban, cliente, tipo_conto, date.today())
        return self.database.nuovo_conto(self._codice(), conto)

    def modifica_conto(self, id_conto, iban, tipo_conto, stato):
        conto = self._oggetto_conto(id_conto)
        conto.iban = iban
        conto.tipo_conto = tipo_conto
        conto.stato = stato
        return self.database.modifica('conti', id_conto, self._codice(), {'iban': conto.iban, 'tipo_conto': conto.tipo_conto.value, 'stato': conto.stato.value})

    def versamento(self, id_conto, importo, tipo, causale):
        conto = self._oggetto_conto(id_conto)
        movimento = Versamento(1, date.today(), importo, conto, tipo, CanaleOperazione.FILIALE, causale)
        dati = {'id_conto': id_conto, 'tipo': 'Versamento', 'data_operazione': movimento.data_operazione, 'importo': movimento.importo, 'canale': movimento.canale.value, 'causale': movimento.causale, 'tipo_versamento': movimento.tipo_versamento.value}
        return self.database.nuovo_movimento(self._codice(), dati)

    def prelievo_atm(self, codice_atm, id_conto, importo):
        riga = self.atm(codice_atm)
        atm = ATM(riga['codice_atm'], riga['codice_filiale'], StatoATM(riga['stato']), riga['data_installazione'])
        atm.verifica_operativo()
        conto = self._oggetto_conto(id_conto)
        movimento = Prelievo(1, date.today(), importo, conto, CanaleOperazione.ATM, f'Prelievo ATM {atm.codice_atm}')
        dati = {'id_conto': id_conto, 'tipo': 'Prelievo', 'data_operazione': movimento.data_operazione, 'importo': movimento.importo, 'canale': movimento.canale.value, 'causale': movimento.causale, 'tipo_versamento': None}
        return self.database.nuovo_movimento(self._codice(), dati, atm.codice_atm)

    def crea_finanziamento(self, tipo, id_conto, importo, durata_mesi, tasso, finalita):
        conto = self._oggetto_conto(id_conto)
        if tipo == 'Prestito': fin = Prestito(1, date.today(), importo, conto, durata_mesi, tasso, finalita)
        elif tipo == 'Mutuo': fin = Mutuo(1, date.today(), importo, conto, durata_mesi, tasso, finalita)
        else: raise ValueError('Tipo finanziamento non valido')
        dati = {'id_conto': id_conto, 'numero_cliente': conto.intestatario.numero_cliente, 'tipo': tipo, 'data_operazione': fin.data_operazione, 'importo': fin.importo, 'durata_mesi': fin.durata_mesi, 'tasso': fin.tasso, 'stato': 'Richiesta', 'finalita': fin.finalita, 'eseguito': False}
        return self.database.nuovo_finanziamento(self._codice(), dati)

    def delibera_finanziamento(self, id_operazione, stato):
        if not isinstance(stato, StatoRichiesta): raise TypeError('Stato finanziamento non valido')
        return self.database.delibera_finanziamento(self._codice(), id_operazione, stato.value)

    def investimento(self, id_conto, importo, prodotto, profilo_rischio, rendimento_atteso):
        conto = self._oggetto_conto(id_conto)
        inv = Investimento(1, date.today(), importo, conto, prodotto, profilo_rischio, rendimento_atteso)
        dati = {'id_conto': id_conto, 'numero_cliente': conto.intestatario.numero_cliente, 'data_operazione': inv.data_operazione, 'importo': inv.importo, 'prodotto': inv.prodotto, 'profilo_rischio': inv.profilo_rischio.value, 'rendimento_atteso': inv.rendimento_atteso, 'stato': inv.stato.value, 'eseguito': True}
        return self.database.nuovo_investimento(self._codice(), dati)

    def movimenti(self, id_conto):
        self.conto(id_conto)
        return self.database.movimenti_conto(self._codice(), id_conto)

    def movimenti_periodo(self, inizio, fine):
        if fine < inizio: raise ValueError('La data finale precede la data iniziale')
        return self.database.movimenti_periodo(self._codice(), inizio, fine)

    def report(self):
        return self.database.report(self._codice())

    def esporta_csv(self, entita, percorso=None):
        righe = self.elenco(entita)
        return self.csv.esporta_entita(entita, righe, self._codice(), percorso)

    def valida_csv(self, entita, riga):
        if entita == 'filiale':
            filiale = self.filiale()
            direttore = self._oggetto_dipendente(self.dipendente(filiale['direttore_id']))
            Filiale(riga['codice_filiale'], riga['nome_filiale'], riga['citta'], riga['provincia'], riga['regione'], riga['data_apertura'], direttore)
        elif entita == 'clienti':
            self._oggetto_cliente(riga)
        elif entita == 'dipendenti':
            self._oggetto_dipendente(riga)
        elif entita == 'atm':
            ATM(riga['codice_atm'], riga['codice_filiale'], StatoATM(riga['stato']), riga['data_installazione'])
        elif entita == 'conti':
            cliente = self._oggetto_cliente(self.cliente(riga['numero_cliente']))
            ContoCorrente(riga['id_conto'], riga['iban'], cliente, TipoConto(riga['tipo_conto']), riga['data_apertura'], StatoConto(riga['stato']))
        elif entita in ('movimenti', 'finanziamenti', 'investimenti'):
            conto = self._oggetto_conto(riga['id_conto'])
            if entita == 'movimenti':
                args = [riga['id_operazione'], riga['data_operazione'], float(riga['importo']), conto]
                if riga['tipo'] == 'Versamento': Versamento(*args, TipoVersamento(riga['tipo_versamento']), CanaleOperazione(riga['canale']), riga['causale'])
                elif riga['tipo'] == 'Prelievo': Prelievo(*args, CanaleOperazione(riga['canale']), riga['causale'])
                else: raise ValueError('Tipo movimento non valido nel CSV')
            elif entita == 'finanziamenti':
                args = [riga['id_operazione'], riga['data_operazione'], float(riga['importo']), conto, riga['durata_mesi'], float(riga['tasso']), riga['finalita']]
                if riga['tipo'] == 'Prestito': Prestito(*args)
                elif riga['tipo'] == 'Mutuo': Mutuo(*args)
                else: raise ValueError('Tipo finanziamento non valido nel CSV')
            else:
                Investimento(riga['id_operazione'], riga['data_operazione'], float(riga['importo']), conto, riga['prodotto'], ProfiloRischio(riga['profilo_rischio']), float(riga['rendimento_atteso']))

    def importa_csv(self, entita, percorso):
        righe = self.csv.importa_entita(entita, percorso)
        for numero, riga in enumerate(righe, 2):
            try: self.valida_csv(entita, riga)
            except (ValueError, TypeError) as errore: raise ValueError(f'CSV {entita}, riga {numero}: {errore}') from errore
        return self.database.importa(entita, righe, self._codice())
