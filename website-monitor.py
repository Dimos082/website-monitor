#!/usr/bin/env python3

import os, urllib.request, urllib.error, argparse, re
from urllib.parse import urljoin
from datetime import datetime

# Constant for logger Setup
LOG_FILE = "monitor.log"

def log_message(message):
    """Logs messages to both console and a log file."""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")

class BrokenAssetObserver:
    """Checks for missing images and assets on a single webpage."""
    def __init__(self):
        self.broken_assets = []

    def scan_page(self, page_url, content):
        """Scans the HTML content for missing or broken images."""
        img_tags = re.findall(r'<img[^>]+>', content)

        for img_tag in img_tags:
            src_match = re.search(r'src="([^"]*)"', img_tag)
            src = src_match.group(1) if src_match else ""

            full_url = urljoin(page_url, src) if src else "MISSING_SRC"

            if not src or not self._is_url_valid(full_url):
                self.broken_assets.append((page_url, full_url))
                log_message(f"[BROKEN IMAGE] {full_url} (Found on: {page_url})")

    def _is_url_valid(self, url):
        """Checks if the image URL is accessible."""
        if url == "MISSING_SRC":
            return False
        return check_url_status(url)

class ReportGeneratorObserver:
    """Generates a report summarizing the findings."""
    def __init__(self, output_file):
        self.output_file = output_file

    def generate_html_report(self, broken_assets):
        """Creates an HTML report summarizing broken images."""
        total_broken_assets = len(broken_assets)

        html_content = f"""
        <html>
        <head>
            <title>Website Monitor Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .error {{ color: red; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Website Monitor Report - {datetime.now()}</h1>
            
            <h2>Summary</h2>
            <p>Total Broken Images: <span class="error">{total_broken_assets}</span></p>
            
            <h2>Broken Images</h2>
            <table>
                <tr><th>Broken Image URL</th><th>Found On Page</th></tr>
        """
        for page, img in broken_assets:
            html_content += f'<tr><td>{img}</td><td><a href="{page}" target="_blank">{page}</a></td></tr>'

        html_content += """
            </table>
        </body>
        </html>
        """

        with open(self.output_file, "w", encoding="utf-8") as file:
            file.write(html_content)
        log_message(f"[REPORT GENERATED] {self.output_file}")

def check_url_status(url):
    """Checks if a URL is accessible, using a User-Agent header."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False

def main():
    """Main function to start the website monitoring process."""
    parser = argparse.ArgumentParser(description="Monitor a single webpage for broken images.")
    parser.add_argument("--url", required=True, help="The URL of the webpage to monitor.")
    parser.add_argument("--output", default="report.html", help="Path to save the HTML report.")
    args = parser.parse_args()

    log_message(f"[START] Scanning Page: {args.url}")

    asset_observer = BrokenAssetObserver()
    report_observer = ReportGeneratorObserver(args.output)

    try: # Fetch the page content
        request = urllib.request.Request(args.url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=5) as response:
            content = response.read().decode('utf-8', errors='ignore')

        asset_observer.scan_page(args.url, content)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        log_message(f"[ERROR] Unable to access {args.url} ({e})")
        return

    report_observer.generate_html_report(asset_observer.broken_assets) # Generate final report
    log_message("[DONE] Website Monitoring Completed.")

if __name__ == "__main__":
    main()