"""
Company Data Enrichment Agent
------------------------------
Reads a CSV of company names and augments each row with:
  - location (HQ city/state/country)
  - phone (main corporate/customer service number)
  - website (official domain)

Uses pplx_sdk (web search + page-content extraction) as the research backend.
For each company: 1 web search call + 1 batched multi-URL fetch call with an
extraction prompt, so results are grounded in real fetched pages (reduces
hallucination risk vs. asking a model to recall facts from memory).
"""
import csv
import re
import sys
import time
import pplx_sdk

IN_CSV = "companies_input.csv"
OUT_CSV = "starter-companies-augmented.csv"
LOG = "agent_log.jsonl"


def extract_fields(text):
    loc = re.search(r"Location:\s*(.*?)(?:;|\n|$)", text, re.I)
    phone = re.search(r"Phone:\s*(.*?)(?:;|\n|$)", text, re.I)
    site = re.search(r"Website:\s*(.*?)(?:;|\n|$)", text, re.I)
    def clean(m):
        v = m.group(1).strip() if m else ""
        return "" if v.lower() in ("unknown", "n/a", "none", "") else v
    return clean(loc), clean(phone), clean(site)


def research_company(name):
    query = f"{name} corporate headquarters address phone number official website"
    hits = pplx_sdk.search.web(query, limit=4)
    urls = [h.url for h in hits[:3]]
    if not urls:
        return "", "", "", []

    prompt = (
        f"Based only on this page, answer for the company '{name}': "
        f"What is its headquarters location (city, state/country)? "
        f"What is its main corporate or customer-service phone number? "
        f"What is its official website domain? "
        f"Reply in EXACTLY this format (use 'Unknown' if not stated on this page):\n"
        f"Location: ...; Phone: ...; Website: ..."
    )
    pages = pplx_sdk.content.fetch(urls, prompt=prompt, cache_enabled=False)

    loc, phone, site = "", "", ""
    for p in pages:
        content = getattr(p, "content", None) or ""
        if not content:
            continue
        l, ph, s = extract_fields(content)
        loc = loc or l
        phone = phone or ph
        site = site or s
        if loc and phone and site:
            break

    if not site and hits:
        site = hits[0].domain
    return loc, phone, site, urls


def main():
    import json, os
    with open(IN_CSV) as f:
        companies = [row["company_name"].strip() for row in csv.DictReader(f) if row.get("company_name", "").strip()]

    done = {}
    if os.path.exists(LOG):
        with open(LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    done[rec["company"]] = rec
                except Exception:
                    pass

    rows = []
    with open(LOG, "a") as logf:
        for i, name in enumerate(companies, 1):
            if name in done:
                rec = done[name]
                rows.append({"company_name": name, "location": rec.get("location", ""), "phone": rec.get("phone", ""), "website": rec.get("website", "")})
                print(f"[{i}/{len(companies)}] {name} -> (cached)")
                continue
            loc, phone, site, sources = "", "", "", []
            try:
                loc, phone, site, sources = research_company(name)
            except Exception as e:
                print(f"[{i}/{len(companies)}] ERROR {name}: {e}", file=sys.stderr)
            rows.append({"company_name": name, "location": loc, "phone": phone, "website": site})
            logf.write(f'{{"company": "{name}", "location": "{loc}", "phone": "{phone}", "website": "{site}", "sources": {sources}}}\n')
            logf.flush()
            print(f"[{i}/{len(companies)}] {name} -> loc={loc!r} phone={phone!r} site={site!r}")
            time.sleep(0.3)

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_name", "location", "phone", "website"])
        w.writeheader()
        w.writerows(rows)

    print(f"\nDone. Wrote {len(rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
