# Flow for Windows: one-step installer.
#
#   irm https://raw.githubusercontent.com/kodair918-del/flow-releases/main/install.ps1 | iex
#
# Downloads the latest build, checks its SHA-256, puts it in %LOCALAPPDATA%\Flow (settings are kept),
# adds a Start menu entry and "start with Windows", and starts it. After that Flow updates itself.
# Run it again at any time to repair or update by hand. Uninstall: Start menu > "Flow - uninstall".
#
# Keep this file ASCII-only: Windows PowerShell 5.1 misreads UTF-8 without a BOM, and a BOM breaks "irm | iex".

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$base = $env:FLOW_BASE
if (-not $base) { $base = 'https://raw.githubusercontent.com/kodair918-del/flow-releases/dist' }
$dir = $env:FLOW_INSTALL_DIR
if (-not $dir) { $dir = Join-Path $env:LOCALAPPDATA 'Flow' }
$test = [bool]$env:FLOW_TEST          # trying the installer: no Start menu entry, no autostart, no start

if (-not [Environment]::Is64BitOperatingSystem) { throw 'Flow needs 64-bit Windows 10 or 11.' }
if ([Environment]::OSVersion.Version.Build -lt 17763) { throw 'Flow needs Windows 10 (1809) or newer.' }

$tmp = Join-Path ([IO.Path]::GetTempPath()) ('flow-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null
try
{
    Write-Host '==> Downloading the latest Flow'
    $json = (Invoke-WebRequest -UseBasicParsing -Uri "$base/latest.json").Content
    if ($json -is [byte[]]) { $json = [Text.Encoding]::UTF8.GetString($json) }
    $info = $json | ConvertFrom-Json
    if (-not $info.url -or -not $info.sha256) { throw 'latest.json is not valid.' }
    $zip = Join-Path $tmp 'Flow-win.zip'
    Invoke-WebRequest -UseBasicParsing -Uri $info.url -OutFile $zip
    $have = (Get-FileHash -Path $zip -Algorithm SHA256).Hash.ToLower()
    if ($have -ne ([string]$info.sha256).ToLower())
    {
        throw 'The download does not match its checksum. Wait a few minutes and run this again.'
    }

    Write-Host "==> Installing into $dir"
    # stop an older copy (only the ones that run from this folder)
    Get-Process -Name FlowTray, FlowWall, watch -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -and $_.Path.StartsWith($dir, [StringComparison]::OrdinalIgnoreCase) } |
        Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 800

    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $new = Join-Path $tmp 'new'
    Expand-Archive -Path $zip -DestinationPath $new -Force
    foreach ($f in Get-ChildItem -Path $new -File)
    {
        if ($f.Name -ieq 'xamlh.cfg') { continue }                      # never overwrite the settings
        $dest = Join-Path $dir $f.Name
        # the taskbar layer is loaded inside Explorer, so it cannot be replaced now: it waits as
        # xamlh-next.dll and the watcher puts it in place when Explorer next starts.
        if ($f.Name -ieq 'xamlh.dll' -and (Test-Path $dest)) { $dest = Join-Path $dir 'xamlh-next.dll' }
        try { Copy-Item -Path $f.FullName -Destination $dest -Force }
        catch
        {
            if (Test-Path $dest) { Move-Item -Path $dest -Destination ($dest + '.old') -Force }
            Copy-Item -Path $f.FullName -Destination $dest -Force
        }
    }
    Get-ChildItem -Path $dir -Filter '*.old' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

    $tray = Join-Path $dir 'FlowTray.exe'
    if (-not $test)
    {
        # Start menu entries
        $menu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
        $shell = New-Object -ComObject WScript.Shell
        $lnk = $shell.CreateShortcut((Join-Path $menu 'Flow.lnk'))
        $lnk.TargetPath = $tray
        $lnk.WorkingDirectory = $dir
        $lnk.Save()
        foreach ($pair in @(@('Flow - on', '--on'), @('Flow - off', '--off')))
        {
            $lnk = $shell.CreateShortcut((Join-Path $menu ($pair[0] + '.lnk')))
            $lnk.TargetPath = $tray
            $lnk.Arguments = $pair[1]
            $lnk.WorkingDirectory = $dir
            $lnk.Save()
        }
        $un = Join-Path $dir 'Uninstall.ps1'
        if (Test-Path $un)
        {
            $lnk = $shell.CreateShortcut((Join-Path $menu 'Flow - uninstall.lnk'))
            $lnk.TargetPath = 'powershell.exe'
            $lnk.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $un + '"'
            $lnk.WorkingDirectory = $dir
            $lnk.Save()
        }
        # start with Windows
        New-Item -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Force | Out-Null
        Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'Flow' -Value ('"' + $tray + '"')

        Write-Host '==> Starting Flow'
        Start-Process -FilePath $tray -WorkingDirectory $dir
    }

    # can the taskbar scenery run on this Windows? (Windows 11 has the XAML taskbar it attaches to)
    $view = ''
    $found = Get-ChildItem -Path (Join-Path $env:SystemRoot 'SystemApps') -Filter 'Taskbar.View.dll' -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($found) { $view = $found.VersionInfo.FileVersion }
    $ok = ([Environment]::OSVersion.Version.Build -ge 22000) -and [bool]$found
    $checked = $false
    foreach ($v in @($info.taskbarViews)) { if ($v -eq $view) { $checked = $true } }

    Write-Host ''
    Write-Host "Done. Flow $($info.version) is installed; its icon is in the notification area (next to the clock)."
    if ($ok)
    {
        Write-Host 'Both the wallpaper and the taskbar scenery are on (the taskbar needs no restart).'
        if (-not $checked)
        {
            Write-Host "Your taskbar build ($view) has not been tried yet. If the taskbar scenery does not appear,"
            Write-Host 'the wallpaper still works and nothing on the taskbar is changed.'
        }
    }
    else
    {
        Write-Host 'The taskbar scenery needs Windows 11. The wallpaper works; the taskbar is left alone.'
    }
}
finally
{
    Remove-Item -Path $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
