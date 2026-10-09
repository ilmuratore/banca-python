-- Schema non distruttivo: eseguire solo su database vuoto.
CREATE TABLE filiale(
    codice_filiale VARCHAR(20) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    citta VARCHAR(100) NOT NULL,
    provincia VARCHAR(2) NOT NULL,
    regione VARCHAR(100) NOT NULL,
    data_apertura DATE NOT NULL CHECK (data_apertura <= CURRENT_DATE),
    direttore_id INTEGER UNIQUE
);

CREATE TABLE dipendente(
    id_dipendente INTEGER PRIMARY KEY,
    codice_filiale VARCHAR(20) NOT NULL,
    ruolo VARCHAR(30) NOT NULL CHECK(ruolo IN('Gestore', 'Specialista', 'Direttore', 'AddettoAllaSicurezza')),
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    codice_fiscale VARCHAR(16) NOT NULL UNIQUE,
    recapito VARCHAR(150) NOT NULL,
    data_assunzione DATE NOT NULL CHECK (data_assunzione <= CURRENT_DATE),
    specializzazione VARCHAR(20),  
    liv_autorizzazione INTEGER,
    CONSTRAINT fk_dipendente_filiale FOREIGN KEY (codice_filiale) REFERENCES filiale(codice_filiale) ON DELETE CASCADE,
    CONSTRAINT ck_dipendente_specializzazione CHECK (
        (ruolo IN('Specialista', 'Direttore') AND specializzazione IN('Prestiti', 'Mutui', 'Investimenti'))
        OR
        (ruolo IN('Gestore', 'AddettoAllaSicurezza') AND specializzazione IS NULL)
    ),
    CONSTRAINT ck_direttore_livello CHECK(
        (ruolo = 'Direttore' AND liv_autorizzazione IS NOT NULL AND liv_autorizzazione > 0)
        OR
        (ruolo <> 'Direttore' AND liv_autorizzazione IS NULL)
    )
);

ALTER TABLE filiale
ADD CONSTRAINT fk_filiale_direttore
FOREIGN KEY (direttore_id) REFERENCES dipendente(id_dipendente) ON DELETE SET NULL;

CREATE TABLE atm(
    codice_atm VARCHAR(30) PRIMARY KEY,
    codice_filiale VARCHAR(20) NOT NULL,
    stato VARCHAR(20) NOT NULL CHECK (stato IN('Attivo', 'Manutenzione', 'Fuori servizio')),
    data_installazione DATE NOT NULL CHECK (data_installazione <= CURRENT_DATE),
    CONSTRAINT fk_atm_filiale FOREIGN KEY (codice_filiale) REFERENCES filiale(codice_filiale) ON DELETE CASCADE
);

CREATE TABLE cliente(
    numero_cliente INTEGER PRIMARY KEY,
    codice_filiale VARCHAR(20) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    codice_fiscale VARCHAR(16) NOT NULL UNIQUE,
    recapito VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    data_nascita DATE NOT NULL CHECK (data_nascita <= CURRENT_DATE),
    citta varchar(100) NOT NULL,
    data_registrazione DATE NOT NULL CHECK (data_registrazione <= CURRENT_DATE),
    segmento VARCHAR(20) NOT NULL CHECK (segmento IN ('Standard' , 'Premium' , 'Business')),
    CONSTRAINT fk_cliente_filiale FOREIGN KEY (codice_filiale) REFERENCES filiale(codice_filiale) ON DELETE CASCADE
);

CREATE TABLE conto_corrente(
    id_conto INTEGER PRIMARY KEY,
    iban VARCHAR(34) NOT NULL UNIQUE,
    numero_cliente INTEGER NOT NULL,
    tipo_conto VARCHAR(20) NOT NULL CHECK (tipo_conto IN ('Corrente', 'Risparmio')),
    data_apertura DATE NOT NULL CHECK (data_apertura <= CURRENT_DATE),
    stato VARCHAR(20) NOT NULL CHECK (stato IN ('Attivo', 'Bloccato', 'Chiuso')),
    saldo NUMERIC(15, 2) NOT NULL DEFAULT 0 CHECK (saldo >= 0),
    CONSTRAINT fk_conto_cliente FOREIGN KEY (numero_cliente) REFERENCES cliente(numero_cliente) ON DELETE CASCADE
);

