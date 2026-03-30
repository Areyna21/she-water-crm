# SHE Water CRM — Git Setup Script
# Run this once from inside the she-water-crm folder
# In VS Code terminal: .\setup-git.ps1

Write-Host "Setting up Git for SHE Water CRM..." -ForegroundColor Cyan

# Initialize git
git init

# Stage everything
git add .

# Initial commit
git commit -m "initial SHE Water CRM build — database, API, intake form"

Write-Host ""
Write-Host "Git initialized locally." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Go to github.com and create a new PRIVATE repo called: she-water-crm"
Write-Host "2. Do NOT check 'Initialize with README'"
Write-Host "3. Copy the repo URL (looks like: https://github.com/Angel21/she-water-crm.git)"
Write-Host "4. Run these two commands with your actual URL:"
Write-Host ""
Write-Host '   git remote add origin https://github.com/Angel21/she-water-crm.git' -ForegroundColor White
Write-Host '   git push -u origin main' -ForegroundColor White
Write-Host ""
Write-Host "After that, every update is just:" -ForegroundColor Yellow
Write-Host '   git add .'
Write-Host '   git commit -m "what changed"'
Write-Host '   git push'
