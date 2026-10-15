# Contribuire

> **Lingua:** Italiano · [English](../../CONTRIBUTING.md) · [Torna al LEGGIMI](../../LEGGIMI.md)

Il progetto è una simulazione bancaria personale, utilizzata come portfolio. Sono benvenuti contributi limitati e verificabili su correttezza, test, documentazione e facilità d'uso.

## Preparazione

Seguire la [guida di installazione](../../LEGGIMI.md#installazione), poi avviare:

```bash
python -m unittest discover -s tests -v
python scripts/check_docs_links.py
```

I test automatici non richiedono PostgreSQL. Le modifiche al repository SQL o alle operazioni economiche devono essere verificate anche su un database PostgreSQL temporaneo, come indicato nella [guida allo sviluppo](SVILUPPO.md).

## Pull request

- Lavorare su una branch dedicata e mantenere una PR per argomento.
- Descrivere le modifiche e come sono state testate.
- Aggiornare i test quando cambia il comportamento.
- Aggiornare le versioni inglese e italiana dei documenti modificati.
- Non committare password, dati reali, CSV esportati o grafici generati.
- Mantenere PostgreSQL come unica fonte dei dati; il CSV resta solo un import/export esplicito.

Il codice usa principalmente identificatori di dominio in italiano: rispettare le convenzioni già presenti.
