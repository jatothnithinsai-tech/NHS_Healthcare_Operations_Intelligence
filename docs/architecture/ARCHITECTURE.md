# Architecture and modelling decisions

```mermaid
flowchart LR
  NHS[Official NHS publications] --> C[Link and reporting-month discovery]
  C --> R[Immutable raw files + SHA-256 manifest]
  R --> P[Profile / schema / period / source-total controls]
  P --> S[Parquet cache and PostgreSQL staging]
  S --> F[Three independent fact tables]
  F --> V[Weighted KPI views and 30 SQL analyses]
  V --> ST[Statistics and decision report]
  V --> X[Excel management workbook]
  F --> BI[Power BI import model]
  R --> A[Source and pipeline audit]
```

```mermaid
erDiagram
  DIM_DATE ||--o{ FACT_RTT : month
  DIM_DATE ||--o{ FACT_AE : month
  DIM_DATE ||--o{ FACT_DIAGNOSTICS : month
  DIM_PROVIDER ||--o{ FACT_RTT : provider
  DIM_PROVIDER ||--o{ FACT_AE : provider
  DIM_PROVIDER ||--o{ FACT_DIAGNOSTICS : provider
  DIM_SPECIALTY ||--o{ FACT_RTT : specialty
  DIM_SERVICE ||--o{ FACT_DIAGNOSTICS : test
  DIM_PARENT ||--o{ FACT_RTT : source_parent
  DIM_PARENT ||--o{ FACT_DIAGNOSTICS : source_parent
  DIM_REGION ||--o{ FACT_AE : source_region
  SOURCE_FILE ||--o{ FACT_RTT : checksum
  SOURCE_FILE ||--o{ FACT_AE : checksum
  SOURCE_FILE ||--o{ FACT_DIAGNOSTICS : checksum
```

RTT grain: reporting month/provider/specialty/pathway type. DM01: reporting month/provider/test. A&E: reporting month/provider. Commissioner-level raw rows aggregate once into provider facts. Redundant all-specialty/test/national totals remain controls only. Dates are daily and facts use the first day of the reporting month. Single-direction dimension-to-fact relationships avoid many-to-many inflation.

Provider code is the analytical identifier, not a claim of trust/site equivalence. The provider-name dimension is type 1 with latest source date. Source parent ICB fields stay with the appropriate facts; a current geographic lookup is never backdated. A&E regional analysis uses the source monthly region. Official current A&E mapping is retained for reference only and is not used to manufacture historical regional RTT/DM01 mappings.

Each revised file is immutable and identified by checksum. Changed source month is replaced transactionally after dimension upserts; a successful audit row records parser version and count. Same checksum/version skips the load. Failures roll back the affected month. This favours correctness over unsupported append-only incrementality.
