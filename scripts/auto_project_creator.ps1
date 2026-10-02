# Auto Project Creator
# Usage: .\auto_project_creator.ps1 -name "MyApp" -type "flask-api"

param(
    [Parameter(Mandatory=$true)]
    [string]$name,      # Project name
    
    [Parameter(Mandatory=$true)]
    [string]$type       # Project type: "flask-api", "react-app", "django", "express", "fastapi"
)

Write-Host "🚀 AI Project Creator" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Creating: $name" -ForegroundColor Yellow
Write-Host "Type: $type" -ForegroundColor Yellow
Write-Host ""

# Create project directory
New-Item -ItemType Directory -Force -Path $name | Out-Null
Set-Location $name

Write-Host "📁 Created directory: $name" -ForegroundColor Green

# Define project templates
$templates = @{
    "flask-api" = @{
        files = @(
            "app.py",
            "requirements.txt",
            "README.md",
            ".gitignore",
            "config.py",
            "models.py"
        )
        prompts = @{
            "app.py" = "Create a Flask REST API with basic CRUD endpoints for a User resource"
            "requirements.txt" = "List requirements for a Flask REST API with SQLAlchemy and pytest"
            "README.md" = "Create a README for a Flask API project named $name"
            ".gitignore" = "Create a .gitignore for Python Flask project"
            "config.py" = "Create Flask configuration file with dev and prod settings"
            "models.py" = "Create SQLAlchemy User model with id, name, email, created_at"
        }
    }
    "fastapi" = @{
        files = @(
            "main.py",
            "requirements.txt",
            "README.md",
            ".gitignore",
            "models.py",
            "database.py"
        )
        prompts = @{
            "main.py" = "Create a FastAPI application with CRUD endpoints for User"
            "requirements.txt" = "List requirements for FastAPI with SQLAlchemy"
            "README.md" = "Create README for FastAPI project named $name"
            ".gitignore" = "Create .gitignore for Python project"
            "models.py" = "Create Pydantic models for User with validation"
            "database.py" = "Create database connection setup for FastAPI with SQLAlchemy"
        }
    }
    "react-app" = @{
        files = @(
            "App.jsx",
            "package.json",
            "README.md",
            ".gitignore",
            "index.html"
        )
        prompts = @{
            "App.jsx" = "Create a React App component with routing and basic structure"
            "package.json" = "Create package.json for React app named $name"
            "README.md" = "Create README for React app named $name"
            ".gitignore" = "Create .gitignore for React/Node.js project"
            "index.html" = "Create index.html for React app named $name"
        }
    }
}

# Get template or use generic
$template = $templates[$type]
if (-not $template) {
    Write-Host "⚠️ Unknown project type. Creating generic structure..." -ForegroundColor Yellow
    $template = @{
        files = @("main.py", "README.md", ".gitignore")
        prompts = @{
            "main.py" = "Create a basic $type application entry point"
            "README.md" = "Create README for $type project named $name"
            ".gitignore" = "Create .gitignore for $type project"
        }
    }
}

# Generate each file
Write-Host ""
Write-Host "🤖 Generating files..." -ForegroundColor Cyan
Write-Host ""

foreach ($file in $template.files) {
    Write-Host "  📝 Creating $file..." -ForegroundColor Gray
    
    $prompt = $template.prompts[$file]
    if ($prompt) {
        $content = ollama run qwen2.5-coder:7b "$prompt. Output only the code/content, no explanations."
        $content | Out-File -FilePath $file -Encoding UTF8
        Write-Host "  ✅ $file created" -ForegroundColor Green
    }
}

# Initialize git
Write-Host ""
Write-Host "📦 Initializing git repository..." -ForegroundColor Cyan
git init
git add .
git commit -m "Initial commit - Auto-generated $type project"

Write-Host ""
Write-Host "🎉 Project Created Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Location: $(Get-Location)" -ForegroundColor Cyan
Write-Host "📝 Files created: $($template.files.Count)" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "  1. cd $name" -ForegroundColor Gray
Write-Host "  2. Review generated files" -ForegroundColor Gray
Write-Host "  3. Install dependencies" -ForegroundColor Gray
Write-Host "  4. Start coding!" -ForegroundColor Gray
Write-Host ""
