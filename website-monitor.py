#!/usr/bin/env python3

"""
ReadMe: https://github.com/Dimos082/website-monitor/
Description:
    Recursively crawls a website (up to a specified depth), scanning each page
    for broken images using Requests and BeautifulSoup. Gathers results through
    an Observer Pattern and generates an HTML report.
Usage Example:
    python website_monitor.py --url "https://example.com" --output "report.html" --depth 1 --timeout 10
"""

import argparse, requests, sys, os, concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from collections import deque

LOG_FILE = os.getenv("LOG_FILE", "website-monitor.log")

def log_message(msg): # Logs to the console and appends to a log file.
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as lf:
        lf.write(f"{datetime.now()} - {msg}\n")

class ObserverBase:
    """Abstract base class for observers. They receive broken image data from pages."""
    def update(self, page_url, broken_images): # Called once per visited page, with a list of that page's broken images.
        raise NotImplementedError("Subclasses must implement 'update'.")

class BrokenAssetObserver(ObserverBase): # BROKEN ASSET OBSERVER
    """Collects broken images from each page for later reporting or usage"""
    def __init__(self):
        self.broken_assets = []

    def update(self, page_url, broken_images): # Appends the broken images from page_url to our internal list.
        self.broken_assets.extend((page_url, img_url) for img_url in broken_images)

class ReportGeneratorObserver(ObserverBase): # REPORT GENERATOR OBSERVER
    """Gathers broken image data and produces an HTML report."""
    def __init__(self, output_file):
        self.output_file = output_file
        self.broken_assets = []
        self.start_time = None
        self.end_time = None

    def update(self, page_url, broken_images): # Saves broken images so they can be reported at the end.
        self.broken_assets.extend((page_url, img_url) for img_url in broken_images)

    def set_start_time(self): # Records the start time of the scan.
        self.start_time = datetime.now()

    def set_end_time(self): # Records the end time of the scan.
        self.end_time = datetime.now()

    def generate_report(self): # Produces a final HTML file listing all broken images discovered.
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_broken = len(self.broken_assets)
        duration = (self.end_time - self.start_time).total_seconds()

        html = [
            "<html><head>",
            "<meta charset='utf-8'>",
            "<title>Broken Images Report</title>",
            "<style>",
            "  body { font-family: Arial, sans-serif; margin: 20px; }",
            "  table { border-collapse: collapse; width: 100%; }",
            "  th, td { border: 1px solid #ccc; padding: 8px; }",
            "  th { background-color: #f9f9f9; }",
            "  .error { color: red; font-weight: bold; }",
            "</style></head><body>",
            f"<h1>Broken Images Report</h1>",
            f"<p>Report generated on: <strong>{now_str}</strong></p>",
            "<h2>Summary</h2>",
            f"<p>Broken Images: <span class='error'>{total_broken}</span></p>",
            f"<p>Scan Duration: <span class='error'>{duration:.2f} seconds</span></p>",
            "<table>",
            "<tr><th>Broken Image URL</th><th>Found on Page</th></tr>"
        ]

        for page, img in self.broken_assets:
            html.append(f"<tr><td>{img}</td><td><a href='{page}'>{page}</a></td></tr>")

        html.append("</table></body></html>")
        final_output = "\n".join(html)

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(final_output)

        log_message(f"[REPORT GENERATED] {self.output_file}")

def is_image_ok(session, url, timeout=5): # Image check utility 
    if not url: # Returns True if URL is reachable (status < 400), else False.
        return False

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False

    try:
        response = session.get(url, timeout=timeout)
        return response.status_code < 400
    except requests.RequestException:
        return False

