#!/usr/bin/env python3
"""
Pulls the FULL review list (new reviews, star ratings, text, owner replies)
from the Google Business Profile API (mybusiness.googleapis.com/v4) and
regenerates:
  - data/gbp_reviews.json (complete rewrite: summary + full reviews array)
  - the review card grid on reviews.html
  - the "4.9 on Google · 19 reviews" badge + JSON-LD aggregateRating on every page

This is a heavier sibling to update_review_count.py (which only refreshes the
number via the simpler Places API key). This script needs OAuth 2.0 -- the
Business Profile API rejects plain API keys -- and Google gates access to it
behind a manual, one-time approval request tied to the verified GBP listing.

Until that approval comes through (or the required secrets aren't set yet),
this script exits cleanly with a log message instead of failing the whole
workflow, so the simpler count-only refresh keeps working in the meantime.

Required GitHub secrets (see README.txt "Automated review page" section for
the one-time setup steps to obtain these):
    GOOGLE_OAUTH_CLIENT_ID
    GOOGLE_OAUTH_CLIENT_SECRET
    GOOGLE_OAUTH_REFRESH_TOKEN
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_PATH = os.path.join(SITE_ROOT, "data", "gbp_meta.json")
REVIEWS_PATH = os.path.join(SITE_ROOT, "data", "gbp_reviews.json")
REVIEWS_HTML_PATH = os.path.join(SITE_ROOT, "reviews.html")

TOKEN_URL = "https://oauth2.googleapis.com/token"
STAR_MAP = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}

BADGE_RE = re.compile(r"<strong>[\d.]+</strong> on Google &middot; \d+ reviews?")
JSONLD_RATING_RE = re.compile(
    r'"aggregateRating": \{"@type": "AggregateRating", "ratingValue": "[\d.]+", "reviewCount": "\d+"'
)
REVIEWS_COUNT_TEXT_RE = re.compile(r"\(\d+ reviews\)")
REVIEWS_COUNT_ARIA_RE = re.compile(r"— [\d.]+ stars, \d+ reviews\"")


def get_access_token(client_id, client_secret, refresh_token):
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload["access_token"]


def fetch_all_reviews(account, location, access_token):
    reviews = []
    average_rating = None
    total_review_count = None
    page_token = None
    base_url = f"https://mybusiness.googleapis.com/v4/{account}/{location}/reviews"

    while True:
        params = {"pageSize": "50"}
        if page_token:
            params["pageToken"] = page_token
        url = base_url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        reviews.extend(payload.get("reviews", []))
        if average_rating is None:
            average_rating = payload.get("averageRating")
        if total_review_count is None:
            total_review_count = payload.get("totalReviewCount")

        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    return reviews, average_rating, total_review_count


def format_date(iso_ts):
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return dt.strftime("%b %-d, %Y") if os.name != "nt" else dt.strftime("%b %d, %Y").replace(" 0", " ")


def build_review_record(raw):
    reviewer = raw.get("reviewer", {})
    reply = raw.get("reviewReply")
    return {
        "id": raw.get("reviewId", ""),
        "name": reviewer.get("displayName", "Google user"),
        "photo": reviewer.get("profilePhotoUrl", ""),
        "rating": STAR_MAP.get(raw.get("starRating", ""), 5),
        "date": format_date(raw.get("updateTime") or raw.get("createTime")),
        "comment": raw.get("comment", ""),
        "reply": reply.get("comment", "") if reply else None,
    }


def card_html(r):
    name_esc = html.escape(r["name"])
    initial = name_esc[0].upper() if name_esc else "?"
    comment_esc = html.escape(r["comment"]).replace("'", "&#x27;")
    stars = "&#9733;" * r["rating"]
    reply_html = ""
    if r.get("reply"):
        reply_esc = html.escape(r["reply"]).replace("'", "&#x27;")
        reply_html = f'<div class="gr-reply"><div class="gr-reply-label">Response from the owner</div><p>{reply_esc}</p></div>'
    photo = html.escape(r.get("photo", ""))
    return (
        '<article class="google-review-card">\n'
        '  <header class="gr-head">\n'
        f'    <img class="gr-avatar" src="{photo}" alt="" referrerpolicy="no-referrer" loading="lazy" '
        f"onerror=\"this.replaceWith(Object.assign(document.createElement('div'),"
        f"{{className:'gr-avatar gr-avatar--initial',textContent:'{initial}'}}))\">\n"
        '    <div class="gr-who">\n'
        f'      <div class="gr-name">{name_esc}</div>\n'
        f'      <div class="gr-meta"><span class="gr-stars" aria-label="{r["rating"]} out of 5 stars">{stars}</span>'
        f'<span class="gr-date">{r["date"]}</span></div>\n'
        "    </div>\n"
        '    <a class="gr-source" href="https://maps.google.com/maps?cid=18211092675833852676" target="_blank" '
        'rel="noopener" aria-label="View on Google" title="View on Google">'
        '<span class="gr-source-g" aria-hidden="true"></span></a>\n'
        "  </header>\n"
        f'  <p class="gr-text">{comment_esc}</p>\n'
        f"  {reply_html}\n"
        "</article>"
    )


def update_reviews_html(reviews):
    with open(REVIEWS_HTML_PATH, encoding="utf-8") as f:
        content = f.read()
    cards = "".join(card_html(r) for r in reviews)
    new_grid = f'<div class="google-reviews-grid">{cards}</div>'
    pattern = re.compile(r'<div class="google-reviews-grid">.*?</article></div>', re.DOTALL)
    if not pattern.search(content):
        raise ValueError("Could not find google-reviews-grid block in reviews.html")
    content = pattern.sub(new_grid.replace("\\", "\\\\"), content, count=1)
    with open(REVIEWS_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def update_sitewide_badges(rating_str, count):
    changed = 0
    for dirpath, dirnames, filenames in os.walk(SITE_ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", ".github")]
        for fname in filenames:
            if not fname.endswith(".html"):
                continue
            path = os.path.join(dirpath, fname)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            new_content = BADGE_RE.sub(
                f"<strong>{rating_str}</strong> on Google &middot; {count} reviews", content
            )
            new_content = JSONLD_RATING_RE.sub(
                f'"aggregateRating": {{"@type": "AggregateRating", "ratingValue": "{rating_str}", "reviewCount": "{count}"',
                new_content,
            )
            if fname == "reviews.html":
                new_content = REVIEWS_COUNT_TEXT_RE.sub(f"({count} reviews)", new_content)
                new_content = REVIEWS_COUNT_ARIA_RE.sub(f"— {rating_str} stars, {count} reviews\"", new_content)
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                changed += 1
    return changed


def update_json_summary(rating, count, reviews):
    out = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "average_rating": rating,
        "total_review_count": count,
        "reviews": reviews,
    }
    with open(REVIEWS_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")

    with open(META_PATH, encoding="utf-8") as f:
        meta_content = f.read()
    meta_content = re.sub(r'"average_rating": [\d.]+', f'"average_rating": {rating}', meta_content)
    meta_content = re.sub(r'"total_review_count": \d+', f'"total_review_count": {count}', meta_content)
    with open(META_PATH, "w", encoding="utf-8") as f:
        f.write(meta_content)


def main():
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_OAUTH_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print(
            "SKIPPING full review-card refresh: GOOGLE_OAUTH_CLIENT_ID / "
            "GOOGLE_OAUTH_CLIENT_SECRET / GOOGLE_OAUTH_REFRESH_TOKEN are not all set yet.\n"
            "This is expected until the Business Profile API access request is approved "
            "and the one-time OAuth setup (see README.txt) is complete. The simpler "
            "count-only refresh (update_review_count.py) still runs independently."
        )
        return 0

    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)
    account, location = meta["account"], meta["location"]

    try:
        access_token = get_access_token(client_id, client_secret, refresh_token)
        raw_reviews, avg_rating, total_count = fetch_all_reviews(account, location, access_token)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as e:
        print(f"ERROR: failed to fetch reviews from Business Profile API: {e}", file=sys.stderr)
        # Non-fatal: don't fail the whole workflow over a transient API/approval issue.
        return 0

    if not raw_reviews:
        print("WARNING: Business Profile API returned zero reviews -- leaving existing data untouched.")
        return 0

    reviews = [build_review_record(r) for r in raw_reviews]
    # newest first, matching the existing site order
    reviews.sort(key=lambda r: r["date"], reverse=True)

    rating = avg_rating if avg_rating is not None else round(sum(r["rating"] for r in reviews) / len(reviews), 1)
    count = total_count if total_count is not None else len(reviews)
    rating_str = f"{rating:.1f}"

    update_json_summary(rating, count, reviews)
    update_reviews_html(reviews)
    badge_changed = update_sitewide_badges(rating_str, count)

    print(f"Full review refresh complete: {len(reviews)} reviews, rating={rating_str}, count={count}")
    print(f"Site-wide badge/JSON-LD files touched: {badge_changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
