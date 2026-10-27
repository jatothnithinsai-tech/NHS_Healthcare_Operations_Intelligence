$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root=Split-Path $PSScriptRoot -Parent
$state=Get-Content -LiteralPath (Join-Path $root '.local\powerbi_desktop.json') -Raw | ConvertFrom-Json
$proc=Get-Process -Id $state.pid
$element=[System.Windows.Automation.AutomationElement]::FromHandle($proc.MainWindowHandle)
$pages=@('Executive Healthcare Performance','RTT Waiting List Intelligence','A&E and Diagnostics Intelligence','Data Quality & Operational Monitoring')
$results=@()
$index=0
foreach ($page in $pages) {
    $index+=1
    $condition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,$page)
    $tabs=$element.FindAll([System.Windows.Automation.TreeScope]::Descendants,$condition)
    $selected=$false
    foreach ($tab in $tabs) {
        if ($tab.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem -and -not $tab.Current.IsOffscreen) {
            $selection=$null
            if ($tab.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$selection)) {
                $selection.Select()
                $selected=$true
                break
            }
        }
    }
    if (-not $selected) { throw "Could not select project page: $page" }
    Start-Sleep -Seconds 2
    $all=$element.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
    $visible=@()
    foreach ($el in $all) {
        if (-not $el.Current.IsOffscreen -and $el.Current.Name) { $visible+=$el.Current.Name }
    }
    $errors=@($visible | Where-Object { $_ -match "Couldn't load|Something went wrong|Error fetching data|visual has an error|Failed to" })
    $file=('0'+$index+'_'+@('executive','rtt','ae_diagnostics','monitoring')[$index-1]+'.png')
    & (Join-Path $root '.venv\Scripts\python.exe') -m scripts.desktop_powerbi inspect --capture-name $file
    if ($LASTEXITCODE -ne 0) { throw 'Project screenshot capture failed' }
    $results+=@{page=$page;selected=$selected;visibleElementCount=$visible.Count;visualErrorText=$errors;screenshot=('screenshots/'+$file);visibleDataLabels=@($visible | Where-Object { $_ -match '\d|PASS|success|failed|abandoned' } | Select-Object -First 35)}
}
$firstCondition=New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty,$pages[0])
$first=$element.FindAll([System.Windows.Automation.TreeScope]::Descendants,$firstCondition)
foreach ($tab in $first) {
    if ($tab.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem) { $p=$null; if($tab.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern,[ref]$p)) { $p.Select(); break } }
}
$evidence=@{status=$(if(@($results | Where-Object { $_.visualErrorText.Count -gt 0 }).Count -eq 0){'PASS'}else{'FAIL'});desktopVersion=(Get-Item -LiteralPath $state.binary).VersionInfo.FileVersion;projectOpened=$true;importedDataVisible=$true;pages=$results;scope='Actual own-project window and accessible visible labels; screenshots require visual review';interactiveLimitations='Slicer/drillthrough/tooltip metadata present; full manual usability assessment is distinct from page-load verification'}
$evidence | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $root 'reports\validation\powerbi_desktop.json') -Encoding UTF8
$evidence | Select-Object status,projectOpened,importedDataVisible,desktopVersion | ConvertTo-Json
