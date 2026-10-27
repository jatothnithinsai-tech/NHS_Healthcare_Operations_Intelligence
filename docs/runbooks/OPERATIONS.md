# Local operations and monthly refresh

## Prerequisites and one-command execution
Python 3.11+, PostgreSQL 14+ and a DATABASE_URL for a dedicated `nhs_operations` database. Windows native Excel automation requires installed Excel and an interactive desktop. Desktop Power BI validation requires Power BI Desktop. No paid service is needed.

Create `.venv`, install `requirements.txt`, start the isolated cluster with `scripts/start_postgres.ps1` (defaults to PostgreSQL 18 binaries and loopback port 55473), then run `.venv\Scripts\python.exe -m src.pipeline --refresh --reports`. The refresh flag checks official catalogues and revalidates revised files; an unchanged publication is a normal no-op. Without `--refresh`, retained checksums are verified locally. Report construction can be run separately as `python -m src.reporting.build`.

Run native workbook creation with `python -m scripts.build_excel`. Run `python -m scripts.build_powerbi` after exporting data. Power BI's DataRoot parameter must point to the local `powerbi/data` directory. Use `python -m pytest` for unit tests and `NHS_INTEGRATION=1` for authentic-data/database tests. CI uses a temporary PostgreSQL service and official public downloads.

## Refresh stages and failure recovery
1. Discover current official links and compare reporting-month coverage.
2. Download new/revised payloads with timeouts/retries and checksum verification.
3. Parse/version changed files, profile and validate embedded Period and totals.
4. Replace changed dataset/month in one PostgreSQL transaction; retain previous source files.
5. Rebuild SQL results, statistics and management evidence; run regression checks.
6. Rebuild Excel and exported model CSVs. Refresh the Power BI model separately.

If a new schema is rejected, keep the last validated warehouse, inspect the retained file and profile, fix the parser and increment parser_version. A failed file transaction is rolled back. Interrupted runs remain visible in audit; inspect logs before retry. Do not delete raw versions to conceal failures. A missing publisher month is a coverage failure, never a manufactured zero row.

Windows Task Scheduler registration is provided separately. It checks monthly publications; it is not a cloud scheduler. Database updates, workbook regeneration and Power BI model refresh are separate operations. Published monthly observations are not genuine real-time reporting.

## Security
Credentials live only in ignored `.env`; project database listens on 127.0.0.1 and uses SCRAM authentication. Do not export credentials into report metadata, Git or screenshots. Raw files are public aggregates but stay local for repository size; the reproducible manifest is committed. Do not reuse another project's database or kill unrelated desktop processes.
