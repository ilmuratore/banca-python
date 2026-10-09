import psycopg
from psycopg import sql

from psycopg.rows import dict_row

from models import Versamento, Prelievo, Specialista, Direttore, StatoRichiesta, SaldoInsufficienteError, OperazioneNonConsentitaError
from services.mapper import MapperBanca
from decimal import Decimal, ROUND_HALF_UP


def round_importo(valore):
    numero = Decimal(str(valore))
    if not numero.is_finite(): raise ValueError("Importo non finito")
    return numero.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def equivalenti(precedente, valori):
    return all(str(precedente[k] if precedente[k] is not None else "") == str(v if v is not None else "") or (isinstance(precedente[k], Decimal) and precedente[k] == round_importo(v)) for k, v in valori.items())


class DatabaseError(Exception):
    pass


# ===================
# DATABASE POSTGRESQL
# ===================

class DatabasePostgreSQL(MapperBanca):

    def __init__(self, host, dbname, user, password, port=5432):
        self.codice_filiale = None
        try:
            self.connessione = psycopg.connect(host=host, dbname=dbname, user=user, password=password, port=port, row_factory=dict_row)
        except psycopg.Error as errore:
            raise DatabaseError(f"Connessione a PostgreSQL non riuscita: {errore}") from errore

    def chiudi(self):
        if self.connessione is not None and not self.connessione.closed:
            self.connessione.close()

    def verifica_connessione(self):
        return self._select_one("select current_database() as database, current_user as utente")

    def _rollback_e_rilancia(self, errore):
        self.connessione.rollback()
        raise DatabaseError(f"Errore PostgreSQL: {errore}") from errore

    def inizializza_schema(self):
        from pathlib import Path

        schema = Path(__file__).resolve().parent.parent / "schema.sql"
        if not schema.exists():
            raise DatabaseError("File schema.sql non trovato")
        tabelle = ["filiale", "dipendente", "atm", "cliente", "conto_corrente", "movimento", "finanziamento", "investimento"]
        try:
            with self.connessione.cursor() as cursore:
                cursore.execute("select tablename from pg_tables where schemaname = current_schema()")
                esistenti = {riga["tablename"] for riga in cursore.fetchall()}
            if all(tabella in esistenti for tabella in tabelle):
                self.connessione.commit()
                return False
            if any(tabella in esistenti for tabella in tabelle):
                self.connessione.rollback()
                raise DatabaseError("Schema parziale: completare o correggere manualmente il database")
            script = schema.read_text(encoding="utf-8")
            with self.connessione.cursor() as cursore:
                cursore.execute(script)
            self.connessione.commit()
            return True
        except psycopg.Error as errore:
            self._rollback_e_rilancia(errore)

    # =====================
    # GENERAZIONE NUOVI ID
    # =====================

    def prossimo_numero_cliente(self):
        return self._prossimo_id("cliente", "numero_cliente")

    def prossimo_id_dipendente(self):
        return self._prossimo_id("dipendente", "id_dipendente")

    def prossimo_id_conto(self):
        return self._prossimo_id("conto_corrente", "id_conto")

    def prossimo_id_operazione(self):
        query = """
            select coalesce(max(id_operazione), 0) + 1 as prossimo_id
            from (
                select id_operazione from movimento
                union all
                select id_operazione from finanziamento
                union all
                select id_operazione from investimento
            ) as operazioni
        """
        return self._select_one(query)["prossimo_id"]

    def _prossimo_id(self, tabella, colonna):
        query = f"select coalesce(max({colonna}), 0) + 1 as prossimo_id from {tabella}"
        return self._select_one(query)["prossimo_id"]

    # ==================
    # FUNZIONI DI SUPPORTO
    # ==================

    def _dati_dipendente(self, dipendente):
        ruolo = self._ruolo_dipendente(dipendente)
        specializzazione = dipendente.specializzazione.value if isinstance(dipendente, Specialista) else None
        liv_autorizzazione = dipendente.liv_autorizzazione if isinstance(dipendente, Direttore) else None
        return ruolo, specializzazione, liv_autorizzazione

    def _inserisci_dipendente_cursore(self, cursore, codice_filiale, dipendente):
        ruolo, specializzazione, liv_autorizzazione = self._dati_dipendente(dipendente)
        query = """
            insert into dipendente (id_dipendente, codice_filiale, ruolo, nome, cognome, codice_fiscale, recapito, data_assunzione, specializzazione, liv_autorizzazione)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursore.execute(query, (dipendente.id_dipendente, codice_filiale, ruolo, dipendente.nome, dipendente.cognome, dipendente.codice_fiscale, dipendente.recapito, dipendente.data_assunzione, specializzazione, liv_autorizzazione))

    def _inserisci_atm_cursore(self, cursore, atm):
        cursore.execute("insert into atm (codice_atm, codice_filiale, stato, data_installazione) values (%s, %s, %s, %s)", (atm.codice_atm, atm.filiale, atm.stato.value, atm.data_installazione))

    def _inserisci_cliente_cursore(self, cursore, codice_filiale, cliente):
        query = """
            insert into cliente (numero_cliente, codice_filiale, nome, cognome, codice_fiscale, recapito, email, data_nascita, citta, data_registrazione, segmento)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursore.execute(query, (cliente.numero_cliente, codice_filiale, cliente.nome, cliente.cognome, cliente.codice_fiscale, cliente.recapito, cliente.email, cliente.data_nascita, cliente.citta, cliente.data_registrazione, cliente.segmento.value))

    def _inserisci_conto_cursore(self, cursore, conto):
        query = """
            insert into conto_corrente (id_conto, iban, numero_cliente, tipo_conto, data_apertura, stato, saldo)
            values (%s, %s, %s, %s, %s, %s, %s)
        """
        cursore.execute(query, (conto.id_conto, conto.iban, conto.intestatario.numero_cliente, conto.tipo_conto.value, conto.data_apertura, conto.stato.value, conto.saldo))

    def _inserisci_movimento_cursore(self, cursore, movimento):
        tipo_versamento = movimento.tipo_versamento.value if isinstance(movimento, Versamento) else None
        query = """
            insert into movimento (id_operazione, id_conto, tipo, data_operazione, importo, canale, causale, tipo_versamento)
            values (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursore.execute(query, (movimento.id_operazione, movimento.conto.id_conto, type(movimento).__name__, movimento.data_operazione, movimento.importo, movimento.canale.value, movimento.causale, tipo_versamento))

    def _inserisci_finanziamento_cursore(self, cursore, finanziamento):
        query = """
            insert into finanziamento (id_operazione, id_conto, numero_cliente, tipo, data_operazione, importo, durata_mesi, tasso, stato, finalita, eseguito)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursore.execute(query, (finanziamento.id_operazione, finanziamento.conto.id_conto, finanziamento.conto.intestatario.numero_cliente, type(finanziamento).__name__, finanziamento.data_operazione, finanziamento.importo, finanziamento.durata_mesi, finanziamento.tasso, finanziamento.stato.value, finanziamento.finalita, finanziamento.eseguito))

    def _inserisci_investimento_cursore(self, cursore, investimento):
        query = """
            insert into investimento (id_operazione, id_conto, numero_cliente, data_operazione, importo, prodotto, profilo_rischio, rendimento_atteso, stato, eseguito)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursore.execute(query, (investimento.id_operazione, investimento.conto.id_conto, investimento.conto.intestatario.numero_cliente, investimento.data_operazione, investimento.importo, investimento.prodotto, investimento.profilo_rischio.value, investimento.rendimento_atteso, investimento.stato.value, investimento.eseguito))

    # ==================
    # INSERT DEL SISTEMA
    # ==================

    def inserisci_filiale(self, filiale):
        try:
            with self.connessione.cursor() as cursore:
                cursore.execute("insert into filiale (codice_filiale, nome, citta, provincia, regione, data_apertura, direttore_id) values (%s, %s, %s, %s, %s, %s, null)", (filiale.codice_filiale, filiale.nome, filiale.citta, filiale.provincia, filiale.regione, filiale.data_apertura))
                self._inserisci_dipendente_cursore(cursore, filiale.codice_filiale, filiale.direttore)
                cursore.execute("update filiale set direttore_id = %s where codice_filiale = %s", (filiale.direttore.id_dipendente, filiale.codice_filiale))
                for atm in filiale.atm: self._inserisci_atm_cursore(cursore, atm)
            self.connessione.commit()
        except psycopg.Error as errore: self._rollback_e_rilancia(errore)

    def inserisci_cliente(self, codice_filiale, cliente):
        try:
            with self.connessione.cursor() as cursore: self._inserisci_cliente_cursore(cursore, codice_filiale, cliente)
            self.connessione.commit()
        except psycopg.Error as errore: self._rollback_e_rilancia(errore)

    def inserisci_dipendente(self, codice_filiale, dipendente):
        try:
            with self.connessione.cursor() as cursore: self._inserisci_dipendente_cursore(cursore, codice_filiale, dipendente)
            self.connessione.commit()
        except psycopg.Error as errore: self._rollback_e_rilancia(errore)

    def inserisci_atm(self, atm):
        try:
            with self.connessione.cursor() as cursore: self._inserisci_atm_cursore(cursore, atm)
            self.connessione.commit()
        except psycopg.Error as errore: self._rollback_e_rilancia(errore)

    def inserisci_conto(self, conto):
        try:
            with self.connessione.cursor() as cursore: self._inserisci_conto_cursore(cursore, conto)
            self.connessione.commit()
        except psycopg.Error as errore: self._rollback_e_rilancia(errore)


    def inserisci_finanziamento(self, finanziamento):
        try:
            with self.connessione.cursor() as cursore:
                self._controlla_id_operazione(cursore, finanziamento.id_operazione)
                self._conto_bloccato(cursore, finanziamento.conto.id_conto)
                self._inserisci_finanziamento_cursore(cursore, finanziamento)
            self.connessione.commit()
        except psycopg.Error as errore: self._rollback_e_rilancia(errore)


    # ==================
    # UPDATE DEL SISTEMA
    # ==================

    def aggiorna_filiale(self, filiale):
        query = "update filiale set nome = %s, citta = %s, provincia = %s, regione = %s, data_apertura = %s, direttore_id = %s where codice_filiale = %s"
        self._esegui(query, (filiale.nome, filiale.citta, filiale.provincia, filiale.regione, filiale.data_apertura, filiale.direttore.id_dipendente, filiale.codice_filiale))

    def aggiorna_cliente(self, cliente):
        query = "update cliente set nome = %s, cognome = %s, codice_fiscale = %s, recapito = %s, email = %s, data_nascita = %s, citta = %s, data_registrazione = %s, segmento = %s where numero_cliente = %s"
        self._esegui(query, (cliente.nome, cliente.cognome, cliente.codice_fiscale, cliente.recapito, cliente.email, cliente.data_nascita, cliente.citta, cliente.data_registrazione, cliente.segmento.value, cliente.numero_cliente))

    def aggiorna_dipendente(self, dipendente):
        ruolo, specializzazione, liv_autorizzazione = self._dati_dipendente(dipendente)
        query = "update dipendente set ruolo = %s, nome = %s, cognome = %s, codice_fiscale = %s, recapito = %s, data_assunzione = %s, specializzazione = %s, liv_autorizzazione = %s where id_dipendente = %s"
        self._esegui(query, (ruolo, dipendente.nome, dipendente.cognome, dipendente.codice_fiscale, dipendente.recapito, dipendente.data_assunzione, specializzazione, liv_autorizzazione, dipendente.id_dipendente))

    def aggiorna_atm(self, atm):
        self._esegui("update atm set stato = %s, data_installazione = %s where codice_atm = %s", (atm.stato.value, atm.data_installazione, atm.codice_atm))

    def aggiorna_conto(self, conto):
        query = "update conto_corrente set iban = %s, tipo_conto = %s, data_apertura = %s, stato = %s where id_conto = %s"
        self._esegui(query, (conto.iban, conto.tipo_conto.value, conto.data_apertura, conto.stato.value, conto.id_conto))


    # ============================
    # POSTGRESQL -> OGGETTI PYTHON
    # ============================

    def carica_filiale(self, codice_filiale):
        self.codice_filiale = codice_filiale.strip().upper()
        if not self.esiste_filiale(self.codice_filiale):
            raise DatabaseError(f"Filiale {self.codice_filiale} non trovata")
        return self.ricostruisci(self.leggi())

    def leggi(self):
        if self.codice_filiale is None:
            raise DatabaseError("Nessuna filiale selezionata")
        codice = self.codice_filiale
        return {
            "filiale": self._select_all("select codice_filiale, nome as nome_filiale, citta, provincia, regione, data_apertura, direttore_id from filiale where codice_filiale = %s", (codice,)),
            "dipendenti": self._select_all("select id_dipendente, ruolo, nome, cognome, codice_fiscale, recapito, data_assunzione, specializzazione, liv_autorizzazione from dipendente where codice_filiale = %s order by id_dipendente", (codice,)),
            "atm": self._select_all("select codice_atm, codice_filiale, stato, data_installazione from atm where codice_filiale = %s order by codice_atm", (codice,)),
            "clienti": self._select_all("select numero_cliente, nome, cognome, codice_fiscale, recapito, email, data_nascita, citta, data_registrazione, segmento from cliente where codice_filiale = %s order by numero_cliente", (codice,)),
            "conti": self._select_all("select c.id_conto, c.iban, c.numero_cliente, c.tipo_conto, c.data_apertura, c.stato, c.saldo::double precision as saldo from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s order by c.id_conto", (codice,)),
            "movimenti": self._select_all("select m.id_operazione, m.id_conto, m.tipo, m.data_operazione, m.importo::double precision as importo, m.canale, m.causale, coalesce(m.tipo_versamento, '') as tipo_versamento from movimento m join conto_corrente c on c.id_conto = m.id_conto join cliente cl on cl.numero_cliente = c.numero_cliente where cl.codice_filiale = %s order by m.id_operazione", (codice,)),
            "finanziamenti": self._select_all("select f.id_operazione, f.id_conto, f.numero_cliente, f.tipo, f.data_operazione, f.importo::double precision as importo, f.durata_mesi, f.tasso::double precision as tasso, f.stato, f.finalita, f.eseguito from finanziamento f join cliente cl on cl.numero_cliente = f.numero_cliente where cl.codice_filiale = %s order by f.id_operazione", (codice,)),
            "investimenti": self._select_all("select i.id_operazione, i.id_conto, i.numero_cliente, i.data_operazione, i.importo::double precision as importo, i.prodotto, i.profilo_rischio, i.rendimento_atteso::double precision as rendimento_atteso, i.stato, i.eseguito from investimento i join cliente cl on cl.numero_cliente = i.numero_cliente where cl.codice_filiale = %s order by i.id_operazione", (codice,))
        }

    # ==================
    # RICERCHE E REPORT
    # ==================

    def esiste_filiale(self, codice_filiale):
        riga = self._select_one("select exists(select 1 from filiale where codice_filiale = %s) as presente", (codice_filiale.strip().upper(),))
        return riga["presente"]

    def elenco_filiali(self):
        return self._select_all("select codice_filiale, nome, citta, provincia from filiale order by codice_filiale")

    def report_saldi(self, codice_filiale):
        query = """
            select count(c.id_conto) as numero_conti, coalesce(sum(c.saldo), 0) as saldo_totale, coalesce(avg(c.saldo), 0) as saldo_medio
            from conto_corrente c
            join cliente cl on cl.numero_cliente = c.numero_cliente
            where cl.codice_filiale = %s
        """
        return self._select_one(query, (codice_filiale,))

    def report_clienti_segmento(self, codice_filiale):
        return self._select_all("select segmento, count(*) as totale from cliente where codice_filiale = %s group by segmento order by segmento", (codice_filiale,))

    def report_operazioni_canale(self, codice_filiale):
        query = """
            select canale, count(*) as numero_operazioni, coalesce(sum(importo), 0) as volume
            from (
                select m.canale, m.importo
                from movimento m
                join conto_corrente c on c.id_conto = m.id_conto
                join cliente cl on cl.numero_cliente = c.numero_cliente
                where cl.codice_filiale = %s
                union all
                select 'Filiale' as canale, f.importo
                from finanziamento f
                join cliente cl on cl.numero_cliente = f.numero_cliente
                where cl.codice_filiale = %s and f.eseguito = true
                union all
                select 'Filiale' as canale, i.importo
                from investimento i
                join cliente cl on cl.numero_cliente = i.numero_cliente
                where cl.codice_filiale = %s and i.eseguito = true
            ) as operazioni
            group by canale
            order by canale
        """
        return self._select_all(query, (codice_filiale, codice_filiale, codice_filiale))

    def report_finanziamenti_stato(self, codice_filiale):
        query = """
            select f.stato, count(*) as totale, coalesce(sum(f.importo), 0) as importo_totale
            from finanziamento f
            join cliente cl on cl.numero_cliente = f.numero_cliente
            where cl.codice_filiale = %s
            group by f.stato
            order by f.stato
        """
        return self._select_all(query, (codice_filiale,))

    # ==================
    # QUERY GENERICHE
    # ==================

    def _esegui(self, query, parametri=()):
        try:
            with self.connessione.cursor() as cursore: cursore.execute(query, parametri)
            self.connessione.commit()
        except psycopg.Error as errore: self._rollback_e_rilancia(errore)

    def _select_one(self, query, parametri=()):
        try:
            with self.connessione.cursor() as cursore:
                cursore.execute(query, parametri)
                return cursore.fetchone()
        except psycopg.Error as errore:
            self._rollback_e_rilancia(errore)

    def _select_all(self, query, parametri=()):
        try:
            with self.connessione.cursor() as cursore:
                cursore.execute(query, parametri)
                return cursore.fetchall()
        except psycopg.Error as errore:
            self._rollback_e_rilancia(errore)

    # ================================
    # OPERAZIONI ATOMICHE SUL DATABASE
    # ================================

    def _controlla_id_operazione(self, cursore, id_operazione):
        cursore.execute("select 1 from movimento where id_operazione = %s union all select 1 from finanziamento where id_operazione = %s union all select 1 from investimento where id_operazione = %s", (id_operazione, id_operazione, id_operazione))
        if cursore.fetchone() is not None:
            raise OperazioneNonConsentitaError(f"ID operazione {id_operazione} gia presente")

    def _conto_bloccato(self, cursore, id_conto, codice_filiale=None):
        cursore.execute("select c.id_conto, c.saldo, c.stato, cl.codice_filiale from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where c.id_conto = %s for update of c", (id_conto,))
        riga = cursore.fetchone()
        if riga is None:
            raise OperazioneNonConsentitaError(f"Conto {id_conto} non trovato")
        if codice_filiale is not None and riga["codice_filiale"] != codice_filiale:
            raise OperazioneNonConsentitaError("Il conto appartiene a un'altra filiale")
        if riga["stato"] != "Attivo":
            raise OperazioneNonConsentitaError("Il conto non e' attivo")
        return riga

    def inserisci_movimento(self, movimento, codice_filiale=None):
        try:
            with self.connessione.cursor() as cursore:
                conto = self._conto_bloccato(cursore, movimento.conto.id_conto, codice_filiale)
                self._controlla_id_operazione(cursore, movimento.id_operazione)
                if round_importo(movimento.importo) <= 0: raise ValueError("L'importo deve essere almeno 0.01")
                if movimento.importo >= 1_000_000:
                    raise OperazioneNonConsentitaError("Importo superiore al limite consentito")
                if isinstance(movimento, Versamento):
                    if movimento.tipo_versamento.value == "Contanti" and movimento.importo > 5000:
                        raise OperazioneNonConsentitaError("Versamento contanti oltre il limite consentito")
                    saldo_nuovo = conto["saldo"] + round_importo(movimento.importo)
                elif isinstance(movimento, Prelievo):
                    if movimento.importo > 5000:
                        raise OperazioneNonConsentitaError("Prelievo oltre il limite consentito")
                    if round_importo(movimento.importo) > conto["saldo"]:
                        raise SaldoInsufficienteError(f"Saldo insufficiente: {conto['saldo']:.2f} euro")
                    saldo_nuovo = conto["saldo"] - round_importo(movimento.importo)
                else:
                    raise TypeError("Movimento non riconosciuto")
                self._inserisci_movimento_cursore(cursore, movimento)
                cursore.execute("update conto_corrente set saldo = %s where id_conto = %s", (saldo_nuovo, movimento.conto.id_conto))
            self.connessione.commit()
        except Exception as errore:
            self.connessione.rollback()
            if isinstance(errore, psycopg.Error): raise DatabaseError(f"Errore PostgreSQL: {errore}") from errore
            raise

    def inserisci_investimento(self, investimento, codice_filiale=None):
        try:
            with self.connessione.cursor() as cursore:
                conto = self._conto_bloccato(cursore, investimento.conto.id_conto, codice_filiale)
                self._controlla_id_operazione(cursore, investimento.id_operazione)
                if round_importo(investimento.importo) <= 0: raise ValueError("L'importo deve essere almeno 0.01")
                if investimento.importo >= 100_000:
                    raise OperazioneNonConsentitaError("Importo investimento superiore al limite")
                if round_importo(investimento.importo) > conto["saldo"]:
                    raise SaldoInsufficienteError(f"Saldo insufficiente: {conto['saldo']:.2f} euro")
                investimento.eseguito = True
                self._inserisci_investimento_cursore(cursore, investimento)
                cursore.execute("update conto_corrente set saldo = saldo - %s where id_conto = %s", (round_importo(investimento.importo), investimento.conto.id_conto))
            self.connessione.commit()
        except Exception as errore:
            self.connessione.rollback()
            if isinstance(errore, psycopg.Error): raise DatabaseError(f"Errore PostgreSQL: {errore}") from errore
            raise

    def delibera_finanziamento(self, id_operazione, nuovo_stato, codice_filiale):
        if nuovo_stato not in (StatoRichiesta.APPROVATA, StatoRichiesta.RIFIUTATA):
            raise ValueError("Lo stato richiesto non e' valido")
        try:
            with self.connessione.cursor() as cursore:
                cursore.execute("select f.id_conto, f.importo, f.stato, f.eseguito from finanziamento f join cliente cl on cl.numero_cliente = f.numero_cliente where f.id_operazione = %s and cl.codice_filiale = %s for update of f", (id_operazione, codice_filiale))
                fin = cursore.fetchone()
                if fin is None: raise OperazioneNonConsentitaError("Finanziamento non trovato")
                if fin["stato"] != "Richiesta" or fin["eseguito"]:
                    raise OperazioneNonConsentitaError("Il finanziamento e' gia stato deliberato")
                if nuovo_stato == StatoRichiesta.APPROVATA:
                    self._conto_bloccato(cursore, fin["id_conto"], codice_filiale)
                    cursore.execute("update conto_corrente set saldo = saldo + %s where id_conto = %s", (fin["importo"], fin["id_conto"]))
                cursore.execute("update finanziamento set stato = %s, eseguito = %s where id_operazione = %s", (nuovo_stato.value, nuovo_stato == StatoRichiesta.APPROVATA, id_operazione))
            self.connessione.commit()
        except Exception as errore:
            self.connessione.rollback()
            if isinstance(errore, psycopg.Error): raise DatabaseError(f"Errore PostgreSQL: {errore}") from errore
            raise

    # ====================
    # IMPORTAZIONE PER CSV
    # ====================

    def importa_righe(self, entita, righe, codice_filiale):
        configurazioni = {
            "filiale": ("filiale", "codice_filiale"), "dipendenti": ("dipendente", "id_dipendente"),
            "atm": ("atm", "codice_atm"), "clienti": ("cliente", "numero_cliente"),
            "conti": ("conto_corrente", "id_conto"), "movimenti": ("movimento", "id_operazione"),
            "finanziamenti": ("finanziamento", "id_operazione"), "investimenti": ("investimento", "id_operazione")
        }
        if entita not in configurazioni: raise ValueError("Entita' CSV non riconosciuta")
        tabella, chiave = configurazioni[entita]
        colonne = {
            "filiale": self.COLONNE_FILIALE, "dipendenti": self.COLONNE_DIPENDENTI, "atm": self.COLONNE_ATM,
            "clienti": self.COLONNE_CLIENTI, "conti": self.COLONNE_CONTI, "movimenti": self.COLONNE_MOVIMENTI,
            "finanziamenti": self.COLONNE_FINANZIAMENTI, "investimenti": self.COLONNE_INVESTIMENTI
        }[entita]
        # Il campo filiale dei CSV dipendenti/clienti e' implicito nella filiale selezionata.
        if entita == "filiale" and any(riga["codice_filiale"].upper() != codice_filiale for riga in righe):
            raise OperazioneNonConsentitaError("Il file CSV contiene una filiale diversa")
        totale = 0
        try:
            with self.connessione.cursor() as cursore:
                for riga in righe:
                    valori = dict(riga)
                    if entita == "filiale": valori["codice_filiale"] = valori["codice_filiale"].strip().upper()
                    if entita == "atm": valori["codice_filiale"] = valori["codice_filiale"].strip().upper()
                    if entita == "filiale": valori["nome"] = valori.pop("nome_filiale")
                    if entita in ("dipendenti", "clienti"): valori["codice_filiale"] = codice_filiale
                    if entita == "atm" and valori["codice_filiale"].upper() != codice_filiale:
                        raise OperazioneNonConsentitaError("Il CSV contiene un ATM di un'altra filiale")
                    if entita == "dipendenti":
                        if valori["ruolo"] not in ("Gestore", "Specialista", "Direttore", "AddettoAllaSicurezza"):
                            raise ValueError("Ruolo dipendente non valido")
                        if valori.get("specializzazione") == "": valori["specializzazione"] = None
                        if not valori.get("liv_autorizzazione"): valori["liv_autorizzazione"] = None
                    if entita == "movimenti" and valori.get("tipo_versamento") == "": valori["tipo_versamento"] = None
                    if entita == "filiale":
                        cursore.execute("select codice_filiale, direttore_id from filiale where codice_filiale = %s", (codice_filiale,))
                        fil = cursore.fetchone()
                        if fil is None: raise OperazioneNonConsentitaError("Creare prima la filiale dal menu")
                        if fil["direttore_id"] != valori["direttore_id"]: raise OperazioneNonConsentitaError("Il CSV non puo' cambiare il direttore della filiale")
                    if entita not in ("filiale",):
                        if entita in ("dipendenti", "clienti", "atm"):
                            cursore.execute(f"select codice_filiale from {tabella} where {chiave} = %s", (valori[chiave],))
                            esistente = cursore.fetchone()
                            if esistente and esistente["codice_filiale"] != codice_filiale:
                                raise OperazioneNonConsentitaError("Il record appartiene a un'altra filiale")
                        elif entita == "conti":
                            cursore.execute("select codice_filiale from cliente where numero_cliente = %s", (valori["numero_cliente"],))
                            cliente = cursore.fetchone()
                            if cliente is None or cliente["codice_filiale"] != codice_filiale: raise OperazioneNonConsentitaError("Cliente del conto non presente nella filiale")
                            cursore.execute("select cl.codice_filiale from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where c.id_conto = %s", (valori[chiave],))
                            esistente = cursore.fetchone()
                            if esistente and esistente["codice_filiale"] != codice_filiale: raise OperazioneNonConsentitaError("Il conto appartiene a un'altra filiale")
                        else:
                            cursore.execute("select cl.codice_filiale from conto_corrente c join cliente cl on cl.numero_cliente = c.numero_cliente where c.id_conto = %s", (valori["id_conto"],))
                            conto = cursore.fetchone()
                            if conto is None or conto["codice_filiale"] != codice_filiale: raise OperazioneNonConsentitaError("Il conto dell'operazione non appartiene alla filiale")
                            if entita in ("finanziamenti", "investimenti"):
                                cursore.execute("select numero_cliente from conto_corrente where id_conto = %s", (valori["id_conto"],))
                                if cursore.fetchone()["numero_cliente"] != valori["numero_cliente"]: raise OperazioneNonConsentitaError("Cliente e conto dell'operazione non corrispondono")
                    cursore.execute(sql.SQL("select * from {} where {} = %s").format(sql.Identifier(tabella), sql.Identifier(chiave)), (valori[chiave],))
                    precedente = cursore.fetchone()
                    transazione = entita in ("movimenti", "finanziamenti", "investimenti")
                    if transazione:
                        if precedente is not None:
                            if not equivalenti(precedente, valori): raise OperazioneNonConsentitaError("Il CSV tenta di modificare un'operazione storica: importazione annullata")
                            continue
                        self._controlla_id_operazione(cursore, valori["id_operazione"])
                    if entita == "conti" and precedente is not None:
                        if precedente["numero_cliente"] != valori["numero_cliente"]: raise OperazioneNonConsentitaError("Non e' consentito cambiare intestatario a un conto tramite CSV")
                        valori.pop("saldo")  # Non sovrascrivere il saldo del database.
                    if entita == "filiale": valori.pop("direttore_id")
                    keys = list(valori)
                    query = sql.SQL("insert into {} ({}) values ({}) on conflict ({}) do update set {}").format(
                        sql.Identifier(tabella), sql.SQL(", ").join(map(sql.Identifier, keys)), sql.SQL(", ").join([sql.Placeholder()] * len(keys)),
                        sql.Identifier(chiave), sql.SQL(", ").join(sql.SQL("{} = excluded.{}").format(sql.Identifier(k), sql.Identifier(k)) for k in keys if k != chiave))
                    cursore.execute(query, tuple(valori.values()))
                    totale += 1
            codice_precedente = self.codice_filiale
            try:
                self.codice_filiale = codice_filiale
                self.ricostruisci(self.leggi())
            finally:
                self.codice_filiale = codice_precedente
            self.connessione.commit()
            return totale
        except Exception as errore:
            self.connessione.rollback()
            if isinstance(errore, psycopg.Error): raise DatabaseError(f"Errore importazione CSV: {errore}") from errore
            raise
