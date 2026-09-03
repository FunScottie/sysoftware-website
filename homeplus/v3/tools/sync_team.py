#!/usr/bin/env python3
"""Sync the public HomePlus team roster into static V2 directory/profile pages."""

from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import re
import sys
import unicodedata


SOURCE_URL = "https://homeplusmortgage.com/homeplus-mortgage-team/"
ROOT = Path(__file__).resolve().parents[1]
TEAM_DIR = ROOT / "team"
IMAGE_DIR = ROOT / "assets" / "team"
DATA_PATH = ROOT / "team-data.json"
QUOTE_URL = "https://home-plus-mortgage.secure-clix.com/"
PREVIEW_ORIGIN = "https://www.sysoftware.com/homeplus/v3"


def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value


def compact(parts):
    return " ".join(" ".join(parts).split())


def structured(parts):
    """Normalize text while retaining meaningful source line breaks."""
    text = " ".join(parts)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def safer_bio(name, text):
    """Retain the current bio while softening absolute/comparative marketing claims."""
    text = re.sub(r"\s*EQUAL HOUSING LENDER,.*$", "", text, flags=re.IGNORECASE)
    replacements = {
        "the best loan available": "a financing option suited to their situation",
        "the best financing solution": "a financing solution",
        "the best deal": "appropriate terms",
        "the best mortgage services and products": "high-quality mortgage services and products",
        "the best pricing possible": "competitive pricing",
        "best possible service": "responsive service",
        "the lowest rates": "competitive rates",
        "best financing options": "financing options suited to your needs",
        "the best options": "options suited to your needs",
        "guarantee to provide": "am committed to providing",
        "guaranteed to meet": "designed to support",
    }
    for before, after in replacements.items():
        text = re.sub(re.escape(before), after, text, flags=re.IGNORECASE)
    if name == "Phil Pizzino":
        text = re.sub(
            r"Throughout his career, Phil Pizzino.*?keeping the customer foremost\.\s*",
            "Throughout his career, Phil Pizzino has focused on creating a business where customers and employees can thrive. As Founder and CEO of HomePlus Corporation, he has led the company's adoption of technology, marketing, and service practices while keeping the customer foremost. ",
            text,
            count=1,
        )
    return compact([text])


class TeamParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.record = None
        self.div_depth = 0
        self.records = []

    def has_class(self, class_name):
        return any(class_name in classes for _, classes in self.stack)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get("class", "").split())
        if tag == "div" and self.record is None and "meetheteam-box-container" in classes:
            self.record = {
                "name": "", "title": "", "nmls": "", "photoSource": "",
                "bioParts": [], "licenseParts": [], "addressParts": [],
                "contactParts": [], "email": "", "applicationUrl": "",
                "documentUploadUrl": "",
            }
            self.div_depth = 1
        elif self.record is not None and tag == "div":
            self.div_depth += 1

        if self.record is not None and tag == "br":
            if self.has_class("agentlocations"):
                self.record["addressParts"].append("\n")
            if self.has_class("agentscontact-details"):
                self.record["contactParts"].append("\n")

        self.stack.append((tag, classes))
        if not self.record:
            return

        if tag == "img" and not self.record["photoSource"] and (
            "scale-with-grid" in classes or "bio-profil-img" in classes
        ):
            self.record["photoSource"] = attrs.get("src", "").replace("http://", "https://")
            self.record["name"] = attrs.get("alt", "")

        if tag == "a":
            href = attrs.get("href", "")
            if href.startswith("mailto:"):
                self.record["email"] = href[7:].strip()
            elif href != "#" and ("my1003app.com" in href or "secureloandocs.com" in href):
                self.record["applicationUrl"] = href
            elif "sharefile.com" in href or "sharepoint.com" in href:
                self.record["documentUploadUrl"] = href

    def handle_data(self, data):
        if not self.record:
            return
        text = compact([data])
        if not text:
            return
        tag = self.stack[-1][0] if self.stack else ""

        if self.has_class("profilename-title"):
            if tag == "span":
                self.record["title"] = compact([self.record["title"], text])
            elif tag == "h3":
                self.record["name"] = text
            elif tag == "h4" and not self.record["nmls"]:
                match = re.search(r"(\d{3,})", text)
                self.record["nmls"] = match.group(1) if match else ""

        for class_name, key in (
            ("aboutdesc", "bioParts"),
            ("nmlsid-plus", "licenseParts"),
            ("agentlocations", "addressParts"),
            ("agentscontact-details", "contactParts"),
        ):
            if self.has_class(class_name):
                self.record[key].append(text)

    def handle_endtag(self, tag):
        if self.record is not None and tag == "div":
            self.div_depth -= 1
            if self.div_depth == 0:
                for source_key, target_key in (
                    ("bioParts", "bio"),
                    ("licenseParts", "licenseDetails"),
                ):
                    self.record[target_key] = compact(self.record.pop(source_key))
                for source_key, target_key in (
                    ("addressParts", "address"),
                    ("contactParts", "contactDetails"),
                ):
                    self.record[target_key] = structured(self.record.pop(source_key))
                if self.record["name"]:
                    self.records.append(self.record)
                self.record = None

        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break


