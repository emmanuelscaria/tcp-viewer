# TCP Viewer - Documentation Index

**Complete documentation for TCP Viewer v1.0**

---

## Quick Links

- **🚀 [QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **📘 [README.md](README.md)** - Project overview and features
- **🏗️ [ARCHITECTURE.md](ARCHITECTURE.md)** - System design and implementation
- **🔌 [API.md](API.md)** - HTTP REST API reference
- **📊 [TCP_METRICS_GUIDE.md](TCP_METRICS_GUIDE.md)** - Understanding TCP metrics
- **🧪 [TESTING.md](TESTING.md)** - Test procedures and scenarios

---

## Documentation Map

### For New Users

1. **README.md** - Start here for project overview
   - Features list
   - System requirements
   - Installation steps
   - Basic usage

2. **QUICKSTART.md** - Hands-on setup guide
   - Step-by-step installation
   - Running the application
   - Testing procedures
   - Troubleshooting common issues

### For Developers

3. **ARCHITECTURE.md** - Deep dive into system design
   - Component breakdown
   - Data flow diagrams
   - Implementation details
   - Performance considerations
   - Future enhancements

4. **API.md** - Backend API reference
   - Endpoint documentation
   - Data model schemas
   - Request/response examples
   - Error handling
   - Integration patterns

### For Network Engineers

5. **TCP_METRICS_GUIDE.md** - Understanding TCP parameters
   - RTT calculation
   - Window sizes
   - Congestion control
   - Retransmission detection

6. **TESTING.md** - Comprehensive test scenarios
   - Traffic generation
   - Edge cases
   - Performance testing
   - Debugging techniques

---

## Additional Resources

### Configuration Files
- **backend/requirements.txt** - Python dependencies
- **frontend/package.json** - Node.js dependencies
- **backend/server.py** - Main server configuration
- **frontend/src/App.js** - Frontend configuration

### Helper Scripts
- **setup.sh** - Automated setup script
- **backend/run_server.sh** - Backend startup script
- **tcp_test_server.py** - Test TCP server
- **tcp_test_client.py** - Test TCP client
- **test_tcp_connection.sh** - Connection test script

### Historical Documentation (Archive)
- **FIXES_APPLIED.md** - Bug fix history
- **RECENT_UPDATES.md** - Recent changes
- **INTERFACE_CONFIG.md** - Interface configuration notes
- **KERNEL_METRICS.md** - Kernel metrics integration notes
- **TEST_BIDIRECTIONAL.md** - Bidirectional tracking tests
- **REAL_DATA_SETUP.md** - Real network setup guide

---

## Quick Reference Card

### Installation
```bash
# Backend
cd backend && python3 -m venv venv
source venv/bin/activate && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Running
```bash
# Terminal 1 - Backend
cd backend && sudo venv/bin/python3 server.py

# Terminal 2 - Frontend
cd frontend && npm start
```

### Testing
```bash
# Quick test
curl http://localhost:50052/api/traffic | jq .

# Generate traffic
curl https://www.google.com
```

### Common Tasks
```bash
# Check packet count
curl -s http://localhost:50052/api/traffic | jq '.packets | length'

# List connections
curl -s http://localhost:50052/api/traffic | jq '.connections | keys'

# Watch connection count
watch -n 1 'curl -s http://localhost:50052/api/traffic | jq ".connections | length"'
```

---

## Documentation Standards

### Maintained Files
All documentation is kept up-to-date with the codebase. Last full review: **December 14, 2025**

### File Formats
- **Markdown (.md)** - All documentation uses GitHub-flavored markdown
- **Code blocks** - Include language hints for syntax highlighting
- **Examples** - Tested and verified working examples

### Update Process
When code changes:
1. Update relevant .md files
2. Test all examples in documentation
3. Update version numbers if needed
4. Review QUICKSTART.md for accuracy

---

## Getting Help

### Documentation Clarification
- Check the relevant .md file first
- Search for keywords (Ctrl+F in browser)
- Try examples in the documentation

### Technical Issues
1. **QUICKSTART.md** - Troubleshooting section
2. **GitHub Issues** - Report bugs
3. **Email** - Contact maintainer

### Contributing Documentation
- Fix typos: Submit pull request
- Add examples: Include tested code
- Suggest improvements: Open issue with "docs" label

---

## Version History

### v1.0 (December 14, 2025)
- ✅ Complete documentation overhaul
- ✅ Removed all gRPC references (switched to HTTP)
- ✅ Added ARCHITECTURE.md
- ✅ Added API.md
- ✅ Updated QUICKSTART.md with actual workflow
- ✅ Enhanced README.md with detailed features
- ✅ All examples tested and verified

### Previous Versions
- v0.x - Initial development (partial documentation)

---

## Maintainer Notes

### Documentation Review Checklist
- [ ] All code examples tested
- [ ] Screenshots up-to-date (if applicable)
- [ ] Links work correctly
- [ ] No broken references
- [ ] Consistent terminology
- [ ] Version numbers current

### Next Review Due
**Target**: Q1 2026 or after major feature release

---

**Last Updated**: December 14, 2025  
**Maintainer**: Emmanuel Scaria  
**Repository**: https://github.com/emmanuelscaria/tcp-viewer
