#!/usr/bin/env python3
"""
Publishes scheduled blog posts as their dates arrive.

Blog post HTML files (blog/*.html) are all committed to the repo up
front -- this script never creates post content. What it does is make
a post DISCOVERABLE: add its card to blog/index.html and its URL to
sitemap.xml, once its scheduled date has arrived.

Runs daily via .github/workflows/publish-blog-post.yml (not just on the
1st) so a single missed/delayed cron run can't push a post a full month
late -- it publishes anything with publish_date <= today that isn't
already marked published, then commits.

Safe to run repeatedly: if nothing is due, it makes no changes and the
workflow's commit step just no-ops.
"""

import json
import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCHEDULE_PATH = ROOT / "data" / "blog_schedule.json"
BLOG_INDEX_PATH = ROOT / "blog" / "index.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
BASE = "https://claiborneservicesllc.com"

MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def format_date(iso_date):
    y, m, d = iso_date.split("-")
    return f"{MONTH_NAMES[int(m)]} {int(d)}, {y}"


def load_schedule():
    with open(SCHEDULE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_schedule(schedule):
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)


def get_due_posts(schedule, today):
    return [
        p for p in schedule
        if not p["published"] and datetime.strptime(p["publish_date"], "%Y-%m-%d").date() <= today
    ]


def add_to_blog_index(post):
    """blog/index.html lives inside blog/, so its own image/link paths
    are relative to that folder: ../assets/... for images, slug.html
    (no blog/ prefix) for links to sibling post files."""
    html = BLOG_INDEX_PATH.read_text(encoding="utf-8")
    pub_date_human = format_date(post["publish_date"])
    card = f'''<div class="blog-card">
      <span class="blog-card-img"><img src="../assets/img/jobs/{post["hero_img"]}" alt="{post["title"]}" loading="lazy"></span>
      <div class="blog-card-body">
        <p class="eyebrow">{post["category"]} &middot; {pub_date_human}</p>
        <h3><a href="/blog/{post["slug"]}">{post["title"]}</a></h3>
        <p>{post["dek"]}</p>
        <a class="more" href="/blog/{post["slug"]}">Read More &rarr;</a>
      </div>
    </div>\n    '''

    marker = '<div class="blog-grid">'
    idx = html.index(marker) + len(marker)
    html = html[:idx] + "\n      " + card + html[idx:]
    BLOG_INDEX_PATH.write_text(html, encoding="utf-8")


def add_to_sitemap(post):
    xml = SITEMAP_PATH.read_text(encoding="utf-8")
    url = f"{BASE}/blog/{post['slug']}"
    if url in xml:
        return
    entry = (
        "  <url>\n"
        f"    <loc>{url}</loc>\n"
        f"    <lastmod>{post['publish_date']}</lastmod>\n"
        "    <priority>0.6</priority>\n"
        "  </url>\n"
    )
    xml = xml.replace("</urlset>", entry + "</urlset>")
    SITEMAP_PATH.write_text(xml, encoding="utf-8")


def main():
    today = date.today()
    schedule = load_schedule()
    due = get_due_posts(schedule, today)

    if not due:
        print(f"No posts due for publishing as of {today.isoformat()}.")
        return

    for post in due:
        print(f"Publishing: {post['slug']} (scheduled {post['publish_date']})")
        add_to_blog_index(post)
        add_to_sitemap(post)
        post["published"] = True

    save_schedule(schedule)
    print(f"Published {len(due)} post(s). Schedule file updated.")


if __name__ == "__main__":
    main()