def download(source, destination):
    request = Request(source, headers={"User-Agent": "Mozilla/5.0 HomePlusSiteSync/1.0"})
    destination.write_bytes(urlopen(request, timeout=30).read())


def fetch_team():
    request = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0 HomePlusSiteSync/1.0"})
    parser = TeamParser()
    parser.feed(urlopen(request, timeout=30).read().decode("utf-8", "replace"))
    return parser.records


def navigation(prefix="", active="team"):
    return f'''<header class="nav scrolled">
    <div class="nav-inner">
      <a class="nav-logo" href="{prefix}index.html"><img class="logo-white" src="{prefix}assets/logo_white.png" alt="HomePlus Mortgage" /><img class="logo-color" src="{prefix}assets/logo_color.png" alt="HomePlus Mortgage" /></a>
      <button class="nav-burger" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
      <nav class="nav-links" aria-label="Primary navigation">
        <div class="nav-group">
          <button class="nav-group-trigger" type="button" aria-expanded="false"><span>Loans</span><i aria-hidden="true"></i></button>
          <div class="nav-dropdown" aria-label="Loans">
            <a class="nav-dropdown-link" href="{prefix}buy-a-home.html">Buy a Home</a>
            <a class="nav-dropdown-link" href="{prefix}refinance.html">Refinance</a>
            <a class="nav-dropdown-link" href="{prefix}loan-options.html">Loan Options</a>
            <a class="nav-dropdown-link" href="{prefix}compare-rates.html">Compare Rates</a>
          </div>
        </div>
        <a class="nav-primary-link" href="{prefix}resources.html">Resources</a>
        <div class="nav-group">
          <button class="nav-group-trigger active" type="button" aria-expanded="false"><span>About Us</span><i aria-hidden="true"></i></button>
          <div class="nav-dropdown" aria-label="About Us">
            <a class="nav-dropdown-link" href="{prefix}about-us.html">Company Information</a>
            <a class="nav-dropdown-link" href="{prefix}why-homeplus.html">Why HomePlus</a>
            <a class="nav-dropdown-link active" href="{prefix}team.html">Our Team</a>
            <a class="nav-dropdown-link" href="{prefix}reviews.html">Reviews</a>
            <a class="nav-dropdown-link" href="{prefix}contact.html">Contact</a>
          </div>
        </div>
        <a class="nav-quote-link" href="{QUOTE_URL}">Get a Free Quote</a>
        <a class="nav-phone" href="tel:8008107587">800.810.PLUS</a>
        <a class="nav-join-cta" href="{prefix}join-the-team.html"><span>Join the Team</span><span class="nav-join-arrow" aria-hidden="true">→</span></a>
      </nav>
    </div>
  </header>'''


