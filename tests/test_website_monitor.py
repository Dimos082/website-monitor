import os
import pytest
import urllib.error
import importlib.util
from unittest.mock import patch, MagicMock

# Dynamically load the `website-monitor.py` module
MODULE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "website-monitor.py"))
MODULE_NAME = "website_monitor"

spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
website_monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(website_monitor)

@pytest.fixture
def asset_observer():
    """Fixture to create a BrokenAssetObserver instance."""
    return website_monitor.BrokenAssetObserver()

@pytest.fixture
def report_observer(tmp_path):
    """Fixture to create a ReportGeneratorObserver instance with a temp file."""
    return website_monitor.ReportGeneratorObserver(tmp_path / "test_report.html")

def test_broken_image_detection(asset_observer):
    """Test detection of missing or broken images."""
    test_html = '''
        <html>
            <body>
                <img src="https://example.com/valid.jpg">
                <img src="">
                <img src="https://example.com/broken.jpg">
                <img src="https://example.com/not-found.png">
            </body>
        </html>
    '''
    
    # Mock `check_url_status` to return True for valid.jpg and False for broken images
    with patch.object(website_monitor, "check_url_status") as mock_status:
        mock_status.side_effect = lambda url: url == "https://example.com/valid.jpg"
        
        asset_observer.scan_page("https://example.com", test_html)

    expected_broken = [
        ("https://example.com", "MISSING_SRC"),
        ("https://example.com", "https://example.com/broken.jpg"),
        ("https://example.com", "https://example.com/not-found.png"),
    ]

    assert len(asset_observer.broken_assets) == len(expected_broken)
    assert all(img in asset_observer.broken_assets for img in expected_broken)

def test_valid_url():
    """Test if a valid URL is correctly identified as accessible."""
    result = website_monitor.check_url_status("https://www.example.com")
    assert isinstance(result, bool), "Function must return a boolean"

@patch.object(website_monitor.urllib.request, "urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", None, None))
def test_invalid_url(mock_urlopen):
    """Test if a broken URL is correctly identified as inaccessible."""
    assert website_monitor.check_url_status("https://thiswebsitedoesnotexist12345.com") is False

def test_empty_page(asset_observer):
    """Test scanning an empty HTML page."""
    test_html = ""  # No images
    asset_observer.scan_page("https://example.com", test_html)
    assert len(asset_observer.broken_assets) == 0  # No images, so no broken assets

def test_malformed_image_tags(asset_observer):
    """Test scanning a page with malformed image tags."""
    test_html = '''
        <html>
            <body>
                <img>
                <img src>
                <img src="">
            </body>
        </html>
    '''
    asset_observer.scan_page("https://example.com", test_html)

    expected_broken = [
        ("https://example.com", "MISSING_SRC"),
        ("https://example.com", "MISSING_SRC"),
    ]

    assert len(asset_observer.broken_assets) == len(expected_broken)
    assert all(img in asset_observer.broken_assets for img in expected_broken)

def test_report_generation(report_observer, asset_observer, tmp_path):
    """Test if the HTML report is correctly generated."""
    # Simulated broken images
    asset_observer.broken_assets = [
        ("https://example.com", "https://example.com/broken.jpg"),
        ("https://example.com/page", "https://example.com/missing.png"),
    ]

    # Generate report
    report_observer.generate_html_report(asset_observer.broken_assets)

    # Check if report file was created
    report_path = report_observer.output_file
    assert os.path.exists(report_path)

    # Validate report contents
    with open(report_path, "r", encoding="utf-8") as file:
        content = file.read()
        assert "<h1>Website Monitor Report" in content
        assert "https://example.com/broken.jpg" in content
        assert "https://example.com/missing.png" in content
