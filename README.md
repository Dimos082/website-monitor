# Website Monitor (Singe-page image checker)

## Overview
`website_monitor.py` is a simple Python script that scans a **single webpage** for **broken images**. It detects:
- ✅ **Images with missing `src` attributes**
- ✅ **Images that return 404 Not Found errors**
- ✅ **Generates an HTML report listing broken images**

## Installation
**Requirements:**
- Python 3.x (no external dependencies)

Clone the repository:
```bash
git clone https://github.com/yourusername/website-monitor.git
cd website-monitor
```

## Usage
```bash
python website_monitor.py --url "https://example.com" --output "report.html"
```

## Running Tests
To test the script, use pytest:
```bash
cd website-monitor/tests
pytest
```