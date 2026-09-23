<#
.SYNOPSIS
  Compiles fo4-anatomy's Papyrus scripts (papyrus/) into build/papyrus/.

.DESCRIPTION
  Import order matters: F4SE's own sources first (they are Bethesda's real sources plus F4SE's
  additions, e.g. Actor.GetWornItem, and keep their default arguments), then the reconstructed base
  sources (which lost every default: pass all arguments), then ours and the import-only stubs
  (LooksMenu's BodyGen). AAF's sources come with the base (Base/AAF).

  NEVER compile into Data/Scripts: it is Vortex-deployed. ASCII only (Windows PowerShell 5.1 reads a
  BOM-less UTF-8 script as ANSI). Adapted from fo4-chemistry/scripts/build-papyrus.ps1.
#>
[CmdletBinding()]
param(
    [string] $Base     = 'D:\F4CustomMods\PapyrusBase\Source\Base',
    [string] $Compiler = 'D:\GOGGames\Fallout 4 GOTY\Papyrus Compiler\PapyrusCompiler.exe',
    [string] $F4SE     = 'D:\Vortex\fallout4\mods\Fallout 4 Script Extender (F4SE)-42147-0-6-23-1665656782\Data\Scripts\Source'
)

$ErrorActionPreference = 'Stop'
$root    = Split-Path -Parent $PSScriptRoot
$sources = Join-Path $root 'papyrus'
$stubs   = Join-Path $root 'papyrus-stubs'
$out     = Join-Path $root 'build\papyrus'

foreach ($p in @($Compiler, (Join-Path $Base 'Institute_Papyrus_Flags.flg'), (Join-Path $F4SE 'Actor.psc'))) {
    if (-not (Test-Path $p)) { throw "Missing $p" }
}
New-Item -ItemType Directory -Force -Path $out | Out-Null
$scripts = Get-ChildItem -Recurse -Filter *.psc $sources
Write-Host "Compiling $($scripts.Count) script(s)"

# Batch mode: a namespaced script (Anatomy:Arousal) takes its namespace from the import paths.
$output = & $Compiler $sources -all -f="Institute_Papyrus_Flags.flg" -i="$F4SE;$Base;$sources;$stubs" -o="$out" 2>&1
$output | ForEach-Object { Write-Host "  $_" }

$built = Get-ChildItem -Recurse -Filter *.pex $out -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "$($built.Count) .pex in $out"
if ($output -match 'compilation failed' -or $output -match '0 succeeded' -or $built.Count -lt $scripts.Count) { exit 1 }