def footer_markup(prefix=""):
    return f'''<footer class="footer" data-shared-footer>
    <div class="wrap">
      <div class="footer-mission">
        <img class="f-logo" src="{prefix}assets/logo_white.png" alt="HomePlus Mortgage" />
        <p>Our mission is to provide our customers with the highest level of customer service and a competitive mortgage rate and term.</p>
      </div>
      <div class="footer-top">
        <div><h4>Corporate Headquarters</h4><p>HomePlus Corporation<br />9655 Granite Ridge Drive, Suite 200<br />San Diego, CA 92123</p></div>
        <div><h4>Contact</h4><ul><li><a href="tel:8008107587">800-810-PLUS (7587)</a></li><li><a href="tel:6193258282">619-325-8282</a></li><li>Fax: 800-378-6031</li><li><a href="mailto:approvaldept@homeplusmortgage.com">approvaldept@homeplusmortgage.com</a></li></ul></div>
        <div><h4>Loans</h4><ul><li><a href="{prefix}buy-a-home.html">Buy a Home</a></li><li><a href="{prefix}refinance.html">Refinance</a></li><li><a href="{prefix}loan-options.html">Loan Options</a></li><li><a href="{prefix}compare-rates.html">Compare Rates</a></li><li><a href="{prefix}resources.html">Resources</a></li></ul></div>
        <div><h4>Company</h4><ul><li><a href="{prefix}about-us.html">Company Information</a></li><li><a href="{prefix}team.html">Our Team</a></li><li><a href="{prefix}reviews.html">Reviews</a></li><li><a href="{prefix}join-the-team.html">Join the Team</a></li><li><a href="{prefix}contact.html">Contact</a></li></ul></div>
      </div>
      <div class="footer-legal">
        <p>© 2026 HomePlus Corporation dba HomePlus Mortgage · NMLS 78669 · Real Estate Broker, CA DRE License #01426454</p>
        <div class="footer-legal-links"><a href="https://www.nmlsconsumeraccess.org" target="_blank" rel="noopener">NMLS Consumer Access</a><a href="https://homeplusmortgage.com/legal/" target="_blank" rel="noopener">State &amp; Federal Disclosures / Licenses</a><a href="https://homeplusmortgage.com/privacy-policy/" target="_blank" rel="noopener">Privacy Policy</a><a href="https://homeplusmortgage.com/wp-content/uploads/2018/01/Consumer-Complaint-and-Recovery-Fund-Notice.pdf" target="_blank" rel="noopener">Texas Complaint / Recovery Fund Notice</a></div>
        <div class="ehl" aria-label="Equal Housing Lender"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 1 10h2v12h7v-7h4v7h7V10h2L12 2zm0 5.7 4.5 3.3H7.5L12 7.7zM8.2 12.5h7.6v1.6H8.2v-1.6zm0 3h7.6v1.6H8.2v-1.6z"/></svg>HOMEPLUS CORPORATION IS AN EQUAL HOUSING LENDER</div>
      </div>
    </div>
  </footer>'''


def footer(prefix=""):
    return f'''{footer_markup(prefix)}
  <script src="{prefix}js/main.js"></script>'''


def document(title, description, body, prefix="", active="team", extra_script="", social_image=""):
    social_image = social_image or f"{PREVIEW_ORIGIN}/assets/og-homeplus.png"
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="robots" content="noindex, nofollow" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description, quote=True)}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{escape(title, quote=True)}" />
  <meta property="og:description" content="{escape(description, quote=True)}" />
  <meta property="og:image" content="{escape(social_image, quote=True)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{escape(title, quote=True)}" />
  <meta name="twitter:description" content="{escape(description, quote=True)}" />
  <meta name="twitter:image" content="{escape(social_image, quote=True)}" />
  <link rel="icon" href="https://homeplusmortgage.com/wp-content/uploads/2021/04/homeplus-icon.ico" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{prefix}css/style.css" />
</head>
<body class="team-site">
  {navigation(prefix, active)}
  {body}
  {footer(prefix)}
  {extra_script}
