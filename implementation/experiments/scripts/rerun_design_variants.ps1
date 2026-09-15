# Re-run the design-decision ablation round on the post-pyramid-fix engine
# (review finding P4). Run from implementation\experiments in PowerShell:
#
#     .\scripts\rerun_design_variants.ps1
#
# Steps, each stopping the script on failure:
#   1. Regression gate: default p3net must reproduce its stored runs exactly.
#   2. Archive the pre-fix variant raw runs (moved, never deleted).
#   3. Run 9 variants x 4 search spaces x 4 budgets x 30 seeds (4320 runs).
#   4. Regenerate the variant report and the paper's generated tables,
#      then check every number in the paper against the tables.
#
# Safe to interrupt and restart: step 3 skips runs already written, and
# step 2 skips files already archived. Do not run generate_report.py by
# hand while step 3 is still writing to results\raw.

$ErrorActionPreference = "Stop"

function Invoke-Step([string]$Label, [scriptblock]$Command) {
    Write-Host ""
    Write-Host "=== $Label ===" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Label failed (exit code $LASTEXITCODE)" }
}

$Variants = @(
    "p3net_inherited_cost",
    "p3net_cascade",
    "p3net_f1_truncation",
    "p3net_grow_on_stall",
    "p3net_transient_donors",
    "p3net_kappa_half",
    "p3net_kappa_double",
    "p3net_threshold_strict",
    "p3net_threshold_permissive"
)
$SearchSpaces = @("jahs_bench_201", "jahs_bench_201_colorectal", "jahs_bench_201_fashion", "nas_hpo_bench_ii")

# -- 1. regression gate -------------------------------------------------------
Invoke-Step "1/4 Verify default p3net is unchanged" {
    uv run python scripts/verify_p3net_unchanged.py --search-spaces nas_hpo_bench_ii jahs_bench_201 --budgets 50 100 --seeds 1 2 3
}

# -- 2. archive pre-fix variant runs -------------------------------------------
Write-Host ""
Write-Host "=== 2/4 Archive pre-fix variant raw runs ===" -ForegroundColor Cyan
$Archive = "results\archive\design-variants-pre-pyramid-fix_2026-08-16"
New-Item -ItemType Directory -Force -Path "$Archive\raw" | Out-Null
$moved = 0
foreach ($v in $Variants) {
    foreach ($f in Get-ChildItem -Path "results\raw" -Filter "${v}__*.json" -ErrorAction SilentlyContinue) {
        if ($f.LastWriteTime -lt [datetime]"2026-08-18") {
            Move-Item -Path $f.FullName -Destination "$Archive\raw\" -Force
            $moved++
        }
    }
}
Write-Host "moved $moved pre-fix file(s) to $Archive\raw"

# -- 3. the grid ---------------------------------------------------------------
Invoke-Step "3/4 Run design variants (4320 runs)" {
    uv run python scripts/run_grid.py --methods @Variants --search-spaces @SearchSpaces
}

# -- 4. reports and paper check ------------------------------------------------
Invoke-Step "4a/4 Variant report" { uv run python scripts/generate_variants_report.py }
Invoke-Step "4b/4 Main report" { uv run python scripts/generate_report.py --no-archive }
Invoke-Step "4c/4 Paper tables" { uv run python scripts/render_results_tex.py }
Invoke-Step "4d/4 Paper number check" { uv run python scripts/check_paper_numbers.py --strict }

Write-Host ""
Write-Host "Done. Results: results\tables\p3net_variants_comparable.md" -ForegroundColor Green
