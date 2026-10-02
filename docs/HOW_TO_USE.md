# 🚀 Your AI Coding Assistant - Quick Guide

## ✅ System Status: All Working!

### Verified Components:
- ✅ Ollama v0.35.0 running
- ✅ Qwen2.5-Coder 7B model loaded (4.7 GB)
- ✅ MCP Fetch server working (web requests)
- ✅ MCP Git server working (version control)
- ✅ Python environment working
- ✅ Git initialized

---

## 🎯 How to Use Your AI Coding Assistant

### 1. Quick Coding Help with Ollama

#### Ask for Code Examples:
```powershell
# Write a function
ollama run qwen2.5-coder:7b "Write a Python function to sort a dictionary by values"

# Debug code
ollama run qwen2.5-coder:7b "Debug this code: def add(a,b) return a+b"

# Explain concepts
ollama run qwen2.5-coder:7b "Explain what is async/await in JavaScript"

# Code review
ollama run qwen2.5-coder:7b "Review this code and suggest improvements: [paste code]"
```

#### Interactive Coding Session:
```powershell
# Start interactive mode
ollama run qwen2.5-coder:7b

# Now you can chat continuously:
>>> Write a Python class for a car
>>> Add a method to calculate fuel efficiency
>>> How can I optimize this code?
>>> /bye  # Exit when done
```

---

### 2. MCP Servers (Integrated Tools)

#### A. Fetch Server (Web Requests)
```powershell
# Get data from APIs
# Built into Kiro - works automatically when you need web data
```

#### B. Git Server (Version Control)
```powershell
# Initialize repo
git init

# Check status
git status

# Add files
git add .

# Commit
git commit -m "Initial commit"

# The MCP server enhances these operations in Kiro
```

#### C. GitHub Server
- Clone repositories
- Create issues
- Manage pull requests
- Search code
*(Requires GitHub token configuration)*

#### D. SQLite Server
- Query databases
- Create tables
- Manage data
- Database operations

---

## 💡 Practical Use Cases

### Use Case 1: Write New Code
```powershell
ollama run qwen2.5-coder:7b "Create a REST API endpoint in Flask for user registration"
```

### Use Case 2: Debug Errors
```powershell
ollama run qwen2.5-coder:7b "I'm getting 'list index out of range' error in Python. Here's my code: [paste code]"
```

### Use Case 3: Learn New Concepts
```powershell
ollama run qwen2.5-coder:7b "Explain decorators in Python with examples"
```

### Use Case 4: Code Optimization
```powershell
ollama run qwen2.5-coder:7b "Optimize this loop for better performance: [paste code]"
```

### Use Case 5: Test Writing
```powershell
ollama run qwen2.5-coder:7b "Write pytest unit tests for this function: [paste code]"
```

---

## 🛠️ Common Commands

### Ollama Management
```powershell
# List installed models
ollama list

# Check running models
ollama ps

# Stop a model
ollama stop qwen2.5-coder:7b

# Remove a model
ollama rm model-name

# Update Ollama
winget upgrade Ollama.Ollama
```

### Install Additional Models
```powershell
# Smaller/faster coding model
ollama pull qwen2.5-coder:3b

# Larger coding model (needs more RAM)
ollama pull deepseek-coder-v2:16b-lite

# General purpose models
ollama pull llama3.2:3b
ollama pull gemma2:9b
```

---

## 🎨 Kiro IDE Integration

### In Kiro IDE, you can:

1. **Ask coding questions** - Kiro will use MCP servers automatically
2. **Fetch web data** - Automatic with MCP Fetch server
3. **Git operations** - Enhanced with MCP Git server
4. **File operations** - MCP Filesystem server handles it
5. **Database queries** - MCP SQLite server integration

### MCP Server Status
Check in Kiro: 
- Command Palette → "MCP Server" 
- View → MCP Servers panel

---

## 📚 Language Support

Your model supports:
- ✅ Python
- ✅ JavaScript/TypeScript
- ✅ Java
- ✅ C/C++
- ✅ Go
- ✅ Rust
- ✅ PHP
- ✅ Ruby
- ✅ Swift
- ✅ Kotlin
- ✅ HTML/CSS
- ✅ SQL
- ✅ Shell/Bash
- ✅ And more!

---

## 🔥 Pro Tips

### 1. Be Specific
❌ Bad: "Write a function"
✅ Good: "Write a Python function that reads a CSV file and returns a pandas DataFrame"

### 2. Provide Context
Include relevant code, error messages, or requirements in your prompt

### 3. Iterate
If the first answer isn't perfect, ask for modifications:
- "Make it more efficient"
- "Add error handling"
- "Explain this part"

### 4. Use for Learning
Ask "why" questions to understand the code:
- "Why use async here?"
- "What's the time complexity?"
- "What are alternatives?"

### 5. Code Review
Paste your code and ask:
- "Review this and suggest improvements"
- "What are potential bugs?"
- "How can I make this more readable?"

---

## 🚨 Troubleshooting

### Model is slow?
- You might have other heavy applications running
- Close unnecessary apps to free RAM
- Consider using a smaller model: `ollama pull qwen2.5-coder:3b`

### MCP Server not working?
1. Restart Kiro IDE
2. Check: Command Palette → "MCP Server Status"
3. Verify `uv` is installed: `uv --version`

### Out of disk space?
1. Run cleanup script: `.\cleanup_c_drive.ps1` (as admin)
2. Remove unused models: `ollama rm model-name`
3. Move files to D: drive

### Ollama not starting?
```powershell
# Check if running
Get-Process ollama

# Restart
Stop-Process -Name ollama -Force
Start-Process ollama
```

---

## 📊 Resource Usage

### Current Setup:
- **Qwen2.5-Coder 7B**: ~6-8 GB RAM when running
- **Disk Space**: 4.7 GB for model
- **CPU**: Uses 4 cores efficiently

### Your Available Resources:
- **RAM**: 15.6 GB total (enough for current model + IDE + browser)
- **Disk**: 
  - C: 10.86 GB free (for system)
  - D: 235 GB free (for projects)

---

## 🎯 Next Steps

### Beginner:
1. Try the example queries above
2. Ask it to write simple functions
3. Use it to learn new concepts

### Intermediate:
1. Use for debugging real projects
2. Get code review feedback
3. Generate unit tests

### Advanced:
1. Integrate with your development workflow
2. Use MCP servers for automation
3. Customize with additional models

---

## 🆘 Need Help?

### Resources:
- Ollama Docs: https://ollama.com/docs
- Kiro Documentation: Check Help menu
- MCP Servers: https://modelcontextprotocol.io

### Common Questions:

**Q: Can I use multiple models?**
A: Yes! Install multiple with `ollama pull model-name`

**Q: Can it access the internet?**
A: The MCP Fetch server can get web data for you

**Q: Is this private?**
A: Yes! Everything runs locally on your PC

**Q: Can I use it offline?**
A: Yes! Once downloaded, no internet needed for Ollama

---

## 🎊 You're Ready to Code!

Start with simple queries and explore. The more you use it, the more productive you'll become!

**Happy Coding with AI!** 🚀

---

*Last Updated: October 1, 2026*
*Model: Qwen2.5-Coder 7B*
*MCP Servers: Fetch, Git, GitHub, SQLite, Filesystem*
