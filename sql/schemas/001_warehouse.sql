CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS raw.source_file (
    sha256 text PRIMARY KEY CHECK (length(sha256)=64),
    dataset text NOT NULL CHECK (dataset IN ('rtt','ae','diagnostics')),
    month date NOT NULL,
    url text NOT NULL,
    publication_date date,
    retrieved_at timestamptz NOT NULL,
    bytes bigint NOT NULL CHECK (bytes>0),
    metadata jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS audit.pipeline_run (
    run_id uuid PRIMARY KEY,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    status text NOT NULL,
    summary jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS audit.loaded_source (
    dataset text NOT NULL,
    month date NOT NULL,
    sha256 text NOT NULL REFERENCES raw.source_file,
    parser_version text NOT NULL,
    rows_loaded bigint NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(dataset,month)
);
CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date date PRIMARY KEY, year integer NOT NULL, month_number integer NOT NULL,
    month_name text NOT NULL, financial_year text NOT NULL
);
INSERT INTO analytics.dim_date
SELECT d::date, extract(year FROM d), extract(month FROM d), to_char(d,'Mon YYYY'),
       CASE WHEN extract(month FROM d)>=4 THEN to_char(d,'YYYY')||'-'||to_char(d+interval '1 year','YY')
       ELSE to_char(d-interval '1 year','YYYY')||'-'||to_char(d,'YY') END
FROM generate_series('2006-01-01'::date,'2030-12-31'::date,'1 day') d
ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS analytics.dim_provider (
    provider_code text PRIMARY KEY, provider_name text,
    name_as_of date NOT NULL,
    identity_basis text NOT NULL DEFAULT 'Official source provider identifier; trust/site status not inferred'
);
CREATE TABLE IF NOT EXISTS analytics.dim_parent (
    parent_code text PRIMARY KEY, parent_name text
);
CREATE TABLE IF NOT EXISTS analytics.dim_specialty (
    specialty_code text PRIMARY KEY, specialty_name text NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_service (
    test_code text PRIMARY KEY, test_name text NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_region (
    region_name text PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS analytics.fact_rtt (
    month date NOT NULL REFERENCES analytics.dim_date,
    provider_code text NOT NULL REFERENCES analytics.dim_provider,
    parent_code text NOT NULL REFERENCES analytics.dim_parent,
    specialty_code text NOT NULL REFERENCES analytics.dim_specialty,
    pathway_type text NOT NULL CHECK (pathway_type IN ('Part_1A','Part_1B','Part_2')),
    waiting_count bigint CHECK (waiting_count>=0), total_all bigint CHECK (total_all>=0),
    unknown_start bigint CHECK (unknown_start>=0), within_18 bigint CHECK (within_18>=0),
    over_18 bigint CHECK (over_18>=0), over_52 bigint CHECK (over_52>=0),
    over_65 bigint CHECK (over_65>=0), over_78 bigint CHECK (over_78>=0), over_104 bigint CHECK (over_104>=0),
    source_sha256 text NOT NULL REFERENCES raw.source_file,
    PRIMARY KEY(month,provider_code,specialty_code,pathway_type),
    CHECK (within_18+over_18=waiting_count), CHECK (waiting_count+unknown_start=total_all),
    CHECK (over_104<=over_78 AND over_78<=over_65 AND over_65<=over_52 AND over_52<=over_18)
);
CREATE TABLE IF NOT EXISTS analytics.fact_ae (
    month date NOT NULL REFERENCES analytics.dim_date,
    provider_code text NOT NULL REFERENCES analytics.dim_provider,
    region_name text NOT NULL REFERENCES analytics.dim_region,
    attendances bigint CHECK (attendances>=0), over_4 bigint CHECK (over_4>=0), within_4 bigint CHECK (within_4>=0),
    type1_attendances bigint CHECK (type1_attendances>=0), type1_over_4 bigint CHECK (type1_over_4>=0),
    admissions_via_ae bigint CHECK (admissions_via_ae>=0), other_admissions bigint CHECK (other_admissions>=0),
    emergency_admissions bigint CHECK (emergency_admissions>=0), dta_4_12 bigint CHECK (dta_4_12>=0), dta_12_plus bigint CHECK (dta_12_plus>=0),
    source_sha256 text NOT NULL REFERENCES raw.source_file,
    PRIMARY KEY(month,provider_code), CHECK (within_4+over_4=attendances),
    CHECK (type1_over_4<=type1_attendances), CHECK (admissions_via_ae+other_admissions=emergency_admissions)
);
CREATE TABLE IF NOT EXISTS analytics.fact_diagnostics (
    month date NOT NULL REFERENCES analytics.dim_date,
    provider_code text NOT NULL REFERENCES analytics.dim_provider,
    parent_code text NOT NULL REFERENCES analytics.dim_parent,
    test_code text NOT NULL REFERENCES analytics.dim_service,
    waiting_count bigint CHECK (waiting_count>=0), over_6 bigint CHECK (over_6>=0), over_13 bigint CHECK (over_13>=0),
    total_activity bigint CHECK (total_activity>=0), waiting_activity bigint CHECK (waiting_activity>=0),
    planned_activity bigint CHECK (planned_activity>=0), unscheduled_activity bigint CHECK (unscheduled_activity>=0),
    source_sha256 text NOT NULL REFERENCES raw.source_file,
    PRIMARY KEY(month,provider_code,test_code), CHECK (over_13<=over_6 AND over_6<=waiting_count),
    CHECK (waiting_activity+planned_activity+unscheduled_activity=total_activity)
);
CREATE UNLOGGED TABLE IF NOT EXISTS staging.rtt (LIKE analytics.fact_rtt INCLUDING DEFAULTS);
CREATE UNLOGGED TABLE IF NOT EXISTS staging.ae (LIKE analytics.fact_ae INCLUDING DEFAULTS);
CREATE UNLOGGED TABLE IF NOT EXISTS staging.diagnostics (LIKE analytics.fact_diagnostics INCLUDING DEFAULTS);
CREATE INDEX IF NOT EXISTS idx_rtt_provider_month ON analytics.fact_rtt(provider_code,month) INCLUDE(waiting_count,over_52) WHERE pathway_type='Part_2';
CREATE INDEX IF NOT EXISTS idx_rtt_pathway_month ON analytics.fact_rtt(pathway_type,month);
CREATE INDEX IF NOT EXISTS idx_diag_provider_month ON analytics.fact_diagnostics(provider_code,month);
CREATE INDEX IF NOT EXISTS idx_ae_region_month ON analytics.fact_ae(region_name,month);
