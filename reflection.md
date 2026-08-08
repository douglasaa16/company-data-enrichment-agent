# Reflection: Company Data Enrichment Agent

## Tools Chosen
Built in Python using Perplexity's `pplx_sdk` search/fetch API as the research backend (a scripted "vibe coding" agent, same idea as Claude/Copilot but run directly). This grounds results in real fetched pages instead of a model's memory. Code and outputs live in a public GitHub repo.

## Prompt / Code Structure
For each of the 50 companies: (1) search `"{company} corporate headquarters address phone number official website"`; (2) fetch the top 2–3 result URLs with a structured extraction prompt requesting `Location: ...; Phone: ...; Website: ...`, instructing "Unknown" over guessing; (3) regex-parse the reply into the output CSV/XLSX, logging sources per company; (4) checkpoint progress to disk so a long run could resume without repeating work.

## Challenges Faced
- **Masked data**: Lead-gen sites (ZoomInfo, Seamless.ai) showed redacted phone digits (e.g., "278-xxxx"). Fixed by rejecting numbers containing "x" and excluding those domains from search.
- **Entity confusion**: Short brand names collided with unrelated companies — "MSR" matched a Japanese company instead of Mountain Safety Research, "Stanley" briefly matched Morgan Stanley. Caught in manual QA and corrected.
- **Low-quality domains**: Complaint-aggregator sites (pissedconsumer.com) occasionally got picked as the "website" — excluded and replaced with verified official domains.
- **Ambiguous entity**: "Sonder" never resolved to a recognizable outdoor gear brand; left as "Unknown" rather than force a likely-wrong match.

## QA Methodology
Reviewed every row for missing values, masked phone digits, non-official website domains, and incomplete locations. Flagged rows were re-researched with domain exclusions; anything still low-confidence was manually verified or left blank/"Unknown" — prioritizing accuracy over completeness.
