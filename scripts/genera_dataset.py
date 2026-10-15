"""Dataset didattici sintetici per il progetto Banca (CSV importabili dal menu)."""
import argparse
import csv
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

NOMI = ('Luca', 'Marco', 'Giulia', 'Sara', 'Paolo', 'Anna', 'Matteo', 'Elena', 'Davide', 'Chiara', 'Francesco', 'Martina', 'Andrea', 'Valentina', 'Simone', 'Federica', 'Alessandro', 'Laura', 'Stefano', 'Silvia', 'Giorgio', 'Alice', 'Roberto', 'Beatrice', 'Filippo', 'Marta', 'Nicola', 'Sofia', 'Pietro', 'Irene')
COGNOMI = ('Rossi', 'Bianchi', 'Esposito', 'Romano', 'Colombo', 'Ricci', 'Marino', 'Greco', 'Bruno', 'Gallo', 'Conti', 'De Luca', 'Moretti', 'Barbieri', 'Fontana', 'Santoro', 'Ferrari', 'Caruso', 'Costa', 'Mancini', 'Vitale', 'Rizzo', 'Ferri', 'Longo', 'Serra', 'Leone', 'Martini', 'Gentile', 'Palmieri', 'Fiore')
CITTA = ('Roma', 'Milano', 'Napoli', 'Torino', 'Bologna', 'Firenze', 'Genova', 'Bari', 'Palermo', 'Catania', 'Venezia', 'Verona', 'Perugia', 'Pisa', 'Salerno', 'Parma', 'Padova', 'Lecce', 'Livorno', 'Siena')
COLONNE = {
    'dipendenti': ('id_dipendente', 'ruolo', 'nome', 'cognome', 'codice_fiscale', 'recapito', 'data_assunzione', 'specializzazione', 'liv_autorizzazione'),
    'atm': ('codice_atm', 'codice_filiale', 'stato', 'data_installazione'),
    'clienti': ('numero_cliente', 'nome', 'cognome', 'codice_fiscale', 'recapito', 'email', 'data_nascita', 'citta', 'data_registrazione', 'segmento'),
    'conti': ('id_conto', 'iban', 'numero_cliente', 'tipo_conto', 'data_apertura', 'stato', 'saldo'),
    'movimenti': ('id_operazione', 'id_conto', 'tipo', 'data_operazione', 'importo', 'canale', 'causale', 'tipo_versamento'),
    'finanziamenti': ('id_operazione', 'id_conto', 'numero_cliente', 'tipo', 'data_operazione', 'importo', 'durata_mesi', 'tasso', 'stato', 'finalita', 'eseguito'),
    'investimenti': ('id_operazione', 'id_conto', 'numero_cliente', 'data_operazione', 'importo', 'prodotto', 'profilo_rischio', 'rendimento_atteso', 'stato', 'eseguito'),
}


def data_csv(giorno):
    return giorno.strftime('%d/%m/%Y')


def euro(valore):
    return f'{valore:.2f}'.replace('.', ',')


def iban_italiano(conto):
    bban = f'X0306909606{conto:012d}'
    convertito = ''.join(str(int(ch, 36)) if ch.isalpha() else ch for ch in bban + 'IT00')
    controllo = 98 - int(convertito) % 97
    return f'IT{controllo:02d}{bban}'


