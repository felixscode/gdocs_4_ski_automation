#!/usr/bin/env python3
"""
Script to regenerate yagmail OAuth2 credentials.
This will open a browser window for you to authorize the app.
"""
import yagmail

# Email address
email = "kursanmeldungengoetting@gmail.com"

# Path to store the new credentials
oauth_file = "data/dependencies/client_secret_mail_new.json"

print(f"Generating OAuth2 credentials for {email}")
print(f"A browser window will open. Please sign in and authorize the app.")
print(f"New credentials will be saved to: {oauth_file}")

# This will open a browser for OAuth2 authorization
yag = yagmail.SMTP(email, oauth2_file=oauth_file)

print("\n✓ OAuth2 credentials generated successfully!")
print(f"Replace the old file with: {oauth_file}")

