param(
    [int]$Port = 8001
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvUvicorn = Join-Path $ProjectRoot ".venv\Scripts\uvicorn.exe"
$EnvFile = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Не найдено виртуальное окружение .venv" -ForegroundColor Red
    Write-Host "Сначала создай его или проверь, что запускаешь скрипт из папки проекта."
    exit 1
}

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $name, $value = $line.Split("=", 2)
        $name = $name.Trim()
        $value = $value.Trim().Trim('"').Trim("'")

        if ($name -and -not [Environment]::GetEnvironmentVariable($name, "Process")) {
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

if (-not $env:CHECKO_API_KEY) {
    $key = Read-Host "Введи CHECKO_API_KEY"
    if ($key) {
        $env:CHECKO_API_KEY = $key
    }
}

Write-Host "Запускаю сервер: http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "Остановить сервер можно клавишами Ctrl+C"

& $VenvUvicorn app:app --reload --port $Port