def scrivi_csv(cartella, entita, righe):
    percorso = cartella / f'{entita}.csv'
    with percorso.open('w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, delimiter=';', fieldnames=COLONNE[entita])
        writer.writeheader()
        writer.writerows(righe)
    return percorso


def genera(filiale='FIL001', out='data/csv', n=200, base_clienti=10001, base_dipendenti=20001, base_conti=30001, base_operazioni=40001, seed=20261009):
    filiale = filiale.strip().upper()
    if not filiale or len(filiale) > 20: raise ValueError('Codice filiale non valido (max 20 caratteri)')
    if n < 4 or n > 999: raise ValueError('Numero record valido da 4 a 999')
    if min(base_clienti, base_dipendenti, base_conti, base_operazioni) < 1: raise ValueError('Le basi degli identificativi devono essere positive')
    if base_operazioni + 2 * 1000 + n > 2147483647: raise ValueError('Identificativi operazioni troppo grandi')
    rng = random.Random(seed)
    folder = Path(out) / filiale
    folder.mkdir(parents=True, exist_ok=True)
    righe = {entita: [] for entita in COLONNE}
    accounts = []

    for i in range(n):
        nome, cognome = rng.choice(NOMI), rng.choice(COGNOMI)
        ruolo = ('Gestore', 'Specialista', 'AddettoAllaSicurezza')[i % 10 // 4] if i % 10 < 8 else 'AddettoAllaSicurezza'
        spec = ('Prestiti', 'Mutui', 'Investimenti')[i % 3] if ruolo == 'Specialista' else ''
        righe['dipendenti'].append({
            'id_dipendente': base_dipendenti + i, 'ruolo': ruolo, 'nome': nome, 'cognome': cognome,
            'codice_fiscale': f'TESTDP{i + 1:010d}', 'recapito': f'000000{i + 1:06d}',
            'data_assunzione': data_csv(date(2019, 1, 1) + timedelta(days=rng.randint(0, 2400))),
            'specializzazione': spec, 'liv_autorizzazione': ''
        })
        righe['atm'].append({
            'codice_atm': f'ATM-DEMO-{i + 1:04d}', 'codice_filiale': filiale,
            'stato': ('Attivo' if i % 10 < 8 else ('Manutenzione' if i % 10 == 8 else 'Fuori servizio')),
            'data_installazione': data_csv(date(2022, 1, 1) + timedelta(days=rng.randint(0, 1150)))
        })
        cliente_id, conto_id = base_clienti + i, base_conti + i
        nascita = date(rng.randint(1960, 2003), rng.randint(1, 12), rng.randint(1, 28))
        righe['clienti'].append({
            'numero_cliente': cliente_id, 'nome': rng.choice(NOMI), 'cognome': rng.choice(COGNOMI),
            'codice_fiscale': f'TESTCL{i + 1:010d}', 'recapito': f'000001{i + 1:06d}',
            'email': f'cliente.demo.{i + 1:04d}@example.com', 'data_nascita': data_csv(nascita),
            'citta': rng.choice(CITTA), 'data_registrazione': data_csv(date(2024, 3, 1) + timedelta(days=rng.randint(0, 300))),
            'segmento': ('Standard', 'Premium', 'Business')[i % 3]
        })
        righe['conti'].append({
            'id_conto': conto_id, 'iban': iban_italiano(conto_id), 'numero_cliente': cliente_id,
            'tipo_conto': 'Corrente' if i % 4 else 'Risparmio',
            'data_apertura': data_csv(date(2025, 4, 1) + timedelta(days=rng.randint(0, 170))),
            'stato': 'Attivo', 'saldo': '0,00'
        })
        accounts.append((cliente_id, conto_id))

    # 200 movimenti: primi 3/4 versamenti; ultimo 1/4 prelievi su conti gia finanziati.
    depositi = (n * 3) // 4
    saldi = {conto: Decimal('0.00') for _, conto in accounts}
    for i in range(n):
        if i < depositi:
            conto = accounts[i][1]
            importo = Decimal(rng.randint(2300, 4800)) + Decimal(rng.randint(0, 99)) / 100
            saldi[conto] += importo
            tipo = 'Versamento'
            versamento = 'Contanti' if i % 2 else 'Assegno'
            canale = 'Filiale' if i % 3 else 'ATM'
            causale = ('Versamento risparmi', 'Accredito disponibilita', 'Versamento da sportello')[i % 3]
            giorno = date(2026, 2, 1) + timedelta(days=i % 25)
        else:
            conto = accounts[(i - depositi) % depositi][1]
            importo = Decimal(rng.randint(100, 350)) + Decimal(rng.randint(0, 99)) / 100
            assert saldi[conto] >= importo
            saldi[conto] -= importo
            tipo, versamento, canale = 'Prelievo', '', ('ATM' if i % 2 else 'Filiale')
            causale = 'Prelievo contanti'
            giorno = date(2026, 5, 1) + timedelta(days=i % 25)
        righe['movimenti'].append({
            'id_operazione': base_operazioni + i, 'id_conto': conto, 'tipo': tipo, 'data_operazione': data_csv(giorno),
            'importo': euro(importo), 'canale': canale, 'causale': causale, 'tipo_versamento': versamento
        })

    # Il 25% circa dei finanziamenti viene approvato e alimenta conti senza versamenti.
    for i, (cliente, conto) in enumerate(accounts):
        if i >= depositi:
            stato, eseguito = 'Approvata', '1'
        else:
            stato, eseguito = ('Richiesta', '0') if i % 2 else ('Rifiutata', '0')
        tipo = 'Prestito' if i % 3 else 'Mutuo'
        mesi = (24, 36, 48, 60)[i % 4] if tipo == 'Prestito' else (120, 180, 240, 300)[i % 4]
        importo = Decimal(rng.randint(12000, 25000)) + Decimal(rng.randint(0, 99)) / 100
        if eseguito == '1': saldi[conto] += importo
        righe['finanziamenti'].append({
            'id_operazione': base_operazioni + 1000 + i, 'id_conto': conto, 'numero_cliente': cliente, 'tipo': tipo,
            'data_operazione': data_csv(date(2026, 6, 1) + timedelta(days=i % 27)),
            'importo': euro(importo), 'durata_mesi': mesi,
            'tasso': euro(Decimal('2.50') + Decimal((i * 13) % 85) / 10),
            'stato': stato, 'finalita': ('Liquidita personale' if tipo == 'Prestito' else 'Acquisto immobile'),
            'eseguito': eseguito
        })

    for i, (cliente, conto) in enumerate(accounts):
        importo = Decimal(rng.randint(160, 850)) + Decimal(rng.randint(0, 99)) / 100
        assert saldi[conto] >= importo, ('Saldo insufficiente in creazione dataset', conto)
        saldi[conto] -= importo
        profilo = ('Basso', 'Medio', 'Alto')[i % 3]
        prodotto = ('Deposito vincolato', 'Obbligazioni', 'Fondo bilanciato', 'Fondo azionario')[i % 4]
        righe['investimenti'].append({
            'id_operazione': base_operazioni + 2000 + i, 'id_conto': conto, 'numero_cliente': cliente,
            'data_operazione': data_csv(date(2026, 9, 1) + timedelta(days=i % 27)),
            'importo': euro(importo), 'prodotto': prodotto, 'profilo_rischio': profilo,
            'rendimento_atteso': euro(Decimal('1.25') + Decimal((i * 7) % 74) / 10),
            'stato': 'Attivo' if i % 10 != 0 else 'Chiuso', 'eseguito': '1'
        })

    for entita, record in righe.items():
        scrivi_csv(folder, entita, record)
        print(f'{entita:<17} {len(record):>4} record -> {folder / (entita + ".csv")}')
    print(f'Fondi simulati dopo tutte le importazioni: {euro(sum(saldi.values()))} euro')
    return righe


def main():
    parser = argparse.ArgumentParser(description='Genera CSV coerenti per la banca PostgreSQL')
    parser.add_argument('--filiale', default='FIL001', help='Codice filiale esistente nel DB')
    parser.add_argument('--out', default='data/csv', help='Cartella base, prima della sottocartella filiale')
    parser.add_argument('--record', type=int, default=200, help='Record per CSV (default 200)')
    parser.add_argument('--base-clienti', type=int, default=10001)
    parser.add_argument('--base-dipendenti', type=int, default=20001)
    parser.add_argument('--base-conti', type=int, default=30001)
    parser.add_argument('--base-operazioni', type=int, default=40001)
    args = parser.parse_args()
    genera(args.filiale, args.out, args.record, args.base_clienti, args.base_dipendenti, args.base_conti, args.base_operazioni)


if __name__ == '__main__':
    main()
