# Security policy

> **Language:** English · [Italiano](docs/it/SICUREZZA.md)

## Scope

Banca Python is an **educational/portfolio banking simulation**. It is **not designed for production banking, sensitive personal data, payment processing or regulated financial activities**.

The application intentionally does not implement authentication, per-user authorization, encryption of stored financial data, audit-grade accounting, fraud detection or regulatory compliance. Do not present it as a secure banking platform.

## Safe use

- Run only with **fictional** data and a dedicated, disposable PostgreSQL database.
- Set PostgreSQL credentials using environment variables. Never commit real passwords, `.env` files, or server connection strings.
- The optional Docker Compose service binds only to `127.0.0.1` and uses demo-only credentials. Change them for any use beyond a disposable local demo.
- Review backup and ID-conflict risks before importing CSV data.
- Do not expose the PostgreSQL service to the public internet.

## Reporting a vulnerability

Avoid publishing exploit details or sensitive information in a public issue. Contact the repository maintainer through their [GitHub profile](https://github.com/ilmuratore) to arrange a private report. There is no guaranteed response time or security patch SLA for this personal project.

## Supported versions

Only the latest revision on `main` is actively maintained; no production support or backport policy is offered.
