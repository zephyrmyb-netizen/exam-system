from pathlib import Path

from scripts.beta_gateway import cache_headers_for


def test_beta_gateway_revalidates_the_html_shell_on_every_visit(tmp_path: Path):
    index = tmp_path / "index.html"

    assert cache_headers_for(index, tmp_path) == {
        "Cache-Control": "no-cache",
        "Cloudflare-CDN-Cache-Control": "no-cache",
    }


def test_beta_gateway_keeps_content_hashed_assets_immutable(tmp_path: Path):
    asset = tmp_path / "assets" / "index-abc123.js"

    assert cache_headers_for(asset, tmp_path) == {
        "Cache-Control": "public, max-age=31536000, immutable",
    }
