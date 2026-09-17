#!/usr/bin/env python3
"""
URL-Wall core logic.
"""

import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

import urlwall.config as config

__all__ = [
    "getCanonicalHost",
    "isUrlAllowed",
    "isWebURL",
    "niceHost",
    "openURL",
    "unwrap",
    "writeWarningHTML",
]


def isWebURL(url):
    """Check whether url is most likely an actual web URL."""
    up = urllib.parse.urlparse(url)
    return up.scheme in ('http', 'https', 'ftp') and up.netloc


def getCanonicalHost(url):
    """Extract canonical host from a URL (no www., no trailing dot, no port)."""
    host = url
    if '/' in host:
        purl = urllib.parse.urlparse(host)
        host = purl.netloc
    # Strip port if present
    if ':' in host:
        host = host.rsplit(':', 1)[0]
    host = host.lower().strip('.')
    if host.startswith('www.'):
        host = host[4:]
    return host


def niceHost(url):
    """Human-readable host name for display."""
    up = urllib.parse.urlparse(url)
    host = up.netloc.lower()
    if host.startswith('www.'):
        host = host[4:]
    if host.endswith('.safelinks.protection.outlook.com'):
        host = 'safelinks.outlook.com'
    return host


def unwrap(url):
    """Unwrap redirect chains (Cisco web proxy, Outlook safelinks, etc.).

    Returns a list of all URLs encountered during unwrapping.
    """
    urls = []
    while True:
        urls.append(url)
        up = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(up.query)

        # Cisco web proxy: https://secure-web.cisco.com/...#...
        if up.netloc == 'secure-web.cisco.com':
            m = re.match(r'^([^#]+)/(.+)$', url)
            if m:
                url1, url2 = m.groups()
                url2 = urllib.parse.unquote(url2)
                if isWebURL(url1) and isWebURL(url2):
                    url = url2
                    continue

        # Common redirect query params
        for q in ('url', 'target', 'rd'):
            if q in query and query[q] and isWebURL(query[q][0]):
                url = query[q][0]
                break
        else:
            break

    return urls


def isUrlAllowed(url, _seen=None, _depth=0):
    """Check if a URL is allowed, unwrapping redirect chains and query params."""
    if _seen is None:
        _seen = set()
    if _depth > 20 or url in _seen:
        # Prevent infinite recursion from circular redirects
        return False
    _seen.add(url)

    # First unwrap query params to find nested URLs
    up = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(up.query)
    for key in ('q', 'url'):
        for val in query.get(key, []):
            if val.startswith('http://') or val.startswith('https://'):
                return isUrlAllowed(val, _seen, _depth + 1)

    # Then check the canonical host
    host = getCanonicalHost(url)
    return config.getConfig().isAllowed(host)


def writeWarningHTML(urls):
    """Generate a warning HTML page showing the URL chain.

    Returns the path to a temp file containing the rendered page.
    """
    assert urls
    url_pairs = list((niceHost(url), url) for url in urls)

    # Read template from package resources (works when installed via pip)
    template_path = Path(__file__).parent / "html" / "template.html"
    text = template_path.read_text(encoding="utf-8")

    bg_path = Path(__file__).parent / "html" / "bg.jpg"
    bgurl = "file://" + str(bg_path.resolve())

    # The final URL for the "Go to" button
    final_url = url_pairs[-1][1]

    for k, v in {
        "backgroundimage": bgurl,
        "URLS": "",  # Old template uses JS to build the chain
        "URL": final_url,
    }.items():
        text = text.replace("{{" + k + "}}", v)

    fd, fn = tempfile.mkstemp(prefix="warning-", suffix=".html")
    os.write(fd, text.encode("utf-8"))
    os.close(fd)

    return fn


def openURL(url):
    """Open a URL through the URL-Wall gate."""
    try:
        # Normalize: ensure https scheme
        if not url.startswith('http'):
            if not url.startswith('//'):
                url = '//' + url
            url = 'https:' + url

        # Log
        log_fn = config.getConfig().logFile
        with open(log_fn, 'a') as log:
            log.write(f'{url}\n')

        # Unwrap redirect chains
        chain = unwrap(url)

        # Check if any URL in the chain is allowed
        allowed = False
        for chain_url in chain:
            if isUrlAllowed(chain_url):
                allowed = True
                break
        if not allowed:
            # Show warning page with the full chain
            tfn = writeWarningHTML(chain)
            url = tfn

        browser = config.getConfig().getBrowser()
        subprocess.call(['/usr/bin/open', '-a', browser, url])
    except Exception as e:
        # Log error but still open to avoid losing the URL entirely
        print(f'URL-Wall error: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Open in default browser (not user's preferred) as a safe fallback
        subprocess.call(['/usr/bin/open', url])
