# Auto Commit with AI-Generated Message
# Usage: .\auto_commit.ps1

Write-Host "🤖 AI Git Commit Assistant" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""

# Check if in git repo
if (-not (Test-Path .git)) {
    Write-Host "❌ Not a git repository!" -ForegroundColor Red
    Write-Host "Run 'git init' first." -ForegroundColor Yellow
    exit 1
}

# Check for changes
$status = git status --porcelain
if (-not $status) {
    Write-Host "✅ No changes to commit." -ForegroundColor Green
    exit 0
}

Write-Host "📊 Changes detected:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Get diff
Write-Host "🔍 Analyzing changes..." -ForegroundColor Cyan
$diff = git diff --cached
if (-not $diff) {
    # No staged changes, stage all
    Write-Host "Staging all changes..." -ForegroundColor Gray
    git add -A
    $diff = git diff --cached
}

# Generate commit message
Write-Host "🤖 Generating commit message..." -ForegroundColor Cyan
$prompt = "Based on these git changes, write a concise commit message (max 72 chars) following conventional commits format. Only output the commit message, nothing else. Changes: $diff"

$message = ollama run qwen2.5-coder:7b $prompt

# Clean up the message (remove quotes, extra text)
$message = $message -replace '^["\s]+|["\s]+$', ''
$message = $message.Split("`n")[0]  # Take first line only

Write-Host ""
Write-Host "📝 Generated commit message:" -ForegroundColor Yellow
Write-Host "  $message" -ForegroundColor White
Write-Host ""

# Ask for confirmation
$confirm = Read-Host "Commit with this message? (Y/n)"
if ($confirm -eq '' -or $confirm -eq 'Y' -or $confirm -eq 'y') {
    git commit -m $message
    Write-Host ""
    Write-Host "✅ Committed successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Ask about push
    $push = Read-Host "Push to remote? (Y/n)"
    if ($push -eq '' -or $push -eq 'Y' -or $push -eq 'y') {
        git push
        Write-Host "✅ Pushed to remote!" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Commit cancelled." -ForegroundColor Red
    Write-Host "💡 You can manually commit with: git commit -m ""your message""" -ForegroundColor Gray
}
