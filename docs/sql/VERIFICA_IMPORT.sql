-- Query di sola lettura per DBeaver; non modificano il database.
-- Per filtrare una filiale particolare cambiare 'FIL001' sotto.

-- Conteggio dei dati importati per la filiale.
select 'dipendenti' as entita, count(*) as totale from dipendente where codice_filiale = 'FIL001'
union all
select 'atm', count(*) from atm where codice_filiale = 'FIL001'
union all
select 'clienti', count(*) from cliente where codice_filiale = 'FIL001'
union all
select 'conti', count(*) from conto_corrente cc join cliente cl on cl.numero_cliente = cc.numero_cliente where cl.codice_filiale = 'FIL001'
union all
select 'movimenti', count(*) from movimento m join conto_corrente cc on cc.id_conto = m.id_conto join cliente cl on cl.numero_cliente = cc.numero_cliente where cl.codice_filiale = 'FIL001'
union all
select 'finanziamenti', count(*) from finanziamento f join cliente cl on cl.numero_cliente = f.numero_cliente where cl.codice_filiale = 'FIL001'
union all
select 'investimenti', count(*) from investimento i join cliente cl on cl.numero_cliente = i.numero_cliente where cl.codice_filiale = 'FIL001';

-- Un conto con proprietario e saldo aggiornato da PostgreSQL.
select cl.numero_cliente, cl.nome, cl.cognome, cc.id_conto, cc.iban, cc.saldo
from conto_corrente cc
join cliente cl on cl.numero_cliente = cc.numero_cliente
where cl.codice_filiale = 'FIL001'
order by cc.id_conto;

-- Tipologia e numero di movimenti.
select m.tipo, count(*) as operazioni, sum(m.importo) as totale_importi
from movimento m
join conto_corrente cc on cc.id_conto = m.id_conto
join cliente cl on cl.numero_cliente = cc.numero_cliente
where cl.codice_filiale = 'FIL001'
group by m.tipo order by m.tipo;

-- Stati dei finanziamenti.
select f.stato, count(*) as numero, sum(f.importo) as totale_importi
from finanziamento f
join cliente cl on cl.numero_cliente = f.numero_cliente
where cl.codice_filiale = 'FIL001'
group by f.stato order by f.stato;

-- Conti importati con saldo negativo (atteso: zero righe).
select cc.id_conto, cc.saldo from conto_corrente cc
join cliente cl on cl.numero_cliente = cc.numero_cliente
where cl.codice_filiale = 'FIL001' and cc.saldo < 0;
