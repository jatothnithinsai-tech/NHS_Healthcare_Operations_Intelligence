$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $root
$python=Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create the project virtual environment and install requirements first' }
& (Join-Path $PSScriptRoot 'start_postgres.ps1')
& $python -m src.pipeline --refresh --reports
if ($LASTEXITCODE -ne 0) { throw 'Publication refresh failed; inspect logs and audit records' }
& $python -m scripts.build_powerbi
if ($LASTEXITCODE -ne 0) { throw 'Power BI project metadata validation failed' }
& $python -m scripts.build_excel
if ($LASTEXITCODE -ne 0) { throw 'Excel calculation and reconciliation failed' }
$env:NHS_INTEGRATION='1'
& $python -m pytest -q -p no:cacheprovider --basetemp=.local/pytest-scheduled --junitxml=reports/validation/scheduled_tests.xml
if ($LASTEXITCODE -ne 0) { throw 'Refresh regression tests failed' }
Write-Output 'Official publications, warehouse, analytical exports and Excel updated. Power BI model refresh remains a separate desktop operation.'
