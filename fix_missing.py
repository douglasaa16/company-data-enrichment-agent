import csv
import pplx_sdk
from agent import extract_fields

BAD_DOMAINS = ["zoominfo.com", "seamless.ai", "prospeo.io", "moneycontrol.com", "business-directory.fr", "elliott.org"]

TO_FIX = [
    "Rab", "Mountain Equipment", "Helly Hansen", "Salewa", "Mammut", "Ortovox",
    "Klean Kanteen", "Hydro Flask", "Nalgene", "CamelBak", "Yeti", "Stanley",
    "Leatherman", "Petzl", "Garmin", "Suunto", "Sonder", "Backcountry",
    "Marmot", "prAna", "Deuter", "Black Diamond Equipment", "Mountain Hardwear",
    "Keen", "Hoka",
]

MSR_OVERRIDE_QUERY = "MSR Mountain Safety Research Cascade Designs Seattle headquarters phone"


def research(name):
    query = MSR_OVERRIDE_QUERY if name == "MSR" else f"{name} official corporate headquarters address phone number"
    hits = pplx_sdk.search.web(query, limit=5, excluded_domains=BAD_DOMAINS)
    urls = [h.url for h in hits[:3]]
    if not urls:
        return "", "", ""
    prompt = (
        f"Based only on this page, for the company '{name}': what is its headquarters "
        f"location (city, state/country)? What is its main phone number (must be a complete, "
        f"real number with no masked/redacted digits like 'xxxx' or 'x's)? What is its official "
        f"website domain? Reply EXACTLY as: Location: ...; Phone: ...; Website: ... "
        f"Use 'Unknown' for anything not clearly and fully stated on this page."
    )
    pages = pplx_sdk.content.fetch(urls, prompt=prompt, cache_enabled=False)
    loc, phone, site = "", "", ""
    for p in pages:
        content = getattr(p, "content", None) or ""
        if not content:
            continue
        l, ph, s = extract_fields(content)
        if ph and "x" in ph.lower().replace("ext", ""):
            ph = ""  # reject masked numbers
        loc = loc or l
        phone = phone or ph
        site = site or s
    if not site and hits:
        site = hits[0].domain
    return loc, phone, site


results = {}
for name in TO_FIX:
    try:
        loc, phone, site = research(name)
    except Exception as e:
        loc, phone, site = "", "", ""
        print(f"ERROR {name}: {e}")
    results[name] = (loc, phone, site)
    print(f"{name} -> loc={loc!r} phone={phone!r} site={site!r}")

# Merge into final CSV
rows = []
with open("starter-companies-augmented.csv") as f:
    for row in csv.DictReader(f):
        name = row["company_name"]
        if name in results:
            loc, phone, site = results[name]
            row["location"] = loc or row.get("location", "")
            row["phone"] = phone or row.get("phone", "")
            row["website"] = site or row.get("website", "")
        rows.append(row)

with open("starter-companies-augmented.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["company_name", "location", "phone", "website"])
    w.writeheader()
    w.writerows(rows)

print("Merged fixes into starter-companies-augmented.csv")
