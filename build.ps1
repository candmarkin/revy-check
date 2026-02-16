# Build script for Windows (PowerShell)

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "RevyCheck - Build Script (Windows)" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check if Rust is installed
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Rust não está instalado!" -ForegroundColor Red
    Write-Host "Instale de: https://rustup.rs/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Rust encontrado: $(rustc --version)" -ForegroundColor Green
Write-Host ""

Write-Host "Compilando em modo Release..." -ForegroundColor Yellow
Write-Host ""

cargo build --release

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host "✅ Build concluído com sucesso!" -ForegroundColor Green
    Write-Host "===================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Binário: target\release\revy-check.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Para executar:" -ForegroundColor Yellow
    Write-Host "  .\target\release\revy-check.exe" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Erro durante a compilação!" -ForegroundColor Red
    exit 1
}
