param([switch]$InspectOnly)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$name='NHS Healthcare Operations - Official Publication Check'
$script=Join-Path $PSScriptRoot 'refresh.ps1'
if (-not (Test-Path -LiteralPath $script)) { throw 'Refresh script missing' }
$existing=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($InspectOnly) {
    if ($existing) { $existing | Select-Object TaskName,State; Get-ScheduledTaskInfo -TaskName $name }
    else { Write-Output 'Project publication task is not registered' }
    exit
}
if ($existing) {
    $expected='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$script+'"'
    if ($existing.Actions.Arguments -ne $expected) { throw 'Existing task action differs; inspect before replacing' }
    Write-Output 'Matching project task already exists; no change'
    exit
}
$args='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+$script+'"'
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $args -WorkingDirectory $root
$trigger=New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At '14:30'
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$user=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Free local official NHS publication check; requires signed-in user for Excel. Power BI refresh is separate.' | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName $name | Select-Object NextRunTime,LastTaskResult
