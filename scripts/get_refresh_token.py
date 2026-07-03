#!/usr/bin/env python3
"""
ONE-TIME LOCAL SETUP SCRIPT -- run this on your own computer, not in GitHub
Actions. It walks Shawn through the interactive Google OAuth consent screen
once, then prints a long-lived refresh token to paste into GitHub secrets.

Prerequisites (see README.txt "Automated review page" section for the full
walkthrough):
  1. Google's approval for Business Profile API access must already be
     granted for this project (this is a separate manual request -- this
     script does not submit that request for you).
  2. An OAuth 2.0 Client ID of type "Desktop app" created in Google Cloud
     Console -> APIs & Services -> Credentials, with the account that
     manages the Claiborne Services Google Business Profile.

Usage:
    pip install google-auth-oauthlib
    python3 scripts/get_refresh_token.py --client-id YOUR_ID --client-secret YOUR_SECRET

A browser window will open asking you to log in and grant access. After you
approve, this script prints your CLIENT_ID, CLIENT_SECRET, and REFRESH_TOKEN.
Add all three to the GitHub repo as secrets:
    Settings -> Secrets and variables -> Actions -> New repository secret
        GOOGLE_OAUTH_CLIENT_ID      = your client id
        GOOGLE_OAUTH_CLIENT_SECRET  = your client secret
        GOOGLE_OAUTH_REFRESH_TOKEN  = the refresh token this script prints

The refresh token does not expire under normal use, so this is a one-time
step -- the GitHub Action mints short-lived access tokens from it on every
run automatically.
"""
import argparse
import sys

SCOPES = ["https://www.googleapis.com/auth/business.manage"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    args = parser.parse_args()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "Missing dependency. Run:\n"
            "    pip install google-auth-oauthlib\n"
            "then try again.",
            file=sys.stderr,
        )
        return 1

    client_config = {
        "installed": {
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    print("A browser window will open. Log in with the Google account that")
    print("manages the Claiborne Services Business Profile, and approve access.\n")
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 70)
    print("Success. Add these three values as GitHub repository secrets:")
    print("(Settings -> Secrets and variables -> Actions -> New repository secret)")
    print("=" * 70)
    print(f"GOOGLE_OAUTH_CLIENT_ID      = {args.client_id}")
    print(f"GOOGLE_OAUTH_CLIENT_SECRET  = {args.client_secret}")
    print(f"GOOGLE_OAUTH_REFRESH_TOKEN  = {creds.refresh_token}")
    print("=" * 70)
    print("\nKeep this output private -- the refresh token grants ongoing")
    print("access to manage/read your Business Profile reviews.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
