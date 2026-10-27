$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$pbiBin=Split-Path ((Get-Process -Name PBIDesktop | Select-Object -First 1).Path)
if (-not $pbiBin) { throw 'Installed Power BI Desktop binary path could not be resolved' }
$tomDir=Join-Path $root '.local\tom'
[System.Reflection.Assembly]::LoadFrom((Join-Path $tomDir 'Microsoft.AnalysisServices.Core.dll')) | Out-Null
[System.Reflection.Assembly]::LoadFrom((Join-Path $tomDir 'Microsoft.AnalysisServices.Tabular.dll')) | Out-Null
$definition=Join-Path $root 'powerbi\NHS_Healthcare.SemanticModel\definition'
$db=[Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($definition)
$measures=0
foreach ($table in $db.Model.Tables) { $measures += $table.Measures.Count }
$result=@{status='PASS';database=$db.Name;tables=$db.Model.Tables.Count;relationships=$db.Model.Relationships.Count;measures=$measures;validation='Parsed by Microsoft public TOM TmdlSerializer; installed Desktop version recorded separately. DAX execution requires refreshed model';desktopVersion=(Get-Item (Join-Path $pbiBin 'PBIDesktop.exe')).VersionInfo.FileVersion}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'reports\validation\tmdl_validation.json') -Encoding UTF8
$result | ConvertTo-Json
