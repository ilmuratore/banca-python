from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from models import OperazioneNonConsentitaError, SaldoInsufficienteError


class DatabaseError(Exception):
    pass


class DatabasePostgreSQL:

    TABELLE = ('filiale', 'dipendente', 'atm', 'cliente', 'conto_corrente', 'movimento', 'finanziamento', 'investimento')
    CHIAVI = {'filiale': 'codice_filiale', 'dipendenti': 'id_dipendente', 'atm': 'codice_atm', 'clienti': 'numero_cliente', 'conti': 'id_conto', 'movimenti': 'id_operazione', 'finanziamenti': 'id_operazione', 'investimenti': 'id_operazione'}
    NOMI_TABELLE = {'filiale': 'filiale', 'dipendenti': 'dipendente', 'atm': 'atm', 'clienti': 'cliente', 'conti': 'conto_corrente', 'movimenti': 'movimento', 'finanziamenti': 'finanziamento', 'investimenti': 'investimento'}
    COLONNE = {
        'filiale': ('codice_filiale', 'nome_filiale', 'citta', 'provincia', 'regione', 'data_apertura', 'direttore_id'),
        'dipendenti': ('id_dipendente', 'ruolo', 'nome', 'cognome', 'codice_fiscale', 'recapito', 'data_assunzione', 'specializzazione', 'liv_autorizzazione'),
        'atm': ('codice_atm', 'codice_filiale', 'stato', 'data_installazione'),
        'clienti': ('numero_cliente', 'nome', 'cognome', 'codice_fiscale', 'recapito', 'email', 'data_nascita', 'citta', 'data_registrazione', 'segmento'),
        'conti': ('id_conto', 'iban', 'numero_cliente', 'tipo_conto', 'data_apertura', 'stato', 'saldo'),
        'movimenti': ('id_operazione', 'id_conto', 'tipo', 'data_operazione', 'importo', 'canale', 'causale', 'tipo_versamento'),
        'finanziamenti': ('id_operazione', 'id_conto', 'numero_cliente', 'tipo', 'data_operazione', 'importo', 'durata_mesi', 'tasso', 'stato', 'finalita', 'eseguito'),
        'investimenti': ('id_operazione', 'id_conto', 'numero_cliente', 'data_operazione', 'importo', 'prodotto', 'profilo_rischio', 'rendimento_atteso', 'stato', 'eseguito')
    }
    MODIFICABILI = {
        'filiale': ('nome', 'citta', 'provincia', 'regione'),
        'clienti': ('nome', 'cognome', 'codice_fiscale', 'recapito', 'email', 'citta', 'segmento'),
        'dipendenti': ('nome', 'cognome', 'codice_fiscale', 'recapito', 'specializzazione', 'liv_autorizzazione'),
        'atm': ('stato',),
        'conti': ('iban', 'tipo_conto', 'stato')
    }
    SEQUENZE = {'clienti': 'banca_id_cliente_seq', 'dipendenti': 'banca_id_dipendente_seq', 'conti': 'banca_id_conto_seq', 'operazioni': 'banca_id_operazione_seq'}

    def __init__(self, host='localhost', dbname='banca', user='postgres', password='postgres', port=5432):
        try:
            self.connessione = psycopg.connect(host=host, dbname=dbname, user=user, password=password, port=port, autocommit=True, row_factory=dict_row, connect_timeout=5)
        except psycopg.Error as errore:
            raise DatabaseError(f'Connessione PostgreSQL fallita: {errore}') from errore

    def chiudi(self):
        if not self.connessione.closed: self.connessione.close()

    def _lettura(self, query, parametri=(), singolo=False):
        try:
            with self.connessione.cursor() as cursore:
                cursore.execute(query, parametri)
                return cursore.fetchone() if singolo else cursore.fetchall()
        except psycopg.Error as errore:
            raise DatabaseError(f'Errore di lettura PostgreSQL: {errore}') from errore

    def _scrittura(self, azione):
        try:
            with self.connessione.transaction():
                with self.connessione.cursor() as cursore:
                    return azione(cursore)
        except psycopg.Error as errore:
            raise DatabaseError(f'Scrittura PostgreSQL annullata: {errore}') from errore

    def inizializza_schema(self):
        def azione(cursore):
            cursore.execute('select tablename from pg_tables where schemaname = current_schema()')
            presenti = {r['tablename'] for r in cursore.fetchall()}
            esistenti = set(self.TABELLE) & presenti
            if 0 < len(esistenti) < len(self.TABELLE):
                raise DatabaseError('Schema parziale: controllare le tabelle in PostgreSQL; nessuna tabella sara eliminata')
            if not esistenti:
                cursore.execute((Path(__file__).resolve().parent.parent / 'schema.sql').read_text(encoding='utf-8'))
            for sequenza in self.SEQUENZE.values():
                cursore.execute(sql.SQL('create sequence if not exists {}').format(sql.Identifier(sequenza)))
            for categoria, colonna, tabella in [('clienti','numero_cliente','cliente'), ('dipendenti','id_dipendente','dipendente'), ('conti','id_conto','conto_corrente')]:
                self._allinea_sequenza(cursore, categoria, f'select coalesce(max({colonna}), 0) as massimo from {tabella}')
            self._allinea_sequenza(cursore, 'operazioni', 'select coalesce(max(id_operazione), 0) as massimo from (select id_operazione from movimento union all select id_operazione from finanziamento union all select id_operazione from investimento) as t')
            return not bool(esistenti)
        return self._scrittura(azione)

    def _allinea_sequenza(self, cursore, categoria, query):
        nome = self.SEQUENZE[categoria]
        cursore.execute(query)
        massimo = cursore.fetchone()['massimo']
        cursore.execute(sql.SQL('select last_value, is_called from {}').format(sql.Identifier(nome)))
        stato = cursore.fetchone()
        precedente = stato['last_value'] if stato['is_called'] else stato['last_value'] - 1
        cursore.execute('select setval(%s::regclass, %s, %s)', (nome, max(1, massimo, precedente), bool(massimo or precedente)))

    def _prossimo(self, cursore, categoria):
        cursore.execute('select nextval(%s::regclass) as id', (self.SEQUENZE[categoria],))
        return cursore.fetchone()['id']

    def stato_database(self):
        return self._lettura('select current_database() as database, current_user as utente', singolo=True)

    def filiali(self):
        return self._lettura('select codice_filiale, nome, citta, provincia from filiale order by codice_filiale')

    def filiale(self, codice):
        return self._lettura('select f.*, d.nome as direttore_nome, d.cognome as direttore_cognome, (select count(*) from cliente c where c.codice_filiale = f.codice_filiale) as totale_clienti, (select count(*) from dipendente d2 where d2.codice_filiale = f.codice_filiale) as totale_dipendenti, (select count(*) from atm a where a.codice_filiale = f.codice_filiale) as totale_atm from filiale f left join dipendente d on d.id_dipendente = f.direttore_id where f.codice_filiale = %s', (codice,), True)

    def lista(self, entita, codice):
        query = {
            'filiale': 'select codice_filiale, nome as nome_filiale, citta, provincia, regione, data_apertura, direttore_id from filiale where codice_filiale = %s',
            'dipendenti': 'select id_dipendente, ruolo, nome, cognome, codice_fiscale, recapito, data_assunzione, specializzazione, liv_autorizzazione from dipendente where codice_filiale = %s order by id_dipendente',
            'atm': 'select codice_atm, codice_filiale, stato, data_installazione from atm where codice_filiale = %s order by codice_atm',
            'clienti': 'select numero_cliente, nome, cognome, codice_fiscale, recapito, email, data_nascita, citta, data_registrazione, segmento from cliente where codice_filiale = %s order by numero_cliente',
            'conti': 'select c.id_conto, c.iban, c.numero_cliente, c.tipo_conto, c.data_apertura, c.stato, c.saldo from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s order by c.id_conto',
            'movimenti': 'select m.id_operazione, m.id_conto, m.tipo, m.data_operazione, m.importo, m.canale, m.causale, m.tipo_versamento from movimento m join conto_corrente c on c.id_conto = m.id_conto join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s order by m.id_operazione',
            'finanziamenti': 'select f.id_operazione, f.id_conto, f.numero_cliente, f.tipo, f.data_operazione, f.importo, f.durata_mesi, f.tasso, f.stato, f.finalita, f.eseguito from finanziamento f join cliente cl on cl.numero_cliente = f.numero_cliente where cl.codice_filiale = %s order by f.id_operazione',
            'investimenti': 'select i.id_operazione, i.id_conto, i.numero_cliente, i.data_operazione, i.importo, i.prodotto, i.profilo_rischio, i.rendimento_atteso, i.stato, i.eseguito from investimento i join cliente cl on cl.numero_cliente = i.numero_cliente where cl.codice_filiale = %s order by i.id_operazione'
        }
        if entita not in query: raise ValueError('Entita non valida')
        return self._lettura(query[entita], (codice,))

    def dettaglio(self, entita, chiave, codice):
        if entita not in self.CHIAVI: raise ValueError('Entita non valida')
        # Usa le query filtrate per filiale, non gli oggetti in memoria.
        tabella = self.NOMI_TABELLE[entita]
        id_col = self.CHIAVI[entita]
        scope = {
            'filiale': 'codice_filiale = %s',
            'dipendenti': 'codice_filiale = %s', 'atm': 'codice_filiale = %s', 'clienti': 'codice_filiale = %s',
            'conti': 'numero_cliente in (select numero_cliente from cliente where codice_filiale = %s)',
            'movimenti': 'id_conto in (select c.id_conto from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s)',
            'finanziamenti': 'numero_cliente in (select numero_cliente from cliente where codice_filiale = %s)',
            'investimenti': 'numero_cliente in (select numero_cliente from cliente where codice_filiale = %s)'
        }
        query = sql.SQL('select * from {} where {} = %s and {}').format(sql.Identifier(tabella), sql.Identifier(id_col), sql.SQL(scope[entita]))
        return self._lettura(query, (chiave, codice), True)

    def _esiste(self, cursore, entita, chiave, codice):
        valore = self.dettaglio(entita, chiave, codice)
        if valore is None: raise OperazioneNonConsentitaError(f'{entita}: identificativo {chiave} non trovato nella filiale {codice}')
        return valore

    def nuova_filiale(self, filiale, direttore, atm):
        def azione(cur):
            cur.execute('insert into filiale (codice_filiale, nome, citta, provincia, regione, data_apertura) values (%s,%s,%s,%s,%s,%s)', (filiale.codice_filiale, filiale.nome, filiale.citta, filiale.provincia, filiale.regione, filiale.data_apertura))
            direttore.id_dipendente = self._prossimo(cur, 'dipendenti')
            cur.execute('insert into dipendente (id_dipendente,codice_filiale,ruolo,nome,cognome,codice_fiscale,recapito,data_assunzione,specializzazione,liv_autorizzazione) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (direttore.id_dipendente, filiale.codice_filiale, 'Direttore', direttore.nome, direttore.cognome, direttore.codice_fiscale, direttore.recapito, direttore.data_assunzione, direttore.specializzazione.value, direttore.liv_autorizzazione))
            cur.execute('update filiale set direttore_id = %s where codice_filiale = %s', (direttore.id_dipendente, filiale.codice_filiale))
            cur.execute('insert into atm (codice_atm,codice_filiale,stato,data_installazione) values (%s,%s,%s,%s)', (atm.codice_atm, atm.filiale, atm.stato.value, atm.data_installazione))
        self._scrittura(azione)
        return self.filiale(filiale.codice_filiale)

    def nuovo_cliente(self, codice, cliente):
        def azione(cur):
            cliente.numero_cliente = self._prossimo(cur, 'clienti')
            cur.execute('insert into cliente (numero_cliente,codice_filiale,nome,cognome,codice_fiscale,recapito,email,data_nascita,citta,data_registrazione,segmento) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (cliente.numero_cliente,codice,cliente.nome,cliente.cognome,cliente.codice_fiscale,cliente.recapito,cliente.email,cliente.data_nascita,cliente.citta,cliente.data_registrazione,cliente.segmento.value))
        self._scrittura(azione)
        return self.dettaglio('clienti', cliente.numero_cliente, codice)

    def nuovo_dipendente(self, codice, dipendente, ruolo):
        def azione(cur):
            dipendente.id_dipendente = self._prossimo(cur, 'dipendenti')
            cur.execute('insert into dipendente (id_dipendente,codice_filiale,ruolo,nome,cognome,codice_fiscale,recapito,data_assunzione,specializzazione,liv_autorizzazione) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (dipendente.id_dipendente,codice,ruolo,dipendente.nome,dipendente.cognome,dipendente.codice_fiscale,dipendente.recapito,dipendente.data_assunzione,dipendente.specializzazione.value if ruolo == 'Specialista' else None,None))
        self._scrittura(azione)
        return self.dettaglio('dipendenti', dipendente.id_dipendente, codice)

    def nuovo_atm(self, atm):
        self._scrittura(lambda cur: cur.execute('insert into atm (codice_atm,codice_filiale,stato,data_installazione) values (%s,%s,%s,%s)', (atm.codice_atm,atm.filiale,atm.stato.value,atm.data_installazione)))
        return self.dettaglio('atm', atm.codice_atm, atm.filiale)

    def nuovo_conto(self, codice, conto):
        def azione(cur):
            cur.execute('select 1 from cliente where numero_cliente = %s and codice_filiale = %s', (conto.intestatario.numero_cliente, codice))
            if cur.fetchone() is None: raise OperazioneNonConsentitaError('Cliente non presente nella filiale')
            conto.id_conto = self._prossimo(cur, 'conti')
            cur.execute('insert into conto_corrente (id_conto,iban,numero_cliente,tipo_conto,data_apertura,stato,saldo) values (%s,%s,%s,%s,%s,%s,0)', (conto.id_conto, conto.iban, conto.intestatario.numero_cliente, conto.tipo_conto.value, conto.data_apertura, conto.stato.value))
        self._scrittura(azione)
        return self.dettaglio('conti', conto.id_conto, codice)

    def modifica(self, entita, chiave, codice, modifiche):
        consentiti = self.MODIFICABILI.get(entita)
        if not consentiti or not modifiche or set(modifiche) - set(consentiti): raise ValueError('Campi da modificare non consentiti')
        tabella, pk = self.NOMI_TABELLE[entita], self.CHIAVI[entita]
        def azione(cur):
            precedente = self.dettaglio(entita, chiave, codice)
            if precedente is None: raise OperazioneNonConsentitaError('Record non trovato nella filiale selezionata')
            colonne = list(modifiche)
            query = sql.SQL('update {} set {} where {} = %s').format(sql.Identifier(tabella), sql.SQL(', ').join(sql.SQL('{} = %s').format(sql.Identifier(c)) for c in colonne), sql.Identifier(pk))
            cur.execute(query, (*[modifiche[k] for k in colonne], chiave))
            if cur.rowcount != 1: raise OperazioneNonConsentitaError('Record non modificato')
        self._scrittura(azione)
        return self.dettaglio(entita, chiave, codice)

    def _conto_bloccato(self, cur, codice, id_conto, richiedi_attivo=True):
        cur.execute('select c.id_conto,c.numero_cliente,c.saldo,c.stato from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where c.id_conto = %s and cl.codice_filiale = %s for update of c', (id_conto, codice))
        conto = cur.fetchone()
        if conto is None: raise OperazioneNonConsentitaError('Conto inesistente nella filiale')
        if richiedi_attivo and conto['stato'] != 'Attivo': raise OperazioneNonConsentitaError(f'Conto non operativo: {conto["stato"]}')
        return conto

    def _importo(self, valore, massimo=1000000):
        try:
            n = Decimal(str(valore))
            if not n.is_finite() or n <= 0 or n >= massimo or n != n.quantize(Decimal('0.01')): raise ValueError()
            return n.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f'Importo non valido: deve essere positivo, con massimo due decimali e inferiore a {massimo}')

    def _registra_movimento(self, cur, codice, dati, id_esistente=None, storico=False):
        conto = self._conto_bloccato(cur, codice, dati['id_conto'], not storico)
        if dati['tipo'] not in ('Versamento', 'Prelievo'): raise ValueError('Tipo movimento non valido')
        importo = self._importo(dati['importo'])
        if dati['tipo'] == 'Versamento':
            if dati['tipo_versamento'] not in ('Contanti', 'Assegno'): raise ValueError('Tipo versamento non valido')
            if dati['tipo_versamento'] == 'Contanti' and importo > 5000: raise OperazioneNonConsentitaError('Versamento in contanti oltre limite')
        else:
            if dati.get('tipo_versamento'): raise ValueError('Un prelievo non ha tipo versamento')
            if importo > 5000: raise OperazioneNonConsentitaError('Prelievo superiore a 5000 euro')
            if conto['saldo'] < importo: raise SaldoInsufficienteError(f'Saldo insufficiente: {conto["saldo"]} euro')
        id_operazione = id_esistente if id_esistente is not None else self._prossimo(cur, 'operazioni')
        cur.execute('insert into movimento (id_operazione,id_conto,tipo,data_operazione,importo,canale,causale,tipo_versamento) values (%s,%s,%s,%s,%s,%s,%s,%s)', (id_operazione,dati['id_conto'],dati['tipo'],dati['data_operazione'],importo,dati['canale'],dati['causale'],dati.get('tipo_versamento')))
        delta = importo if dati['tipo'] == 'Versamento' else -importo
        cur.execute('update conto_corrente set saldo = saldo + %s where id_conto = %s', (delta, dati['id_conto']))
        return id_operazione

    def nuovo_movimento(self, codice, dati, codice_atm=None):
        def azione(cur):
            if codice_atm is not None:
                cur.execute('select stato from atm where codice_atm = %s and codice_filiale = %s', (codice_atm, codice))
                atm = cur.fetchone()
                if atm is None or atm['stato'] != 'Attivo': raise OperazioneNonConsentitaError('ATM assente, non attivo o di altra filiale')
            return self._registra_movimento(cur, codice, dati)
        id_operazione = self._scrittura(azione)
        return self.dettaglio('movimenti', id_operazione, codice), self.dettaglio('conti', dati['id_conto'], codice)['saldo']

    def _registra_finanziamento(self, cur, codice, dati, id_esistente=None, storico=False):
        conto = self._conto_bloccato(cur, codice, dati['id_conto'], not storico)
        importo = self._importo(dati['importo'])
        if dati['tipo'] not in ('Prestito','Mutuo'): raise ValueError('Tipo finanziamento non valido')
        if not 3 <= int(dati['durata_mesi']) <= 480: raise ValueError('Durata da 3 a 480 mesi')
        if not 0 <= Decimal(str(dati['tasso'])) <= 30: raise ValueError('Tasso non valido')
        if conto['numero_cliente'] != dati['numero_cliente']: raise OperazioneNonConsentitaError('Conto e cliente non corrispondono')
        stato, eseguito = dati['stato'], dati['eseguito']
        if (stato, eseguito) not in (('Richiesta', False), ('Approvata', True), ('Rifiutata', False)): raise ValueError('Stato finanziamento incoerente')
        id_operazione = id_esistente if id_esistente is not None else self._prossimo(cur, 'operazioni')
        cur.execute('insert into finanziamento (id_operazione,id_conto,numero_cliente,tipo,data_operazione,importo,durata_mesi,tasso,stato,finalita,eseguito) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (id_operazione,dati['id_conto'],dati['numero_cliente'],dati['tipo'],dati['data_operazione'],importo,dati['durata_mesi'],dati['tasso'],stato,dati['finalita'],eseguito))
        if eseguito: cur.execute('update conto_corrente set saldo = saldo + %s where id_conto = %s', (importo, dati['id_conto']))
        return id_operazione

    def nuovo_finanziamento(self, codice, dati):
        id_operazione = self._scrittura(lambda cur: self._registra_finanziamento(cur, codice, dati))
        return self.dettaglio('finanziamenti', id_operazione, codice)

    def delibera_finanziamento(self, codice, id_operazione, stato):
        if stato not in ('Approvata', 'Rifiutata'): raise ValueError('Delibera non valida')
        def azione(cur):
            cur.execute('select f.* from finanziamento f join cliente cl on cl.numero_cliente = f.numero_cliente where f.id_operazione = %s and cl.codice_filiale = %s for update of f', (id_operazione, codice))
            f = cur.fetchone()
            if f is None: raise OperazioneNonConsentitaError('Finanziamento non trovato')
            if f['stato'] != 'Richiesta' or f['eseguito']: raise OperazioneNonConsentitaError('Finanziamento gia deliberato')
            if stato == 'Approvata':
                self._conto_bloccato(cur, codice, f['id_conto'])
                cur.execute('update conto_corrente set saldo = saldo + %s where id_conto = %s', (f['importo'], f['id_conto']))
            cur.execute('update finanziamento set stato = %s, eseguito = %s where id_operazione = %s', (stato, stato == 'Approvata', id_operazione))
        self._scrittura(azione)
        return self.dettaglio('finanziamenti', id_operazione, codice)

    def _registra_investimento(self, cur, codice, dati, id_esistente=None, storico=False):
        conto = self._conto_bloccato(cur, codice, dati['id_conto'], not storico)
        importo = self._importo(dati['importo'], 100000)
        if conto['numero_cliente'] != dati['numero_cliente']: raise OperazioneNonConsentitaError('Cliente e conto non corrispondono')
        if not -100 <= Decimal(str(dati['rendimento_atteso'])) <= 100: raise ValueError('Rendimento non valido')
        if dati['eseguito'] and importo > conto['saldo']: raise SaldoInsufficienteError('Saldo insufficiente per investimento')
        id_operazione = id_esistente if id_esistente is not None else self._prossimo(cur, 'operazioni')
        cur.execute('insert into investimento (id_operazione,id_conto,numero_cliente,data_operazione,importo,prodotto,profilo_rischio,rendimento_atteso,stato,eseguito) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (id_operazione,dati['id_conto'],dati['numero_cliente'],dati['data_operazione'],importo,dati['prodotto'],dati['profilo_rischio'],dati['rendimento_atteso'],dati['stato'],dati['eseguito']))
        if dati['eseguito']: cur.execute('update conto_corrente set saldo = saldo - %s where id_conto = %s', (importo, dati['id_conto']))
        return id_operazione

    def nuovo_investimento(self, codice, dati):
        id_operazione = self._scrittura(lambda cur: self._registra_investimento(cur, codice, dati))
        return self.dettaglio('investimenti', id_operazione, codice)

    def movimenti_periodo(self, codice, inizio, fine):
        return self._lettura('select m.* from movimento m join conto_corrente c on c.id_conto = m.id_conto join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s and m.data_operazione between %s and %s order by m.data_operazione, m.id_operazione', (codice, inizio, fine))

    def report(self, codice):
        return {
            'saldi': self._lettura('select count(c.id_conto) as numero_conti, coalesce(sum(c.saldo),0) as saldo_totale, coalesce(avg(c.saldo),0) as saldo_medio from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s', (codice,), True),
            'segmenti': self._lettura('select segmento, count(*) as totale from cliente where codice_filiale = %s group by segmento order by segmento', (codice,)),
            'canali': self._lettura('select m.canale, count(*) as numero_operazioni, sum(m.importo) as volume from movimento m join conto_corrente c on c.id_conto = m.id_conto join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s group by m.canale order by m.canale', (codice,)),
            'finanziamenti': self._lettura('select f.stato, count(*) as totale, sum(f.importo) as importo_totale from finanziamento f join cliente c on c.numero_cliente = f.numero_cliente where c.codice_filiale = %s group by f.stato order by f.stato', (codice,))
        }

    def importa(self, entita, righe, codice):
        if entita not in self.CHIAVI: raise ValueError('Entita non valida')
        def azione(cur):
            elaborati = 0
            for riga in righe:
                dati = dict(riga)
                chiave = dati[self.CHIAVI[entita]]
                vecchio = self.dettaglio(entita, chiave, codice)
                if entita == 'filiale':
                    if dati['codice_filiale'].upper() != codice or vecchio is None or dati['direttore_id'] != vecchio['direttore_id']: raise OperazioneNonConsentitaError('CSV filiale: codice o direttore non corrispondente')
                    cur.execute('update filiale set nome = %s,citta = %s,provincia = %s,regione = %s,data_apertura = %s where codice_filiale = %s', (dati['nome_filiale'],dati['citta'],dati['provincia'],dati['regione'],dati['data_apertura'],codice))
                elif entita in ('clienti','dipendenti','atm','conti'):
                    if entita == 'atm':
                        if dati['codice_filiale'].upper() != codice: raise OperazioneNonConsentitaError('ATM di altra filiale')
                        cur.execute('select codice_filiale from atm where codice_atm = %s', (chiave,))
                        trovato_atm = cur.fetchone()
                        if trovato_atm and trovato_atm['codice_filiale'] != codice: raise OperazioneNonConsentitaError('ATM gia presente in un altra filiale')
                    if entita == 'conti':
                        cur.execute('select 1 from cliente where numero_cliente = %s and codice_filiale = %s', (dati['numero_cliente'],codice))
                        if cur.fetchone() is None: raise OperazioneNonConsentitaError('Cliente del conto di altra filiale')
                        if vecchio and dati['numero_cliente'] != vecchio['numero_cliente']: raise OperazioneNonConsentitaError('Intestatario conto non modificabile')
                        dati['saldo'] = 0 if vecchio is None else vecchio['saldo']
                    if entita in ('clienti','dipendenti'):
                        cur.execute(sql.SQL('select codice_filiale from {} where {} = %s').format(sql.Identifier(self.NOMI_TABELLE[entita]),sql.Identifier(self.CHIAVI[entita])), (chiave,))
                        trovato = cur.fetchone()
                        if trovato and trovato['codice_filiale'] != codice: raise OperazioneNonConsentitaError('Identificativo gia usato da altra filiale')
                        dati['codice_filiale'] = codice
                    if entita == 'dipendenti':
                        if dati.get('specializzazione') == '': dati['specializzazione'] = None
                        if not dati.get('liv_autorizzazione'): dati['liv_autorizzazione'] = None
                        if vecchio and vecchio['ruolo'] == 'Direttore' and dati['ruolo'] != 'Direttore': raise OperazioneNonConsentitaError('Non cambiare il ruolo del direttore via CSV')
                    tabella = self.NOMI_TABELLE[entita]
                    colonne = list(dati)
                    q = sql.SQL('insert into {} ({}) values ({}) on conflict ({}) do update set {}').format(sql.Identifier(tabella), sql.SQL(',').join(sql.Identifier(k) for k in colonne), sql.SQL(',').join(sql.Placeholder() for _ in colonne), sql.Identifier(self.CHIAVI[entita]), sql.SQL(',').join(sql.SQL('{}=excluded.{}').format(sql.Identifier(k),sql.Identifier(k)) for k in colonne if k not in (self.CHIAVI[entita], 'saldo', 'codice_filiale')))
                    cur.execute(q, tuple(dati[k] for k in colonne))
                else:
                    if vecchio:
                        # Le operazioni precedenti non vengono applicate due volte.
                        continue
                    for altra in ('movimenti','finanziamenti','investimenti'):
                        if altra == entita: continue
                        cur.execute(sql.SQL('select 1 from {} where id_operazione = %s').format(sql.Identifier(self.NOMI_TABELLE[altra])), (chiave,))
                        if cur.fetchone(): raise OperazioneNonConsentitaError('ID operazione gia esistente in altra tabella')
                    if entita == 'movimenti': self._registra_movimento(cur, codice, dati, chiave, True)
                    elif entita == 'finanziamenti': self._registra_finanziamento(cur, codice, dati, chiave, True)
                    else: self._registra_investimento(cur, codice, dati, chiave, True)
                elaborati += 1
            categoria = {'clienti': 'clienti', 'dipendenti': 'dipendenti', 'conti': 'conti', 'movimenti': 'operazioni', 'finanziamenti': 'operazioni', 'investimenti': 'operazioni'}.get(entita)
            if categoria:
                queries = {'clienti': 'select coalesce(max(numero_cliente),0) as massimo from cliente', 'dipendenti': 'select coalesce(max(id_dipendente),0) as massimo from dipendente', 'conti': 'select coalesce(max(id_conto),0) as massimo from conto_corrente', 'operazioni': 'select coalesce(max(id_operazione),0) as massimo from (select id_operazione from movimento union all select id_operazione from finanziamento union all select id_operazione from investimento) as q'}
                self._allinea_sequenza(cur, categoria, queries[categoria])
            return elaborati
        return self._scrittura(azione)

    def movimenti_conto(self, codice, id_conto):
        return self._lettura('select m.* from movimento m join conto_corrente c on c.id_conto = m.id_conto join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s and m.id_conto = %s order by m.data_operazione, m.id_operazione', (codice, id_conto))
