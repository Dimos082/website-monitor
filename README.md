# Website Monitor (Recursive Image Checker)

## Overview
`website_monitor.py` is a Python script that recursively scans a website up to a specified depth for broken images. It detects:
- ✅ **Images with missing `src` attributes**
- ✅ **Images that return 404 Not Found errors**
- ✅ **Generates an HTML report listing broken images**
- ✅ **Tracks and reports the total scan duration**

## Features
- **Recursive Scanning**: Scans a website up to a specified depth.
- **Concurrent Image Checks**: Uses concurrent requests to check images for broken links.
- **HTML Report Generation**: Generates a detailed HTML report of broken images.
- **Configurable via Environment Variables**: Allows configuration of log file path, scan timeout, and scan depth.

## Installation
**Requirements:**
- Python 3.x
- `requests` library
- `beautifulsoup4` library

Clone the repository:
```bash
git clone https://github.com/yourusername/website-monitor.git
cd website-monitor
```

## Install the required dependencies:
```bash
pip install requests beautifulsoup4
```

## Usage
```bash
python website-monitor.py --url "https://example.com" --output "report.html" --depth 1 --timeout 10
```

## Environment Variables
You can configure the script using environment variables:
- LOG_FILE: Path to the log file (default: monitor.log).
- SCAN_TIMEOUT: HTTP request timeout in seconds (default: 5).
- SCAN_DEPTH: Depth of recursion (default: 1).

#### Example (Windows Command Prompt)
```bash
set LOG_FILE=C:\path\to\your\logfile.log
set SCAN_TIMEOUT=10
set SCAN_DEPTH=2
python website_monitor.py --url "https://example.com" --output "report.html"
```
#### Example (macOS/Linux Terminal)
```bash
export LOG_FILE="/path/to/your/logfile.log"
export SCAN_TIMEOUT=10
export SCAN_DEPTH=2
python website_monitor.py --url "https://example.com" --output "report.html"
```

## Running Tests
To test the script, use pytest:
```bash
cd website-monitor/tests
pytest
```
