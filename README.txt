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
Automated review count (GitHub Action)
--------------------------------------------------------------------
.github/workflows/update-reviews.yml runs daily (and can be triggered
manually from the Actions tab) to refresh the "4.9 on Google - 19 reviews"
badge and matching JSON-LD aggregateRating block on every page, plus the
average_rating/total_review_count fields in data/gbp_meta.json and
data/gbp_reviews.json. It calls the Places API (New) Place Details endpoint
for just the `rating` and `userRatingCount` fields (Atmosphere Data tier --
a few cents per 1,000 calls; at ~30 calls/month this is effectively free
and comes out of the standard $200/month Google Cloud credit).

One-time setup:
  1. In Google Cloud Console, create a NEW API key restricted to the
     Places API only, with NO website/HTTP-referrer restriction (this key
     runs from GitHub's servers, not a browser -- keep it separate from
     the client-side autocomplete key used in contact.html).
  2. In the GitHub repo: Settings -> Secrets and variables -> Actions ->
     New repository secret, named GOOGLE_PLACES_API_KEY, value = that key.
  3. That's it -- the workflow runs on its own schedule from then on.

This script intentionally does NOT refresh the individual review
cards/text in data/gbp_reviews.json (new reviews, reply text, reviewer
photos) -- Place Details (New) only returns up to 5 recent reviews without
owner-reply text. Re-exporting the full review list requires the Google
Business Profile API instead (OAuth, verified ownership), a heavier,
separate setup from this daily count/rating refresh.

--------------------------------------------------------------------
Questions
--------------------------------------------------------------------
Site content owner:  Shawn Claiborne
Email:               shawn@claiborneservicesllc.com
Phone:               (615) 900-4501
