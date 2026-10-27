param([string]$InvokeName = '')
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=Split-Path $PSScriptRoot -Parent
$state=Get-Content -LiteralPath (Join-Path $root '.local\powerbi_desktop.json') -Raw | ConvertFrom-Json
$proc=Get-Process -Id $state.pid
if (-not $proc.MainWindowHandle) { throw 'Project process has no main window yet' }
$element=[System.Windows.Automation.AutomationElement]::FromHandle($proc.MainWindowHandle)
$all=$element.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
$items=@()
foreach ($el in $all) {
    $name=$el.Current.Name
    if ($name -and $el.Current.ControlType.ProgrammaticName -ne 'ControlType.Pane') {
        $items+=@{name=$name;type=$el.Current.ControlType.ProgrammaticName;enabled=$el.Current.IsEnabled;automationId=$el.Current.AutomationId}
    }
    if ($InvokeName -and $name -eq $InvokeName -and $el.Current.IsEnabled -and -not $el.Current.IsOffscreen) {
        $pattern=$null
        if ($el.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)) {
            $pattern.Invoke()
            Write-Output "Invoked '$InvokeName' inside this project's Power BI window"
            break
        }
        $selection=$null
        if ($el.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$selection)) {
            $selection.Select()
            Write-Output "Selected '$InvokeName' inside this project's Power BI window"
            break
        }
    }
}
$items | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root '.local\powerbi_ui.json') -Encoding UTF8
$items | Where-Object { $_.type -in @('ControlType.Window','ControlType.TabItem','ControlType.Image') -or $_.name -match 'error|failed|Refresh|Load|Cancel|Close|incomplete|warning' } | Select-Object -First 55 | ConvertTo-Json -Depth 4
