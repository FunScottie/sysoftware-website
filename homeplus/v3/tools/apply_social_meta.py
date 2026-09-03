#!/usr/bin/env python3
"""Add site-wide Open Graph and X metadata to hand-authored root pages."""

from html import unescape
import re

from sync_team import PREVIEW_ORIGIN, ROOT


for page in ROOT.glob("*.html"):
    html = page.read_text()
    if 'property="og:title"' in html:
        continue
    title_match = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    description_match = re.search(r'<meta name="description" content="(.*?)"\s*/>', html, re.DOTALL)
    if not title_match or not description_match:
        continue
    title = unescape(title_match.group(1)).replace('"', "&quot;")
    description = unescape(description_match.group(1)).replace('"', "&quot;")
    image = f"{PREVIEW_ORIGIN}/assets/og-homeplus.png"
    meta = f'''\n  <meta property="og:type" content="website" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:image" content="{image}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta name="twitter:image" content="{image}" />'''
    html = html.replace(description_match.group(0), description_match.group(0) + meta, 1)
    page.write_text(html)
    print(f"Updated {page.name}")
