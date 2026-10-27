$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$name='NHS Healthcare Operations - Official Publication Check'
$task=Get-ScheduledTask -TaskName $name
$info=Get-ScheduledTaskInfo -TaskName $name
$evidence=@{registered=$true;taskName=$name;state=$task.State.ToString();nextRunTime=$info.NextRunTime.ToString('o');schedule='Thursday 14:30 in Windows local time; interactive signed-in user';windowsTimeZone=(Get-TimeZone).Id;action=$task.Actions.Execute;arguments=$task.Actions.Arguments;lastTaskResult=$info.LastTaskResult;firstScheduledExecutionVerified=$false;refreshScriptVerifiedSeparately=$true}
$evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'reports\validation\schedule.json') -Encoding UTF8
$evidence | ConvertTo-Json
