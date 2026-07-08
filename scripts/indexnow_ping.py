#!/usr/bin/env python3
"""
Notify IndexNow (Bing, and any other participating search engines) that
the site's pages may have changed, by submitting the full URL list from
sitemap.xml in a single bulk request.

Runs automatically via .github/workflows/indexnow-ping.yml on every push
to main, and via the review-sync workflow after it commits changes. Safe
to run repeatedly -- IndexNow has no penalty for re-submitting the same
URLs, and this always submits the same site-wide list rather than trying
to diff exactly which pages changed.

No secrets required: the key is public by design (it's proven by hosting
{key}.txt at the domain root, which is already in this repo).
"""

import json
import re
import sys
import urllib.request
import urllib.error

HOST = "claiborneservicesllc.com"
KEY = "0f6f2c5e79b3453cba4647aaecd50992"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP_PATH = "sitemap.xml"


def get_urls_from_sitemap(path):
    with open(path, encoding="utf-8") as f:
        xml = f.read()
    urls = re.findall(r"<loc>(.*?)</loc>", xml)
    if not urls:
        raise ValueError(f"No <loc> entries found in {path}")
    return urls


def submit(urls):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow submission: HTTP {resp.status} for {len(urls)} URLs")
            return resp.status
    except urllib.error.HTTPError as e:
        # IndexNow returns 200/202 on success; treat other codes as non-fatal
        # so a hiccup here never fails the whole workflow run.
        print(f"IndexNow submission returned HTTP {e.code}: {e.reason}")
        return e.code
    except Exception as e:
        print(f"IndexNow submission failed (non-fatal): {e}")
        return None


def main():
    urls = get_urls_from_sitemap(SITEMAP_PATH)
    print(f"Submitting {len(urls)} URLs from {SITEMAP_PATH} to IndexNow...")
    status = submit(urls)
    if status not in (200, 202):
        # Log clearly but always exit 0 -- IndexNow issues should never
        # block or fail the deploy/review-sync workflow.
        print("Note: IndexNow did not confirm success, but continuing.")
    sys.exit(0)


if __name__ == "__main__":
    main()