</body>
</html>
'''


def directory_states(person):
    match = re.search(r"Licensed in:\s*(.*?)(?:Arizona Mortgage|$)", person["licenseDetails"], re.IGNORECASE)
    if not match:
        return []
    return sorted(set(re.findall(r"\b[A-Z]{2}\b", match.group(1))))


def directory_specialties(person):
    text = f' {person["title"]} {person["bio"]} '.lower()
    rules = {
        "purchase": (r"purchase", r"home\s?buyer", r"homeownership"),
        "refinance": (r"refinanc",),
        "va": (r"\bva\b", r"veteran"),
        "fha": (r"\bfha\b",),
        "jumbo": (r"jumbo", r"high[ -]balance"),
        "non-qm": (r"non[ -]?qm", r"bank statement", r"self-employed", r"\bdscr\b", r"private money"),
        "reverse": (r"reverse mortgage",),
    }
    return [key for key, patterns in rules.items() if any(re.search(pattern, text) for pattern in patterns)]


def directory_languages(person):
    text = person["bio"].lower()
    return ["spanish"] if "spanish" in text else []


def render_directory(records):
    ceo = next(person for person in records if person["name"] == "Phil Pizzino")
    team_records = [person for person in records if person["name"] != "Phil Pizzino"]
    cards = []
    for person in team_records:
        states = " ".join(directory_states(person)).lower()
        specialties = " ".join(directory_specialties(person))
        languages = " ".join(directory_languages(person))
        search_text = " ".join((person["name"], person["title"], person["nmls"], person["address"], person["bio"]))
        nmls = f'<span>NMLS #{escape(person["nmls"])}</span>' if person["nmls"] else ""
        if person["bio"] and (person["applicationUrl"] or person["documentUploadUrl"]):
            profile_label = "Bio, contact & secure links →"
        elif person["bio"]:
            profile_label = "View bio & contact →"
        else:
            profile_label = "View contact details →"
        cards.append(f'''<article class="team-card reveal" data-team-card data-search="{escape(search_text.lower(), quote=True)}" data-states="{escape(states, quote=True)}" data-specialties="{escape(specialties, quote=True)}" data-languages="{escape(languages, quote=True)}">
          <a class="team-photo" href="team/{person['slug']}.html"><img src="{escape(person['photo'])}" alt="{escape(person['name'])}" loading="lazy" /></a>
          <div class="team-card-body">
            <p class="team-role">{escape(person['title'])}</p>
            <h2><a href="team/{person['slug']}.html">{escape(person['name'])}</a></h2>
            {nmls}
            <a class="card-link" href="team/{person['slug']}.html">{profile_label}</a>
          </div>
        </article>''')

    ceo_actions = [
        f'<a class="btn btn-cyan" href="team/{ceo["slug"]}.html">View Phil\'s Full Bio <span class="arrow">→</span></a>'
    ]
    if ceo["applicationUrl"]:
        ceo_actions.append(f'<a class="ceo-text-link" href="{escape(ceo["applicationUrl"], quote=True)}">Secure Online Application →</a>')
    if ceo["documentUploadUrl"]:
        ceo_actions.append(f'<a class="ceo-text-link" href="{escape(ceo["documentUploadUrl"], quote=True)}" target="_blank" rel="noopener">Secure Document Upload →</a>')

    body = f'''<main>
    <section class="subhero team-hero">
      <div class="wrap">
        <span class="kicker">People make the difference</span>
        <h1 class="display">Meet the HomePlus team.</h1>
        <p class="lede">Connect directly with an experienced mortgage professional or a member of our support team.</p>
      </div>
    </section>
    <section class="section ceo-section">
      <div class="wrap">
        <div class="section-head reveal">
          <span class="kicker">Founder &amp; CEO</span>
          <h2 class="h2">Leadership grounded in service.</h2>
        </div>
        <div class="ceo-showcase">
          <article class="ceo-profile reveal">
            <img src="{escape(ceo['photo'])}" alt="{escape(ceo['name'])}" />
            <div class="ceo-profile-copy">
              <p class="team-role">{escape(ceo['title'])}</p>
              <h2>{escape(ceo['name'])}</h2>
              <p class="profile-nmls">NMLS #{escape(ceo['nmls'])}</p>
              <p>{escape(ceo['bio'].split('. ')[0] + '.')}</p>
              <div class="ceo-actions">{''.join(ceo_actions)}</div>
            </div>
          </article>
          <div class="ceo-video-card reveal">
            <div class="ceo-video-frame">
              <iframe src="https://fast.wistia.net/embed/iframe/in6xobzx0w?videoFoam=true" title="A message from HomePlus founder and CEO Phil Pizzino" allow="autoplay; fullscreen" allowfullscreen loading="lazy"></iframe>
            </div>
            <div class="ceo-video-caption"><span>A message from our CEO</span><strong>Why HomePlus puts people first</strong></div>
          </div>
        </div>
      </div>
    </section>
    <section class="section team-directory-section">
      <div class="wrap">
        <div class="section-head reveal team-section-head">
          <span class="kicker">Meet the team</span>
          <h2 class="h2">Mortgage professionals and support staff.</h2>
          <p>Choose a person to view their published biography, licensing details, direct contact information, and individual secure links.</p>
        </div>
        <div class="team-tools reveal">
          <div class="team-search-field">
            <label for="teamSearch">Find a team member</label>
            <input id="teamSearch" type="search" placeholder="Search name, role, location, language, or NMLS" autocomplete="off" />
          </div>
          <div class="team-filter-field">
            <label for="teamState">Licensed state</label>
            <select id="teamState"><option value="">All states</option><option>AZ</option><option>CA</option><option>CO</option><option>FL</option><option>GA</option><option>HI</option><option>ID</option><option>IL</option><option>MD</option><option>MT</option><option>NC</option><option>NM</option><option>NV</option><option>OR</option><option>TN</option><option>TX</option><option>UT</option><option>WA</option></select>
          </div>
          <div class="team-filter-field">
            <label for="teamSpecialty">Published specialty</label>
            <select id="teamSpecialty"><option value="">All specialties</option><option value="purchase">Purchase</option><option value="refinance">Refinance</option><option value="va">VA</option><option value="fha">FHA</option><option value="jumbo">Jumbo</option><option value="non-qm">Non-QM / self-employed</option><option value="reverse">Reverse mortgage</option></select>
          </div>
          <div class="team-filter-field">
            <label for="teamLanguage">Published language</label>
            <select id="teamLanguage"><option value="">All languages</option><option value="spanish">Spanish</option></select>
          </div>
          <p><span id="teamCount">{len(team_records)}</span> team members</p>
        </div>
        <div class="team-grid" id="teamGrid">{''.join(cards)}</div>
        <p class="team-empty" id="teamEmpty" hidden>No team members match that search.</p>
      </div>
    </section>
  </main>'''
    script = '''<script>
    (() => {
      const input = document.querySelector("#teamSearch");
      const state = document.querySelector("#teamState");
      const specialty = document.querySelector("#teamSpecialty");
      const language = document.querySelector("#teamLanguage");
      const cards = [...document.querySelectorAll("[data-team-card]")];
      const count = document.querySelector("#teamCount");
      const empty = document.querySelector("#teamEmpty");
      const filterCards = () => {
        const query = input.value.trim().toLowerCase();
        const selectedState = state.value.toLowerCase();
        const selectedSpecialty = specialty.value;
        const selectedLanguage = language.value;
        let visible = 0;
        cards.forEach((card) => {
          const matchesQuery = !query || card.dataset.search.includes(query);
          const matchesState = !selectedState || card.dataset.states.split(" ").includes(selectedState);
          const matchesSpecialty = !selectedSpecialty || card.dataset.specialties.split(" ").includes(selectedSpecialty);
          const matchesLanguage = !selectedLanguage || card.dataset.languages.split(" ").includes(selectedLanguage);
          const match = matchesQuery && matchesState && matchesSpecialty && matchesLanguage;
          card.hidden = !match;
          visible += match ? 1 : 0;
        });
        count.textContent = visible;
        empty.hidden = visible !== 0;
      };
      input.addEventListener("input", filterCards);
      state.addEventListener("change", filterCards);
      specialty.addEventListener("change", filterCards);
      language.addEventListener("change", filterCards);
      const params = new URLSearchParams(window.location.search);
      if ([...state.options].some((option) => option.value.toLowerCase() === (params.get("state") || "").toLowerCase())) state.value = (params.get("state") || "").toUpperCase();
      if ([...specialty.options].some((option) => option.value === params.get("specialty"))) specialty.value = params.get("specialty");
      if ([...language.options].some((option) => option.value === params.get("language"))) language.value = params.get("language");
      if (params.get("q")) input.value = params.get("q");
      filterCards();
    })();
  </script>'''
    return document(
        "Our Team | HomePlus Mortgage",
        "Meet the HomePlus Mortgage loan originators and support professionals.",
        body,
        extra_script=script,
    )


def paragraphs(text):
    if not text:
        return "<p>A biography is not currently published for this team member. Please use the contact information on this page to connect with them directly.</p>"
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text)
    midpoint = max(1, len(sentences) // 2)
    groups = [compact(sentences[:midpoint]), compact(sentences[midpoint:])]
    return "".join(f"<p>{escape(group)}</p>" for group in groups if group)


CONTACT_LABEL = r"Toll[ -]?Free|E[ -]?Fax|Direct|Fax|P|C|O|F"
CONTACT_PATTERN = re.compile(
    rf"(?i)(?<![\w-])({CONTACT_LABEL}):\s*(.*?)"
    rf"(?=\s+(?:{CONTACT_LABEL}):|\s+[\w.+-]+@[\w.-]+\.[A-Za-z]{{2,}}|$)"
)


def parse_contact_methods(details, email):
    """Turn the compact legacy contact string into labeled, scannable methods."""
    details = re.sub(re.escape(email), "", details, flags=re.IGNORECASE) if email else details
    label_names = {
        "p": "Phone",
        "c": "Mobile",
        "o": "Office",
        "f": "Fax",
        "fax": "Fax",
        "e-fax": "E-Fax",
        "e fax": "E-Fax",
        "toll-free": "Toll-free",
        "toll free": "Toll-free",
        "direct": "Direct",
    }
    methods = []
    for match in CONTACT_PATTERN.finditer(details.replace("\n", " ")):
        raw_label = re.sub(r"\s+", " ", match.group(1).strip().lower())
        value = match.group(2).strip(" ,;\n")
        if value and value != "-":
            methods.append((label_names.get(raw_label, match.group(1)), value))
    return methods


def render_contact_card(person):
    first_name = escape(person["name"].split()[0])
    methods = parse_contact_methods(person["contactDetails"], person["email"])
    method_markup = []
    for label, value in methods:
        label_html = escape(label)
        value_html = escape(value)
        if "fax" in label.lower():
            method_markup.append(
                f'<div class="contact-method"><span>{label_html}</span><strong>{value_html}</strong></div>'
            )
        else:
            phone_href = re.sub(r"[^\d+]", "", value)
            method_markup.append(
                f'<a class="contact-method" href="tel:{escape(phone_href, quote=True)}">'
                f'<span>{label_html}</span><strong>{value_html}</strong></a>'
            )

    if person["email"]:
        email = escape(person["email"])
        email_href = escape(person["email"], quote=True)
        method_markup.append(
            f'<a class="contact-method contact-method-email" href="mailto:{email_href}">'
            f'<span>Email</span><strong>{email}</strong></a>'
        )

    if not method_markup:
        method_markup.append(
            '<div class="contact-method contact-method-email"><span>Contact</span>'
            '<strong>Contact information available upon request</strong></div>'
        )

    address = person["address"] or "HomePlus Corporation\n9655 Granite Ridge Drive, Suite 200\nSan Diego, CA 92123"
    address_lines = [line.strip() for line in address.splitlines() if line.strip()]
    address_markup = "".join(f"<span>{escape(line)}</span>" for line in address_lines)

    return f'''<aside class="profile-contact-card profile-contact-inline">
            <div class="contact-card-heading">
              <span class="contact-eyebrow">Direct contact</span>
              <h2>Contact {first_name}</h2>
            </div>
            <div class="contact-method-grid">{''.join(method_markup)}</div>
            <div class="contact-office">
              <span class="contact-eyebrow">Office</span>
              <address class="contact-address">{address_markup}</address>
            </div>
          </aside>'''


def render_profile(person):
    nmls_line = f'<p class="profile-nmls">NMLS #{escape(person["nmls"])}</p>' if person["nmls"] else ""
    license_details = escape(person["licenseDetails"] or (f'NMLS ID No. {person["nmls"]}' if person["nmls"] else "HomePlus team member"))
    actions = []
    if person["applicationUrl"]:
        actions.append(f'<a class="btn btn-primary" href="{escape(person["applicationUrl"], quote=True)}">Secure Online Application <span class="arrow">→</span></a>')
    if person["documentUploadUrl"]:
        actions.append(f'<a class="btn btn-cyan" href="{escape(person["documentUploadUrl"], quote=True)}" target="_blank" rel="noopener">Secure Document Upload <span class="arrow">→</span></a>')
    if person["email"]:
        actions.append(f'<a class="btn btn-ghost profile-email" href="mailto:{escape(person["email"], quote=True)}">Email {escape(person["name"].split()[0])}</a>')

    secure_note = ""
    if person["applicationUrl"] or person["documentUploadUrl"]:
        secure_note = '<p class="profile-actions-note">Secure buttons use this team member\'s individual destinations published on the current HomePlus website.</p>'

    body = f'''<main>
    <section class="profile-hero">
      <div class="wrap profile-grid">
        <div class="profile-portrait reveal"><img src="../{escape(person['photo'])}" alt="{escape(person['name'])}" /></div>
        <div class="profile-intro reveal">
          <a class="profile-back" href="../team.html">← Back to our team</a>
          <span class="kicker">{escape(person['title'])}</span>
          <h1 class="display">{escape(person['name'])}</h1>
          {nmls_line}
          <p class="profile-license">{license_details}</p>
          <div class="profile-full-bio">
            <span class="kicker">Biography</span>
            {paragraphs(person['bio'])}
          </div>
          {secure_note}
          <div class="profile-actions">{''.join(actions)}</div>
          {render_contact_card(person)}
        </div>
      </div>
    </section>
  </main>'''
    return document(
        f'{person["name"]} | HomePlus Mortgage',
        f'Contact {person["name"]}, {person["title"]} at HomePlus Mortgage.',
        body,
        prefix="../",
        social_image=person["photoSource"],
    )


def main():
    records = fetch_team()
    TEAM_DIR.mkdir(exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    for person in records:
        person["slug"] = slugify(person["name"])
        person["title"] = re.sub(r"\s*/\s*$", "", person["title"]).strip()
        person["title"] = re.sub(r"\bSpecialis$", "Specialist", person["title"])
        person["email"] = person["email"].strip()
        person["bio"] = safer_bio(person["name"], person["bio"])
        parsed = urlparse(person["photoSource"])
        suffix = Path(parsed.path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"
        image_name = f'{person["slug"]}{suffix}'
        image_path = IMAGE_DIR / image_name
        if not image_path.exists():
            try:
                download(person["photoSource"], image_path)
            except Exception as error:
                print(f'Warning: could not download {person["photoSource"]}: {error}')
        person["photo"] = f"assets/team/{image_name}" if image_path.exists() else person["photoSource"]

    DATA_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "team.html").write_text(render_directory(records))
    for person in records:
        (TEAM_DIR / f'{person["slug"]}.html').write_text(render_profile(person))

    applications = {}
    for person in records:
        if person["applicationUrl"]:
            applications.setdefault(person["applicationUrl"], []).append(person["name"])
    duplicates = {url: names for url, names in applications.items() if len(names) > 1}
    print(f"Synced {len(records)} team profiles.")
    for url, names in duplicates.items():
        print(f"VERIFY duplicate application URL ({', '.join(names)}): {url}")


def render_existing():
    """Rebuild team pages from saved approved content without scraping the source."""
    records = json.loads(DATA_PATH.read_text())
    (ROOT / "team.html").write_text(render_directory(records))
    for person in records:
        (TEAM_DIR / f'{person["slug"]}.html').write_text(render_profile(person))
    print(f"Rendered {len(records)} saved team profiles without refreshing their content.")


if __name__ == "__main__":
    render_existing() if "--render-only" in sys.argv else main()
