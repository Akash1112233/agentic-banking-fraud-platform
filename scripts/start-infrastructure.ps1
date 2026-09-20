[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DbPassword,

    [Parameter(Mandatory = $true)]
    [string]$Neo4jPassword
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host "Checking Docker Desktop..." -ForegroundColor Cyan
docker info | Out-Null

$env:AML_DB_PASSWORD = $DbPassword
$env:NEO4J_PASSWORD = $Neo4jPassword

Write-Host "Checking local Ollama model..." -ForegroundColor Cyan
ollama show qwen3:14b | Out-Null

Write-Host "Starting Redpanda..." -ForegroundColor Cyan
docker compose -f phase3_streaming\docker-compose.yml up -d

Write-Host "Starting PostgreSQL..." -ForegroundColor Cyan
docker compose -f phase4_backend\docker-compose.yml up -d

Write-Host "Starting Neo4j..." -ForegroundColor Cyan
docker compose -f phase5_graph\docker-compose.yml up -d

Write-Host "Infrastructure status:" -ForegroundColor Green
docker compose -f phase3_streaming\docker-compose.yml ps
docker compose -f phase4_backend\docker-compose.yml ps
docker compose -f phase5_graph\docker-compose.yml ps

Write-Host "Infrastructure is started. Keep these values in the current PowerShell session:" -ForegroundColor Green
Write-Host "  AML_DB_PASSWORD=<provided password>"
Write-Host "  NEO4J_PASSWORD=<provided password>"
Write-Host "  LLM_PROVIDER=ollama"
Write-Host "  OLLAMA_MODEL=qwen3:14b"
Write-Host "Do not run 'docker compose down -v'; it deletes named database volumes." -ForegroundColor Yellow
