import csv
import pplx_sdk
from agent import extract_fields

BAD_DOMAINS = ["zoominfo.com", "seamless.ai", "prospeo.io", "moneycontrol.com",
               "business-directory.fr", "elliott.org", "pissedconsumer.com",
               "linkedin.com", "morganstanley.com"]

TO_FIX = ["Rab", "Marmot", "Sonder", "Backcountry", "Stanley", "Yeti",
          "Mountain Hardwear", "Hoka"]

results = {}
for name in TO_FIX:
    try:
        hits = pplx_sdk.search.web(f"{name} official corporate headquarters address phone number",
                                    limit=5, excluded_domains=BAD_DOMAINS)
        urls = [h.url for h in hits[:3]]
        loc, phone, site = "", "", (hits[0].domain if hits else "")
        if urls:
            prompt = (f"Based only on this page, for the company '{name}': headquarters location "
                      f"(city, state/country)? Main phone number (complete, no masked digits)? "
                      f"Official website domain? Reply EXACTLY: Location: ...; Phone: ...; Website: ... "
                      f"Use 'Unknown' if not clearly stated.")
            pages = pplx_sdk.content.fetch(urls, prompt=prompt, cache_enabled=False)
            for p in pages:
                content = getattr(p, "content", None) or ""
                if not content:
                    continue
                l, ph, s = extract_fields(content)
                if ph and "x" in ph.lower().replace("ext", ""):
                    ph = ""
                loc = loc or l
                phone = phone or ph
                site = site or s
        results[name] = (loc, phone, site)
        print(f"{name} -> loc={loc!r} phone={phone!r} site={site!r}")
    except Exception as e:
        print(f"ERROR {name}: {e}")

rows = []
with open("starter-companies-augmented.csv") as f:
    for row in csv.DictReader(f):
        name = row["company_name"]
        if name in results:
            loc, phone, site = results[name]
            if loc:
                row["location"] = loc
            if phone:
                row["phone"] = phone
            if site:
                row["website"] = site
        rows.append(row)

with open("starter-companies-augmented.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["company_name", "location", "phone", "website"])
    w.writeheader()
    w.writerows(rows)
print("Merged.")
