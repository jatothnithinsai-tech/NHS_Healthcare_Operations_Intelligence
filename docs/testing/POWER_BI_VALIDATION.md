# Power BI validation boundaries and format compatibility

The project was opened and refreshed in installed Power BI Desktop **2.159.883.0**. All four pages displayed genuine imported data. Read-only DAX queries against that project's own local Analysis Services engine matched PostgreSQL headline KPIs, provider/date filter context and 25 monthly domain totals. The saved evidence and genuine screenshots accompany the project.

The published source uses documented, publicly available PBIR schemas (including visual-container 2.1.0), report definition version metadata and a TMDL semantic model. Microsoft TOM parses the model. The required `definition/version.json` is present.

This Desktop release upgrades visual metadata to schema 2.14.0 on Save. The referenced public schema endpoint returned HTTP 404 during verification. The repository therefore retains the public-schema generated definitions that this installed Desktop successfully opened, rather than claiming the unavailable schema was validated. Desktop can upgrade those files when a user saves a local copy. Its normal Save also removes the optional schema pointers from `.pbip`, `.pbir` and `.pbism`; the source generator retains them for explicit static validation.

The model's DataRoot parameter points to the actual local validated CSV exports. Change it after cloning to another folder. Local `.pbi` caches and settings are excluded from Git. No `.pbix` is fabricated. Slicer, tooltip and provider-drillthrough metadata are configured; a complete human usability review remains separate from the executed page-load and DAX tests.