CREATE TABLE movimento(
    id_operazione INTEGER PRIMARY KEY,
    id_conto INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Versamento' , 'Prelievo')),
    data_operazione DATE NOT NULL CHECK (data_operazione <= CURRENT_DATE),
    importo NUMERIC(15,2) NOT NULL CHECK (importo > 0 AND importo < 1000000),
    canale VARCHAR(20) NOT NULL CHECK (canale IN ('Filiale', 'ATM' , 'Online')),
    causale VARCHAR(200) NOT NULL,
    tipo_versamento VARCHAR(20),
    CONSTRAINT fk_movimento_conto FOREIGN KEY (id_conto) REFERENCES conto_corrente(id_conto) ON DELETE CASCADE,
    CONSTRAINT ck_tipo_versamento CHECK(
        (tipo = 'Versamento' AND  tipo_versamento IN('Contanti', 'Assegno'))
        OR
        (tipo = 'Prelievo' AND tipo_versamento IS NULL)
    )
);

CREATE TABLE finanziamento(
    id_operazione INTEGER PRIMARY KEY,
    id_conto INTEGER NOT NULL,
    numero_cliente INTEGER NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Prestito', 'Mutuo')),
    data_operazione DATE NOT NULL CHECK (data_operazione <= CURRENT_DATE),
    importo NUMERIC(15,2) NOT NULL CHECK (importo > 0 AND importo < 1000000),
    durata_mesi INTEGER NOT NULL CHECK (durata_mesi BETWEEN 3 AND 480),
    tasso NUMERIC(5,2) NOT NULL CHECK (tasso BETWEEN 0 AND 30),
    stato VARCHAR(20) NOT NULL CHECK (stato IN ('Richiesta' , 'Approvata' , 'Rifiutata')),
    finalita VARCHAR(200) NOT NULL,
    eseguito BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_finanziamento_conto FOREIGN KEY (id_conto) REFERENCES conto_corrente(id_conto) ON DELETE CASCADE,
    CONSTRAINT fk_finanziamento_cliente FOREIGN KEY (numero_cliente) REFERENCES cliente(numero_cliente) ON DELETE CASCADE
);

CREATE TABLE investimento(
    id_operazione INTEGER PRIMARY KEY,
    id_conto INTEGER NOT NULL,
    numero_cliente INTEGER NOT NULL,
    data_operazione DATE NOT NULL CHECK (data_operazione <= CURRENT_DATE),
    importo NUMERIC(15,2) NOT NULL CHECK (importo > 0 AND importo < 100000),
    prodotto VARCHAR(150) NOT NULL,
    profilo_rischio VARCHAR(20) NOT NULL CHECK (profilo_rischio IN ('Basso', 'Medio', 'Alto')),
    rendimento_atteso NUMERIC(6,2) NOT NULL CHECK (rendimento_atteso BETWEEN -100 AND 100),
    stato VARCHAR(20) NOT NULL CHECK (stato IN ('Attivo' , 'Chiuso')),
    eseguito BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_investimento_conto FOREIGN KEY (id_conto) REFERENCES conto_corrente(id_conto) ON DELETE CASCADE,
    CONSTRAINT fk_investimento_cliente FOREIGN KEY (numero_cliente) REFERENCES cliente(numero_cliente) ON DELETE CASCADE
);

CREATE INDEX idx_dipendente_filiale ON dipendente(codice_filiale);
CREATE INDEX idx_cliente_filiale ON cliente(codice_filiale);
CREATE INDEX idx_conto_cliente ON conto_corrente(numero_cliente);
CREATE INDEX idx_movimento_conto ON movimento(id_conto);
CREATE INDEX idx_movimento_data ON movimento(data_operazione);
CREATE INDEX idx_finanziamento_cliente ON finanziamento(numero_cliente);
CREATE INDEX idx_finanziamento_stato ON finanziamento(stato);
CREATE INDEX idx_investimento_cliente ON investimento(numero_cliente);




