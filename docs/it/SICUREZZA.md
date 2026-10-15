# Sicurezza

> **Lingua:** Italiano · [English](../../SECURITY.md) · [Torna al LEGGIMI](../../LEGGIMI.md)

## Destinazione del progetto

Banca Python è una **simulazione per apprendimento e portfolio**. Non è adatta alla gestione di dati personali sensibili, denaro reale, pagamenti o operazioni bancarie regolamentate.

Non implementa autenticazione, autorizzazioni reali per utente, cifratura dei dati finanziari memorizzati, contabilità certificata, antifrode o conformità normativa. Non va presentata come piattaforma bancaria sicura.

## Buone pratiche

- Utilizzare esclusivamente dati **fittizi** e un database PostgreSQL di prova separato.
- Configurare le credenziali tramite variabili d'ambiente; non committare password reali o file `.env`.
- L'eventuale servizio Docker Compose espone PostgreSQL solo su `127.0.0.1` e usa credenziali dimostrative. Sostituirle per qualsiasi utilizzo diverso da un test locale eliminabile.
- Prima di importare CSV, valutare il backup e possibili conflitti tra identificativi.
- Non esporre PostgreSQL su Internet.

## Segnalazioni

Evitare di pubblicare vulnerabilità sfruttabili o dati sensibili nelle issue pubbliche. Contattare il manutentore attraverso il suo [profilo GitHub](https://github.com/ilmuratore) per concordare una segnalazione privata. Non è previsto un tempo di risposta garantito.

## Versioni supportate

È mantenuta soltanto la versione più recente del ramo `main`; non sono previste patch retroattive o assistenza di produzione.
