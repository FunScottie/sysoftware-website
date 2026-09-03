#!/usr/bin/env python3
"""Apply the shared compliance footer to the hand-authored root pages."""

from pathlib import Path
import re

from sync_team import ROOT, footer_markup


for page in ROOT.glob("*.html"):
    html = page.read_text()
    updated, replacements = re.subn(
        r'<footer class="footer"[^>]*>.*?</footer>',
        footer_markup(),
        html,
        count=1,
        flags=re.DOTALL,
    )
    if replacements:
        page.write_text(updated)
        print(f"Updated {page.name}")
