# ⚡ Quick Automation Reference

## 🎯 Ready-to-Use Automation Scripts

All scripts are in: `D:\mcp server\`

---

## 1. 🚀 Auto Project Creator

**Create complete projects instantly!**

```powershell
# Create Flask API
.\auto_project_creator.ps1 -name "MyAPI" -type "flask-api"

# Create FastAPI project
.\auto_project_creator.ps1 -name "FastApp" -type "fastapi"

# Create React app
.\auto_project_creator.ps1 -name "MyReactApp" -type "react-app"
```

**What it does:**
- ✅ Creates project folder
- ✅ Generates all necessary files
- ✅ Initializes git repository
- ✅ Makes first commit

---

## 2. 🤖 Auto Commit

**AI-generated git commit messages!**

```powershell
# Stage and commit with AI message
.\auto_commit.ps1
```

**What it does:**
- ✅ Analyzes your changes
- ✅ Generates meaningful commit message
- ✅ Asks for confirmation
- ✅ Optionally pushes to remote

---

## 3. 🧪 Auto Test Generator

**Generate tests for any code file!**

```powershell
# Generate pytest tests
.\auto_test_generator.ps1 -file "mycode.py"

# Generate with specific framework
.\auto_test_generator.ps1 -file "api.py" -framework "unittest"
```

**What it does:**
- ✅ Reads your code
- ✅ Generates comprehensive tests
- ✅ Includes edge cases
- ✅ Creates test_*.py file

---

## 4. 💻 Auto Code Generator

**Generate any code instantly!**

```powershell
# Generate a function
.\auto_code_generator.ps1 -type "function" -description "validate email address" -language "python"

# Generate a class
.\auto_code_generator.ps1 -type "class" -description "User authentication" -language "python"

# Generate API endpoint
.\auto_code_generator.ps1 -type "api" -description "CRUD for products" -language "python" -output "products_api.py"
```

**What it does:**
- ✅ Generates code based on description
- ✅ Follows best practices
- ✅ Includes comments
- ✅ Saves to file automatically

---

## 🎓 Quick Examples

### Example 1: Start New Project
```powershell
# Create Flask API project
.\auto_project_creator.ps1 -name "TodoAPI" -type "flask-api"
cd TodoAPI
# Review files and start coding!
```

### Example 2: Generate & Test
```powershell
# Generate code
.\auto_code_generator.ps1 -type "function" -description "calculate fibonacci sequence" -language "python" -output "fibonacci.py"

# Generate tests for it
.\auto_test_generator.ps1 -file "fibonacci.py"

# Run tests
pytest test_fibonacci.py
```

### Example 3: Auto Git Workflow
```powershell
# After coding...
git add .
.\auto_commit.ps1
# AI generates message, commits, and pushes!
```

---

## 🔧 Direct Ollama Commands

### Code Generation
```powershell
ollama run qwen2.5-coder:7b "Write a Python function to [description]" > output.py
```

### Get Explanation
```powershell
ollama run qwen2.5-coder:7b "Explain how async/await works in JavaScript"
```

### Debug Help
```powershell
ollama run qwen2.5-coder:7b "Why am I getting 'list index out of range' in this code: [code]"
```

### Code Review
```powershell
ollama run qwen2.5-coder:7b "Review this code for issues: [code]"
```

---

## 💡 Power User Tips

### Batch Processing
```powershell
# Generate tests for all Python files
Get-ChildItem *.py | ForEach-Object {
    .\auto_test_generator.ps1 -file $_.Name
}
```

### Custom Aliases (Add to PowerShell Profile)
```powershell
# Edit profile
notepad $PROFILE

# Add these:
function aigen { .\auto_code_generator.ps1 @args }
function aicommit { .\auto_commit.ps1 }
function aitest { .\auto_test_generator.ps1 @args }
function ainew { .\auto_project_creator.ps1 @args }

# Now use: aigen -type "function" -description "sort array"
```

### Chain Commands
```powershell
# Generate, test, and commit
.\auto_code_generator.ps1 -type "function" -description "API client" -output "client.py"
.\auto_test_generator.ps1 -file "client.py"
git add .
.\auto_commit.ps1
```

---

## 📊 Performance

| Task | Time | Output |
|------|------|--------|
| Generate function | 3-5s | Single file |
| Generate tests | 5-10s | Test file |
| Create project | 30-60s | Multiple files |
| Commit message | 2-5s | Git commit |

---

## ⚠️ Best Practices

1. **Review AI Output** - Always check generated code
2. **Start Small** - Test with simple tasks first
3. **Iterate** - If output isn't perfect, regenerate with better description
4. **Version Control** - Keep git history of changes
5. **Test Everything** - Run generated tests

---

## 🎯 Common Use Cases

### For Beginners:
- Generate boilerplate code
- Learn coding patterns
- Understand error messages
- Get code explanations

### For Intermediate:
- Auto-generate tests
- Quick prototyping
- Code refactoring
- API development

### For Advanced:
- Batch processing
- CI/CD automation
- Code analysis
- Custom tooling

---

## 🆘 Troubleshooting

**Script won't run?**
```powershell
# Enable script execution
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Ollama not found?**
```powershell
# Check if running
ollama --version
# Start service if needed
Start-Process ollama serve
```

**Slow generation?**
- Close other apps to free RAM
- Use smaller prompts
- Consider a lighter model

---

## 🎊 Next Steps

1. **Try the examples above**
2. **Read AUTOMATION_GUIDE.md** for advanced techniques
3. **Build your own automation scripts**
4. **Share your automations!**

---

*These scripts use Ollama qwen2.5-coder:7b locally - no internet required!*
