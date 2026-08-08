# Reflection: Company Data Enrichment Agent

## Tools Chosen
I built the agent in Python using Perplexity's `pplx_sdk` search/fetch API as the research backend (equivalent tooling to a Claude/Copilot "vibe coding" agent, but scripted directly rather than through a chat UI). This let me combine live web search with targeted, prompt-guided extraction from real fetched pages, keeping results grounded in sources rather than a model's memory. The code and outputs are stored in a public GitHub repository per the assignment instructions.

## Prompt / Code Structure
For each of the 50 companies:
1. **Search** — query `"{company} corporate headquarters address phone number official website"`, top results returned.
2. **Fetch + extract** — the top 2–3 result URLs were fetched with a structured extraction prompt asking for `Location: ...; Phone: ...; Website: ...`, instructing the model to answer "Unknown" rather than guess if a fact wasn't clearly present on the page.
3. **Parse** — a regex pulled the three fields out of the model's structured reply and wrote them to the output CSV/XLSX, with a JSONL log of sources used per company for traceability.
4. Progress was checkpointed to disk after every company so a long run could resume without repeating completed work.

## Challenges Faced
- **Masked data from aggregator sites**: Some searches surfaced lead-gen sites (ZoomInfo, Seamless.ai) that display phone numbers with redacted digits (e.g., "(801) 278-xxxx"). I added a filter to reject any phone number containing stray "x" characters and an `excluded_domains` list to steer searches toward official company sites instead.
- **Entity confusion**: A couple of common/short brand names collided with unrelated companies in search results — e.g., "MSR" initially matched a Japanese company instead of Mountain Safety Research, and "Stanley" briefly matched Morgan Stanley. These were caught during manual QA and corrected against verified brand knowledge.
- **Low-quality source domains**: Complaint-aggregator sites (pissedconsumer.com) and other non-authoritative domains occasionally got selected as the "website" field; these were excluded and replaced with verified official domains.
- **Ambiguous entity**: "Sonder" did not resolve to a recognizable outdoor gear brand — it kept matching Sonder Holdings (hospitality). Rather than force a false match, this row was flagged as "Unknown / ambiguous" instead of populated with a likely-wrong answer.
- **Rate limiting / runtime**: Sequentially researching 50 companies (search + multi-page fetch each) took roughly 15–20 minutes total; the script was designed to checkpoint progress so partial runs could resume without re-querying companies already completed.

## QA Methodology
After the automated pass, every row was reviewed for: (1) missing values, (2) phone numbers with masked/placeholder digits, (3) websites pointing to non-official domains (aggregators, unrelated companies), and (4) location fields missing state/country. Flagged rows were re-researched with a narrower, domain-excluded search, and any remaining low-confidence fields were manually verified or explicitly left blank/"Unknown" rather than guessed — prioritizing accuracy over completeness.
