# Crash-safe wrapper around scripts/run_pipeline.py.
#
# Run from implementation\experiments:
#
#     .\scripts\run_pipeline.ps1                     # everything, in plan order
#     .\scripts\run_pipeline.ps1 -DryRun              # counts, missing configs, completion so far
#     .\scripts\run_pipeline.ps1 -Stages s1_headline  # one stage
#     .\scripts\run_pipeline.ps1 -Workers 4           # 4 worker processes (default: plan's parallel.workers)
#
# Resuming: just run the same command again. Completed runs are kept and
# validated; only missing, truncated, or failed runs are re-run.
#
# -MaxRestarts: if the Python process itself dies (crash, out of memory,
# killed), the wrapper starts it again, up to this many times. Each restart
# resumes from the last completed run. Ctrl+C is NOT restarted. A worker
# process that dies is restarted by run_pipeline.py itself; each worker's
# output is in the run root's logs\worker-<i>.log.

param(
    [string[]]$Stages = @(),
    [switch]$DryRun,
    [switch]$AllowDirty,
    [switch]$RetryFailed,
    [switch]$SkipChecks,
    [int]$MaxRetries = 3,
    [int]$MaxRestarts = 5,
    [int]$Workers = 0,
    [string]$RunRoot = ""
)

$ErrorActionPreference = "Stop"

$pyArgs = @("run", "python", "scripts/run_pipeline.py", "--max-retries", "$MaxRetries")
if ($Stages.Count -gt 0) { $pyArgs += "--stages"; $pyArgs += $Stages }
if ($DryRun)      { $pyArgs += "--dry-run" }
if ($AllowDirty)  { $pyArgs += "--allow-dirty" }
if ($RetryFailed) { $pyArgs += "--retry-failed" }
if ($SkipChecks)  { $pyArgs += "--skip-checks" }
if ($RunRoot -ne "") { $pyArgs += "--run-root"; $pyArgs += $RunRoot }
if ($Workers -gt 0)  { $pyArgs += "--workers"; $pyArgs += "$Workers" }

# Exit codes from run_pipeline.py:
#   0 = every requested stage complete
#   1 = refused to start (preflight, dirty code, manifest mismatch, failed checks) -- restarting would not help
#   2 = finished or interrupted with points remaining
#   anything else = the process died -- restart and resume
$restarts = 0
while ($true) {
    Write-Host ""
    Write-Host "=== run_pipeline.py (attempt $($restarts + 1)) ===" -ForegroundColor Cyan
    & uv @pyArgs
    $code = $LASTEXITCODE

    if ($code -eq 0) {
        Write-Host "All requested stages complete." -ForegroundColor Green
        exit 0
    }
    if ($code -eq 1) {
        Write-Host "Pipeline refused to start or checks failed -- see the message above. Not restarting." -ForegroundColor Red
        exit 1
    }
    if ($code -eq 2) {
        Write-Host "Finished with points remaining (failures, given-up points, or Ctrl+C)." -ForegroundColor Yellow
        Write-Host "See the run root's failures.jsonl; rerun this command to retry (add -RetryFailed to reset attempt counts)." -ForegroundColor Yellow
        exit 2
    }

    $restarts++
    if ($restarts -gt $MaxRestarts) {
        Write-Host "Process died $restarts times (last exit code $code); giving up. Rerun this command to resume." -ForegroundColor Red
        exit $code
    }
    Write-Host "Process died with exit code $code -- restarting in 30 s and resuming ($restarts/$MaxRestarts)." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}
