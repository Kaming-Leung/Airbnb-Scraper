# scrapingbee_transport.py
from __future__ import annotations
from urllib.parse import quote

SCRAPINGBEE_HTTPS_PROXY = "https://proxy.scrapingbee.com:8887"  # HTTPS proxy endpoint :contentReference[oaicite:2]{index=2}

def make_scrapingbee_proxy_url(
    api_key: str,
    *,
    render_js: bool = False,
    premium_proxy: bool = True,
    country_code: str | None = "US",
) -> str:
    """
    ScrapingBee Proxy Mode format:
      https://<API_KEY>:render_js=False&premium_proxy=True&country_code=US@proxy.scrapingbee.com:8887
    (username=API key, password=querystring params) :contentReference[oaicite:3]{index=3}
    """
    params = {
        "render_js": "True" if render_js else "False",
        "premium_proxy": "True" if premium_proxy else "False",
    }
    if country_code:
        params["country_code"] = country_code

    # password is a querystring, but must be safe inside URL userinfo
    password = "&".join([f"{k}={v}" for k, v in params.items()])
    password_escaped = quote(password, safe="=&")  # keep & and = readable

    return f"{SCRAPINGBEE_HTTPS_PROXY.replace('https://', f'https://{api_key}:{password_escaped}@')}"
