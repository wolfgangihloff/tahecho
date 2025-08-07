# Local Development Guide

## 🌐 Viewing the SBOM Dashboard Locally

Due to browser CORS (Cross-Origin Resource Sharing) security policies, the SBOM dashboard cannot load JSON data when opened directly as a file (`file://` protocol). Here are the solutions:

### **Option 1: Python HTTP Server (Recommended)**
```bash
# Navigate to the public directory
cd /Users/wolfgang.ihloff/workspace/tahecho/public

# Start a local HTTP server
python3 -m http.server 8000

# Open in browser
open http://localhost:8000
```

### **Option 2: Node.js HTTP Server**
```bash
# Install global server (if not already installed)
npm install -g http-server

# Navigate to public directory
cd /Users/wolfgang.ihloff/workspace/tahecho/public

# Start server
http-server -p 8000

# Open http://localhost:8000
```

### **Option 3: VS Code Live Server Extension**
1. Install the "Live Server" extension in VS Code
2. Right-click on `public/index.html`
3. Select "Open with Live Server"
4. The page will open automatically with proper HTTP protocol

### **Option 4: Use GitHub Pages (Production)**
The dashboard is automatically deployed and works perfectly at:
**https://wolfgang.ihloff.github.io/tahecho/**

## 🔧 Understanding the CORS Issue

### **Why This Happens**
- Browsers block `fetch()` requests from `file://` URLs for security
- This prevents malicious local files from accessing your file system
- The restriction only applies to local file access, not HTTP servers

### **What Works**
- ✅ HTTP/HTTPS protocols (`http://localhost:8000`)
- ✅ GitHub Pages deployment
- ✅ Any web server (local or remote)

### **What Doesn't Work**
- ❌ Opening HTML directly in browser (`file://`)
- ❌ Double-clicking the HTML file

## 🚀 Development Workflow

For active development on the SBOM dashboard:

```bash
# 1. Start local server
cd public && python3 -m http.server 8000

# 2. Make changes to index.html

# 3. Refresh browser at http://localhost:8000

# 4. Test the "Load SBOM Data" functionality
```

## 📋 Quick Test Commands

```bash
# Verify SBOM files exist
ls -la public/sbom.*

# Check JSON validity
jq . public/sbom.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"

# Test local server
curl -s http://localhost:8000/sbom.json | jq .metadata.component.name
```

## 🛠️ Troubleshooting

### **Port Already in Use**
```bash
# Try different port
python3 -m http.server 8001
```

### **JSON Not Loading**
1. Verify `sbom.json` exists in `public/` directory
2. Check browser developer console for errors
3. Ensure you're using HTTP protocol (not file://)

### **Dashboard Not Updating**
1. Hard refresh browser (Ctrl+F5 / Cmd+Shift+R)
2. Clear browser cache
3. Restart local server

This setup ensures the SBOM dashboard works perfectly during local development while maintaining security best practices.