class WebsiteScanner: # Website scanner with depth
    """Crawls a website up to `depth` levels, scanning each page for broken images.
    Uses BFS to avoid deep recursion. Observers are notified for each page."""
    def __init__(self, base_url, observers, depth=1, timeout=5):
        self.base_url = base_url
        self.observers = observers
        self.depth = depth
        self.timeout = timeout
        self.visited = set()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        parsed_base = urlparse(self.base_url)
        self.base_domain = parsed_base.netloc

    def scan(self): # Orchestrates BFS across the website up to the specified depth.
        log_message(f"[START] Scanning up to depth={self.depth}, base URL: {self.base_url}")
        queue = deque([(self.base_url, 0)])
        self.visited.add(self.base_url)

        for obs in self.observers:
            if hasattr(obs, "set_start_time"):
                obs.set_start_time()

        while queue:
            current_url, current_depth = queue.popleft()
            log_message(f"[CRAWLING] {current_url} (depth={current_depth})")

            html = self._fetch_page(current_url) # Fetch and parse page
            if not html:
                continue  # If fetch failed or non-HTML, skip

            broken_images = self._scan_images(current_url, html) # Detect broken images for this page

            for obs in self.observers: # Notify observers
                obs.update(current_url, broken_images)

            if current_depth < self.depth: # If we haven't reached depth limit, enqueue new links from this page
                new_links = self._extract_links(current_url, html)
                for link in new_links:
                    if link not in self.visited:
                        self.visited.add(link)
                        queue.append((link, current_depth + 1))

        for obs in self.observers:
            if hasattr(obs, "set_end_time"):
                obs.set_end_time()

        log_message("[DONE] Website scan completed.")

    def _fetch_page(self, url): # Uses requests to get HTML from the given URL.
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if "text/html" not in resp.headers.get("Content-Type", ""):
                log_message(f"[WARNING] Non-HTML content: {url}")
                return None
            return resp.text
        except requests.RequestException as e:
            log_message(f"[ERROR] {e} while accessing {url}")
            return None # Returns None if an error or non-HTML.

    def _scan_images(self, page_url, html_content): # Parses the page for <img> tags checks each image in parallel, returns a list of broken.
        soup = BeautifulSoup(html_content, "html.parser")
        img_tags = soup.find_all("img")
 
        image_urls = [urljoin(page_url, tag.get("src", "")) for tag in img_tags if tag.get("src")] # Build absolute URLs for each <img>

        broken = [] # Check concurrency for images
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_map = {executor.submit(is_image_ok, self.session, img_url, self.timeout): img_url for img_url in image_urls}
            for future in concurrent.futures.as_completed(future_map):
                img_url = future_map[future]
                try:
                    if not future.result():
                        broken.append(img_url)
                        log_message(f"[BROKEN IMAGE] {img_url} (page: {page_url})")
                except Exception as exc:
                    log_message(f"[DEBUG] Exception while checking {img_url}: {exc}")

        return broken

    def _extract_links(self, page_url, html_content): # Finds internal links (<a href="...">) in the page that match the base domain
        soup = BeautifulSoup(html_content, "html.parser")
        links = soup.find_all("a", href=True)
        new_links = []
        for tag in links:
            href = tag["href"]
            full_link = urljoin(page_url, href)
            parsed = urlparse(full_link)
            if parsed.netloc == self.base_domain and parsed.scheme in ("http", "https"): # Only follow links within the same domain
                new_links.append(full_link)
        return new_links  # Returns a list of absolute URLs for BFS queueing.

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Recursively scan a website (up to --depth) for broken images."
    )
    parser.add_argument("--url", required=True, help="Base URL to start scanning.")
    parser.add_argument("--output", default="report.html", help="HTML report output.")
    parser.add_argument("--depth", type=int, default=1, help="Depth of recursion (default=1).")
    parser.add_argument("--timeout", type=int, default=5, help="HTTP request timeout (seconds).")
    return parser.parse_args()

def main():
    args = parse_arguments() 
    asset_observer = BrokenAssetObserver()  
    report_observer = ReportGeneratorObserver(args.output)
    scanner = WebsiteScanner(
        base_url=args.url,
        observers=[asset_observer, report_observer],
        depth=args.depth,
        timeout=args.timeout
    )
    scanner.scan()
    report_observer.generate_report()

if __name__ == "__main__":
    main()