$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires elevated privileges to modify the PATH environment variable."
    Write-Host "Opening an elevated PowerShell window..."
    
    # Start a new PowerShell process with elevated privileges
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    
    Exit
}

$folderPath = "C:\GitEx"
$exePath = ".\dist\gitex.exe"

if (!(Test-Path $folderPath -ErrorAction SilentlyContinue)) {
    New-Item -Path $folderPath -ItemType Directory | Out-Null
}

Copy-Item -Path $exePath -Destination $folderPath -Force
$PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine")

if ($PATH -notlike "*;$folderPath;*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$PATH;$folderPath", "Machine")
}

Write-Host "Setup completed"
