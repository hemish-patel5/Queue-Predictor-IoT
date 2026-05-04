<#
Queue & Comfort Predictor — Windows runner (PowerShell)

Usage:
  .\run_all.ps1           # create venv, install deps (first time) and start services
  .\run_all.ps1 stop      # stop background jobs started by this script

Notes:
- Camera (Raspberry Pi) installation steps are printed but not executed on Windows.
- This script uses Start-Process to launch Python services so they keep running.
#>

param(
    [string]$Action = 'start'
)

Set-StrictMode -Version Latest
$ProjectDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Push-Location $ProjectDir

$LogDir = Join-Path $ProjectDir 'logs'
$PidFile = Join-Path $ProjectDir '.pids_windows'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

function Write-Info($m){ Write-Host $m -ForegroundColor Green }
function Write-Warn($m){ Write-Host $m -ForegroundColor Yellow }
function Write-Err($m){ Write-Host $m -ForegroundColor Red }

if ($Action -eq 'stop') {
    if (Test-Path $PidFile) {
        $pids = Get-Content $PidFile | Where-Object { $_ -ne '' }
        foreach ($pid in $pids) {
            try { Stop-Process -Id [int]$pid -ErrorAction SilentlyContinue; Write-Info "Stopped PID $pid" } catch {}
        }
        Remove-Item $PidFile -Force
        Write-Info "All processes stopped."
    } else {
        Write-Warn "No running processes found (no $PidFile)."
    }
    Pop-Location
    return
}

# Create venv if missing
$VenvDir = Join-Path $ProjectDir 'venv'
if (-not (Test-Path (Join-Path $VenvDir 'Scripts\Activate.ps1'))) {
    Write-Warn "No virtual environment found. Creating one (this may take a moment)..."
    python -m venv $VenvDir
    & $VenvDir\Scripts\pip.exe install --upgrade pip
    if (Test-Path "backend\requirements-updated.txt") {
        & $VenvDir\Scripts\pip.exe install -r "backend\requirements-updated.txt"
    } elseif (Test-Path "backend\requirements.txt") {
        & $VenvDir\Scripts\pip.exe install -r "backend\requirements.txt"
    }
    # Install frontend deps
    if (Test-Path "frontend\package.json") {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            Write-Info "Installing frontend npm packages..."
            npm install --prefix frontend
        } else {
            Write-Warn "npm not found. Skipping frontend npm install. Install Node.js and run: npm install --prefix frontend"
        }
    }
}

if (-not (Test-Path "$ProjectDir\.env")) {
    Write-Err "Required .env file is missing in project root. Copy .env.example to .env and configure environment variables."; Pop-Location; exit 1
}

# Helper: start process and record PID
function Start-ServiceProc($name, $cmd, $args) {
    $log = Join-Path $LogDir "$name.log"
    Write-Info "Starting $name... (log: $log)"
    $startInfo = @{FilePath=$cmd; ArgumentList=$args; RedirectStandardOutput=$true; RedirectStandardError=$true; UseNewWindow=$false}
    $proc = Start-Process @startInfo -PassThru
    # Write PID
    $proc.Id | Out-File -FilePath $PidFile -Append -Encoding ascii
    Write-Info "✔ $name -> PID $($proc.Id)"
}

# Ensure .pids file is cleared
if (Test-Path $PidFile) { Remove-Item $PidFile -Force }

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  Queue & Comfort Predictor — Starting (Windows)"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Sensor drivers (on Windows these may be no-ops / develop-only)
Write-Host "[ Sensor Drivers ]"
# If hardware drivers rely on Raspberry Pi libraries, warn and skip
function MaybeStartDriver($label, $path) {
    $full = Join-Path $ProjectDir $path
    if (Test-Path $full) {
        # On Windows we still attempt to run Python scripts if present
        Start-ServiceProc $label 'python' $full
    } else {
        Write-Warn "Driver $path not found; skipping."
    }
}

MaybeStartDriver 'dht22' 'hardware/drivers/Humiture_Sensor.py'
MaybeStartDriver 'co2'   'hardware/drivers/co2_sensor.py'
MaybeStartDriver 'sound' 'hardware/drivers/sound_sensor.py'
MaybeStartDriver 'pir'   'hardware/drivers/PIR_sensor.py'

# Vision: Raspberry Pi specific - do not auto-run on Windows
if ($IsLinux -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM') {
    MaybeStartDriver 'vision' 'hardware/vision/pi_camera_logic.py'
} else {
    Write-Warn "Camera launch skipped on Windows. To run vision on a Pi, execute the script on the Pi and ensure YOLO model and camera drivers are installed."
}

Write-Host ""
Write-Host "[ Backend ]"
Start-ServiceProc 'fusion' 'python' 'backend/logic/sensor_fusion.py'
Start-Sleep -Seconds 1
Start-ServiceProc 'advisory' 'python' 'backend/services/LLM_advisory.py'
Start-ServiceProc 'api' 'python' '-m uvicorn backend.services.API_server:app --host 0.0.0.0 --port 5000 --reload'

Write-Host ""
Write-Host "[ Frontend ]"
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pycmd = 'python3'
} else { $pycmd = 'python' }
Start-ServiceProc 'dashboard' $pycmd '-m http.server 8080 --directory frontend'

Write-Host ""
Write-Info "All services started. Logs: $LogDir"
Write-Info "Stop all  -> .\run_all.ps1 stop"

Pop-Location
