#!/usr/bin/env python3
"""
Updates the site-wide Google review count / rating badge from the Places API (New).

Reads the Place ID from data/gbp_meta.json, calls Place Details (New) requesting
only `rating` and `userRatingCount` (Atmosphere Data SKU -- the cheapest tier that
includes these two fields), then does a targeted find/replace across every HTML
page's visible "4.9 on Google . 19 reviews" badge and JSON-LD aggregateRating
block, plus the two data/gbp_*.json summary fields.

This does NOT touch the individual review cards/text in data/gbp_reviews.json --
Place Details (New) only returns up to 5 recent reviews without owner-reply text,
so refreshing the full review list is intentionally out of scope for this script.
Re-exporting the full list requires the Google Business Profile API instead (OAuth,
verified ownership) -- a separate, heavier lift than this daily count/rating refresh.

Environment:
    GOOGLE_PLACES_API_KEY   required. A *server-side* key restricted to the
                            Places API only (no HTTP-referrer restriction, since
                            this runs from GitHub's runners, not a browser).
                            Store it as a GitHub Actions secret -- never commit it.

Exit codes:
    0  success (whether or not any files changed)
    1  API call failed or returned no rating/count
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PATH = os.path.join(SITE_ROOT, "data", "gbp_meta.json")
REVIEWS_PATH = os.path.join(SITE_ROOT, "data", "gbp_reviews.json")

BADGE_RE = re.compile(r"<strong>[\d.]+</strong> on Google &middot; \d+ reviews?")
JSONLD_RATING_RE = re.compile(
    r'"aggregateRating": \{"@type": "AggregateRating", "ratingValue": "[\d.]+", "reviewCount": "\d+"'
)

# Additional hardcoded spots found on index.html / reviews.html that the simple
# trustbar badge regex above does NOT cover -- title tags, headings, meta
# descriptions, the "eyebrow" link, and the gbp-badge component's aria-label
# and inner spans.
STARS_ON_GOOGLE_RE = re.compile(r"[\d.]+ Stars on Google(?!\s*&middot;)")
EYEBROW_RE = re.compile(r"[\d.]+ Stars on Google &middot; \d+ Reviews")
META_DESC_RE = re.compile(
    r"Read \d+ verified Google reviews for Claiborne Services LLC — [\d.]+ stars\."
)
HERO_SUB_RE = re.compile(
    r"Based on \d+ verified Google reviews from across the Franklin area\."
)
GBP_ARIA_RE = re.compile(
    r'aria-label="View Claiborne Services on Google — [\d.]+ stars, \d+ reviews"'
)
GBP_BADGE_TEXT_RE = re.compile(r'<span class="gbp-badge-text"><strong>[\d.]+</strong></span>')
GBP_BADGE_COUNT_RE = re.compile(r'<span class="gbp-badge-count">\(\d+ reviews\)</span>')


def fetch_rating(place_id, api_key):
    url = "https://places.googleapis.com/v1/places/" + place_id
    req = urllib.request.Request(
        url,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "rating,userRatingCount",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    rating = data.get("rating")
    count = data.get("userRatingCount")
    if rating is None or count is None:
        raise ValueError("Places API response missing rating/userRatingCount: %r" % (data,))
    return float(rating), int(count)


def format_rating(rating):
    return "%.1f" % rating


def update_html_files(rating_str, count):
    changed = 0
    for dirpath, dirnames, filenames in os.walk(SITE_ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", ".github")]
        for fname in filenames:
            if not fname.endswith(".html"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                print("WARNING: skipping non-UTF-8 file: %s" % path, file=sys.stderr)
                continue
            new_content = BADGE_RE.sub(
                "<strong>%s</strong> on Google &middot; %d reviews" % (rating_str, count), content
            )
            new_content = JSONLD_RATING_RE.sub(
                '"aggregateRating": {"@type": "AggregateRating", "ratingValue": "%s", "reviewCount": "%d"' % (rating_str, count),
                new_content,
            )
            new_content = STARS_ON_GOOGLE_RE.sub("%s Stars on Google" % rating_str, new_content)
            new_content = EYEBROW_RE.sub(
                "%s Stars on Google &middot; %d Reviews" % (rating_str, count), new_content
            )
            new_content = META_DESC_RE.sub(
                "Read %d verified Google reviews for Claiborne Services LLC — %s stars." % (count, rating_str),
                new_content,
            )
            new_content = HERO_SUB_RE.sub(
                "Based on %d verified Google reviews from across the Franklin area." % count, new_content
            )
            new_content = GBP_ARIA_RE.sub(
                'aria-label="View Claiborne Services on Google — %s stars, %d reviews"' % (rating_str, count),
                new_content,
            )
            new_content = GBP_BADGE_TEXT_RE.sub(
                '<span class="gbp-badge-text"><strong>%s</strong></span>' % rating_str, new_content
            )
            new_content = GBP_BADGE_COUNT_RE.sub(
                '<span class="gbp-badge-count">(%d reviews)</span>' % count, new_content
            )
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                changed += 1
    return changed


def update_json_summary(path, rating, count):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    new_content = re.sub(r'"average_rating": [\d.]+', '"average_rating": %s' % rating, content)
    new_content = re.sub(r'"total_review_count": \d+', '"total_review_count": %d' % count, new_content)
    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def main():
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_PLACES_API_KEY environment variable is not set.", file=sys.stderr)
        return 1

    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)
    place_id = meta["place_id"]

    try:
        rating, count = fetch_rating(place_id, api_key)
    except (urllib.error.URLError, ValueError, KeyError) as e:
        print("ERROR: failed to fetch rating from Places API: %s" % e, file=sys.stderr)
        return 1

    rating_str = format_rating(rating)
    print("Fetched from Places API: rating=%s, userRatingCount=%d" % (rating_str, count))

    html_changed = update_html_files(rating_str, count)
    meta_changed = update_json_summary(META_PATH, rating, count)
    reviews_changed = update_json_summary(REVIEWS_PATH, rating, count)

    print("HTML files updated: %d" % html_changed)
    print("data/gbp_meta.json updated: %s" % meta_changed)
    print("data/gbp_reviews.json summary updated: %s" % reviews_changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
