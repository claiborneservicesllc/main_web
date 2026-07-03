Claiborne Services LLC — Website
==================================

This is a fully static website. To publish it, upload the entire folder
contents (everything inside claiborne_site/) to your web host's public
directory (public_html/, htdocs/, or the root of the domain).

Recommended entry point: index.html
Production domain:        https://claiborneservicesllc.com

All canonical URLs, sitemap entries, robots.txt, JSON-LD schema, and
Open Graph tags point to claiborneservicesllc.com.

--------------------------------------------------------------------
Contact form
--------------------------------------------------------------------
The "Request a Free Quote" form on contact.html submits to Formspree:

    https://formspree.io/f/mojokloa

Submissions email:  shawn@claiborneservicesllc.com
Dashboard:          https://formspree.io/forms

The FIRST submission after going live will trigger a one-time Formspree
verification email. Click the confirmation link in that email so future
submissions arrive in your inbox without a "please verify" prompt.

Free tier limit: 50 submissions/month.

Photos: customers are instructed on the contact page to text photos to
(615) 900-4501 rather than upload them (Formspree free tier does not
accept file attachments).

--------------------------------------------------------------------
File map
--------------------------------------------------------------------
index.html                 Homepage
about.html                 About / family story
contact.html               Contact + quote form
pricing.html               Master rate card
services/*.html            Individual service pages
service-area/*.html        City / area landing pages
faq.html, financing.html   Supporting pages
discounts.html             Community discount programs
equipment.html             Equipment fleet
insurance.html             Insurance / licensing
gallery.html, reviews.html Media + testimonials
partners.html              Trusted vendor partners
projects.html, projects/   Recent project detail pages
blog/                      Articles + tips
es/index.html              Spanish landing page
assets/css/styles.css      All styles
assets/js/main.js          Nav, lightbox, form handler
assets/img/                Logos, favicons, banners, job photos
data/gbp_*.json            Google Business Profile review data
sitemap.xml, robots.txt    SEO files
404.html                   Custom not-found page

--------------------------------------------------------------------
Editing prices, copy, or photos
--------------------------------------------------------------------
Every page is a standalone .html file. To change a headline, price, or
photo, open the page in any text editor (or hand it to your Thryv team)
and edit directly. No build step required for HTML edits.

Phone number appears throughout — global find-and-replace on
(615) 900-4501 if it ever needs to update.

--------------------------------------------------------------------
Automated review page (GitHub Action)
--------------------------------------------------------------------
.github/workflows/update-reviews.yml runs twice daily -- 12:00 AM and
12:00 PM Central -- (and can be triggered manually from the Actions tab)
and does two things in sequence:

  1. ALWAYS: refreshes the "4.9 on Google - 19 reviews" badge and matching
     JSON-LD aggregateRating block on every page, via
     scripts/update_review_count.py (Places API, New -- Place Details
     endpoint, `rating`/`userRatingCount` fields only, Atmosphere Data
     tier, a few cents per 1,000 calls). Works today, already set up.

  2. IF CONFIGURED: refreshes the actual review cards on reviews.html --
     new reviews, star ratings, text, owner replies -- via
     scripts/update_reviews_full.py (Google Business Profile API). Until
     the one-time setup below is complete, this step just logs a message
     and does nothing; it will never fail the workflow.

=== Part 1: count/rating only (already live, no action needed) ===
  1. In Google Cloud Console, create a NEW API key restricted to the
     Places API only, with NO website/HTTP-referrer restriction (this key
     runs from GitHub's servers, not a browser -- keep it separate from
     the client-side autocomplete key used in contact.html).
  2. In the GitHub repo: Settings -> Secrets and variables -> Actions ->
     New repository secret, named GOOGLE_PLACES_API_KEY, value = that key.

=== Part 2: full review cards (one-time setup, do when ready) ===
Place Details (New) only returns up to 5 recent reviews and no owner-reply
text, so pulling the full review list -- new reviews, replies, avatars --
needs the Business Profile API instead. That API requires OAuth (not an
API key) and Google requires a separate, manual, one-time approval before
any project can call it. Steps:

  1. Confirm the Google Business Profile listing (not just the website)
     has been verified and active for 60+ days -- Google checks this.
  2. In Google Cloud Console (same project as the Places key):
       - Enable "My Business Business Information API" and
         "My Business Account Management API".
       - Configure the OAuth consent screen (External or Internal,
         whichever applies) if not already done.
       - Create an OAuth 2.0 Client ID of type "Desktop app" under
         APIs & Services -> Credentials. Save the client ID and secret.
  3. Submit Google's access request: search "Google Business Profile API
     access request form" (Google periodically renames/moves this form),
     choose "Application for Basic API Access," and fill it in with:
       - This Google Cloud project's project NUMBER (not name/ID).
       - An email address that is an Owner or Manager on the Business
         Profile listing.
       - A short explanation, e.g. "Automated daily sync of review
         count and review content to our official business website,
         claiborneservicesllc.com."
     Approval typically takes anywhere from a few days to a few weeks.
     You'll get an email when it's approved or if more info is needed.
  4. Once approved, run the local helper script ONE TIME on your own
     computer (not in GitHub Actions) to complete the OAuth login and
     get a refresh token:
         pip install google-auth-oauthlib
         python3 scripts/get_refresh_token.py --client-id YOUR_ID --client-secret YOUR_SECRET
     A browser window opens -- log in with the Google account that
     manages the Business Profile and approve access. The script then
     prints three values.
  5. Add all three as GitHub repository secrets (Settings -> Secrets and
     variables -> Actions -> New repository secret):
         GOOGLE_OAUTH_CLIENT_ID
         GOOGLE_OAUTH_CLIENT_SECRET
         GOOGLE_OAUTH_REFRESH_TOKEN
  6. That's it -- the next scheduled run (or a manual "Run workflow" from
     the Actions tab) will pick up the secrets and start refreshing the
     full review cards automatically. No code changes needed.

Schedule note: GitHub Actions cron is fixed UTC with no daylight-saving
awareness. The workflow is set to 05:00/17:00 UTC, which is 12:00 AM/PM
Central Daylight Time (spring-summer). During Central Standard Time
(roughly Nov-Mar) this drifts about an hour to 11 PM/11 AM Central --
a small seasonal shift that's normal to accept rather than maintain two
separate cron schedules.

--------------------------------------------------------------------
Questions
--------------------------------------------------------------------
Site content owner:  Shawn Claiborne
Email:               shawn@claiborneservicesllc.com
Phone:               (615) 900-4501
