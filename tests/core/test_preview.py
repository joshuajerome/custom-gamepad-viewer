from core.themes.preview import build_preview_urls

def test_preview_urls():
    urls = build_preview_urls(host="127.0.0.1", port=8000, player=2)
    assert "gamepadviewer.com" in urls.gpv_url
    assert urls.css_url.endswith("controller_css/layout.css")
