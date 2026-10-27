param([string]$PostgresBin = 'C:\Program Files\PostgreSQL\18\bin', [int]$Port = 55473)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$localDir = Join-Path $root '.local'
$pgData = Join-Path $localDir 'postgres'
New-Item -ItemType Directory -Path $localDir -Force | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $pgData 'PG_VERSION'))) {
    $randomBytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($randomBytes)
    $password = [Convert]::ToBase64String($randomBytes)
    $passwordFile = Join-Path $localDir 'pg-password.tmp'
    [System.IO.File]::WriteAllText($passwordFile, $password)
    & (Join-Path $PostgresBin 'initdb.exe') -D $pgData -U nhs --pwfile=$passwordFile --auth=scram-sha-256 --encoding=UTF8 --locale=C
    if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
    Remove-Item -LiteralPath $passwordFile
    $escapedPassword = [Uri]::EscapeDataString($password)
    [System.IO.File]::WriteAllText((Join-Path $root '.env'), "DATABASE_URL=postgresql://nhs:$escapedPassword@127.0.0.1:$Port/nhs_operations`n")
}
$envPath = Join-Path $root '.env'
$envText = [System.IO.File]::ReadAllText($envPath)
$envText = $envText -replace '@127\.0\.0\.1:\d+/', "@127.0.0.1:$Port/"
[System.IO.File]::WriteAllText($envPath, $envText)
& (Join-Path $PostgresBin 'pg_ctl.exe') -D $pgData status 2>$null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $PostgresBin 'pg_ctl.exe') -D $pgData -l (Join-Path $localDir 'postgres.log') -o "-h 127.0.0.1 -p $Port" start
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL startup failed' }
}
Write-Output "Isolated project PostgreSQL cluster ready on loopback port $Port. Credentials remain in ignored .env."
