# Auto Test Generator
# Usage: .\auto_test_generator.ps1 -file "mycode.py"

param(
    [Parameter(Mandatory=$true)]
    [string]$file,          # Source file to generate tests for
    
    [string]$framework = "pytest"  # Test framework (pytest, unittest, jest, etc.)
)

Write-Host "🧪 AI Test Generator" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan
Write-Host ""

# Check if file exists
if (-not (Test-Path $file)) {
    Write-Host "❌ File not found: $file" -ForegroundColor Red
    exit 1
}

Write-Host "📂 Analyzing: $file" -ForegroundColor Yellow
Write-Host "🔧 Framework: $framework" -ForegroundColor Yellow
Write-Host ""

# Read the source code
$code = Get-Content $file -Raw

# Generate tests
Write-Host "🤖 Generating comprehensive tests..." -ForegroundColor Cyan
$prompt = "Write comprehensive $framework unit tests for this code. Include edge cases, error handling, and mock data. Code: $code"

$tests = ollama run qwen2.5-coder:7b $prompt

# Determine output filename
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($file)
$extension = [System.IO.Path]::GetExtension($file)
$testFile = "test_$baseName$extension"

# Save tests
$tests | Out-File -FilePath $testFile -Encoding UTF8

Write-Host "✅ Tests generated!" -ForegroundColor Green
Write-Host "📁 Saved to: $testFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "Preview:" -ForegroundColor Yellow
Write-Host "--------" -ForegroundColor Yellow
Get-Content $testFile -Head 30
Write-Host ""
Write-Host "💡 Run tests with: pytest $testFile" -ForegroundColor Gray
