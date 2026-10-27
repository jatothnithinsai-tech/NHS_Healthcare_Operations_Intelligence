from __future__ import annotations
import os
import uuid
import pandas as pd
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from dotenv import load_dotenv
from src.ingestion.acquire import ROOT


def connect(database: str | None = None):
    load_dotenv(ROOT / ".env")
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required; see .env.example")
    if database:
        url = url.rsplit("/", 1)[0] + "/" + database
    return psycopg.connect(url)


def initialise():
    with connect("postgres") as conn:
        conn.autocommit = True
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname='nhs_operations'").fetchone():
            conn.execute("CREATE DATABASE nhs_operations")
    with connect() as conn:
        for folder in ("schemas", "views"):
            for p in sorted((ROOT / "sql" / folder).glob("*.sql")):
                conn.execute(p.read_text(encoding="utf-8"))


def start_run() -> str:
    run_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute("INSERT INTO audit.pipeline_run(run_id,started_at,status) VALUES (%s,now(),'running')", (run_id,))
    return run_id


def finish_run(run_id: str, status: str, summary: dict):
    with connect() as conn:
        conn.execute("UPDATE audit.pipeline_run SET finished_at=now(),status=%s,summary=%s WHERE run_id=%s", (status, Jsonb(summary), run_id))


def load_frame(frame: pd.DataFrame, source: dict, parser_version: str) -> bool:
    domain, month = source["dataset"], source["reporting_month"]
    with connect() as conn:
        prior = conn.execute("SELECT sha256,parser_version FROM audit.loaded_source WHERE dataset=%s AND month=%s", (domain, month)).fetchone()
        conn.execute("""INSERT INTO raw.source_file VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT(sha256) DO UPDATE SET publication_date=coalesce(EXCLUDED.publication_date,source_file.publication_date),metadata=EXCLUDED.metadata""", (source["sha256"], domain, month, source["url"], source.get("publication_date"), source["retrieved_at"], source["bytes"], Jsonb(source)))
        if prior == (source["sha256"], parser_version):
            return False
        providers = frame[["provider_code", "provider_name"]].drop_duplicates()
        for code, name in providers.itertuples(index=False, name=None):
            conn.execute("""INSERT INTO analytics.dim_provider(provider_code,provider_name,name_as_of) VALUES (%s,%s,%s)
             ON CONFLICT(provider_code) DO UPDATE SET provider_name=coalesce(EXCLUDED.provider_name,dim_provider.provider_name),name_as_of=EXCLUDED.name_as_of
             WHERE EXCLUDED.name_as_of>=dim_provider.name_as_of""", (code, None if pd.isna(name) else name, month))
        if domain != "ae":
            frame = frame.copy()
            frame["parent_code"] = frame["parent_code"].fillna("UNREPORTED")
            parents = frame[["parent_code", "parent_name"]].drop_duplicates()
            for code, name in parents.itertuples(index=False, name=None):
                conn.execute("INSERT INTO analytics.dim_parent VALUES (%s,%s) ON CONFLICT(parent_code) DO UPDATE SET parent_name=EXCLUDED.parent_name", (code, None if pd.isna(name) else name))
        if domain == "rtt":
            for code, name in frame[["specialty_code", "specialty_name"]].drop_duplicates().itertuples(index=False, name=None):
                conn.execute("INSERT INTO analytics.dim_specialty VALUES (%s,%s) ON CONFLICT(specialty_code) DO UPDATE SET specialty_name=EXCLUDED.specialty_name", (code, name))
        elif domain == "diagnostics":
            for code, name in frame[["test_code", "test_name"]].drop_duplicates().itertuples(index=False, name=None):
                conn.execute("INSERT INTO analytics.dim_service VALUES (%s,%s) ON CONFLICT(test_code) DO UPDATE SET test_name=EXCLUDED.test_name", (code, name))
        else:
            for (name,) in frame[["region_name"]].drop_duplicates().itertuples(index=False, name=None):
                conn.execute("INSERT INTO analytics.dim_region VALUES (%s) ON CONFLICT DO NOTHING", (name,))
        table = "fact_" + domain
        columns = [r[0] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='analytics' AND table_name=%s ORDER BY ordinal_position", (table,))]
        if not set(columns).issubset(frame.columns):
            raise ValueError(f"Required warehouse fields absent: {set(columns)-set(frame.columns)}")
        key = {"rtt": ["month", "provider_code", "specialty_code", "pathway_type"], "diagnostics": ["month", "provider_code", "test_code"], "ae": ["month", "provider_code"]}[domain]
        if frame.duplicated(key).any():
            raise ValueError(f"Unexpected multiple provider parents/names at declared {domain} grain")
        conn.execute(sql.SQL("TRUNCATE staging.{}").format(sql.Identifier(domain)))
        with conn.cursor().copy(sql.SQL("COPY staging.{} ({}) FROM STDIN").format(sql.Identifier(domain), sql.SQL(',').join(map(sql.Identifier, columns)))) as copy:
            for row in frame[columns].itertuples(index=False, name=None):
                copy.write_row(tuple(None if pd.isna(v) else (int(v) if isinstance(v, __import__('numpy').integer) else v) for v in row))
        conn.execute(sql.SQL("DELETE FROM analytics.{} WHERE month=%s").format(sql.Identifier(table)), (month,))
        conn.execute(sql.SQL("INSERT INTO analytics.{} SELECT * FROM staging.{}").format(sql.Identifier(table), sql.Identifier(domain)))
        count = conn.execute(sql.SQL("SELECT count(*) FROM analytics.{} WHERE month=%s").format(sql.Identifier(table)), (month,)).fetchone()[0]
        if count != len(frame):
            raise ValueError("Warehouse row-count reconciliation failed")
        conn.execute("""INSERT INTO audit.loaded_source(dataset,month,sha256,parser_version,rows_loaded) VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT(dataset,month) DO UPDATE SET sha256=EXCLUDED.sha256,parser_version=EXCLUDED.parser_version,rows_loaded=EXCLUDED.rows_loaded,loaded_at=now()""", (domain, month, source["sha256"], parser_version, len(frame)))
    return True


def query_frame(query: str) -> pd.DataFrame:
    with connect() as conn:
        result = conn.execute(query)
        return pd.DataFrame(result.fetchall(), columns=[x.name for x in result.description])
