#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run-Stack.ps1 — Full MLOps stack startup script for ISE-2 lab submission.
    
.DESCRIPTION
    This script:
    1. Verifies Docker is running
    2. Builds the iris-predictor Docker image
    3. Starts the full stack (app + jenkins + prometheus + grafana)
    4. Prints a smoke test result
    5. Shows all container statuses
    
.USAGE
    cd "C:\ISE 2 MLDEVOPS"
    .\Run-Stack.ps1
#>

$PROJECT_DIR = "C:\ISE 2 MLDEVOPS"
$IMAGE_NAME  = "iris-predictor"
$APP_PORT    = 5000

Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host " ISE-2 MLOps Lab — Stack Startup   " -ForegroundColor Cyan
Write-Host "===================================`n" -ForegroundColor Cyan

# ── Step 1: Check Docker ───────────────────────────────────────────────────────
Write-Host "[1/5] Checking Docker..." -ForegroundColor Yellow
try {
    $v = docker --version 2>&1
    Write-Host "      Docker: $v" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Docker not found. Install Docker Desktop first!" -ForegroundColor Red
    exit 1
}

# ── Step 2: Hello World test ───────────────────────────────────────────────────
Write-Host "[2/5] Running docker hello-world..." -ForegroundColor Yellow
docker run --rm hello-world 2>&1 | Select-String "Hello from Docker" | ForEach-Object {
    Write-Host "      $($_)" -ForegroundColor Green
}

# ── Step 3: Build the app image ───────────────────────────────────────────────
Write-Host "[3/5] Building $IMAGE_NAME image..." -ForegroundColor Yellow
Set-Location $PROJECT_DIR
docker build -t "${IMAGE_NAME}:latest" -t "${IMAGE_NAME}:lab" .
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: docker build failed!" -ForegroundColor Red; exit 1 }
Write-Host "      Build successful." -ForegroundColor Green

# ── Step 4: Start full stack ───────────────────────────────────────────────────
Write-Host "[4/5] Starting full stack with docker compose..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: docker compose up failed!" -ForegroundColor Red; exit 1 }

Start-Sleep -Seconds 10  # wait for containers to become healthy

# ── Step 5: Smoke test ────────────────────────────────────────────────────────
Write-Host "[5/5] Smoke testing /health endpoint..." -ForegroundColor Yellow
$maxAttempts = 10; $attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$APP_PORT/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "      HTTP $($resp.StatusCode): $($resp.Content)" -ForegroundColor Green
        break
    } catch {
        $attempt++
        Write-Host "      Waiting... ($attempt/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 3
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host " STACK IS RUNNING! Service URLs:   " -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host " App       → http://localhost:5000 " -ForegroundColor White
Write-Host " Jenkins   → http://localhost:8085 " -ForegroundColor White
Write-Host " Prometheus→ http://localhost:9090 " -ForegroundColor White
Write-Host " Grafana   → http://localhost:3000 " -ForegroundColor White
Write-Host "   (admin / admin123)              " -ForegroundColor Gray
Write-Host "===================================`n" -ForegroundColor Cyan

Write-Host "Container status:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`nJenkins UI (Setup Wizard disabled, no initial password required):" -ForegroundColor Yellow
Write-Host "  Open http://localhost:8085 in your browser"

Write-Host "`nTo generate traffic for Grafana graphs:" -ForegroundColor Yellow
Write-Host "  python traffic/generate_traffic.py --n 200 --url http://localhost:$APP_PORT"

Write-Host "`nTo stop everything:" -ForegroundColor Yellow
Write-Host "  docker compose down"
