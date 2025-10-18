# Requires PowerShell and Scoop installed
# Installs Poppler and Tesseract, then ensures eng.traineddata is present

$ErrorActionPreference = "Stop"

function Initialize-Scoop {
  if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "Scoop not found. Installing Scoop..."
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Invoke-Expression (New-Object System.Net.WebClient).DownloadString('https://get.scoop.sh')
  }
}

function Install-Tools {
  Write-Host "Installing Poppler and Tesseract via Scoop..."
  scoop install poppler
  scoop install tesseract
}

function Initialize-Tessdata {
  $tessData = "$env:USERPROFILE\scoop\persist\tesseract\tessdata"
  if (-not (Test-Path $tessData)) {
    New-Item -ItemType Directory -Force -Path $tessData | Out-Null
  }
  $env:TESSDATA_PREFIX = $tessData
  $engPath = Join-Path $tessData "eng.traineddata"
  if (-not (Test-Path $engPath)) {
    Write-Host "Downloading eng.traineddata..."
    Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/eng.traineddata" -OutFile $engPath
  }
}

Initialize-Scoop
Install-Tools
Initialize-Tessdata

Write-Host "Done. Poppler and Tesseract installed, TESSDATA_PREFIX set, eng.traineddata present."
