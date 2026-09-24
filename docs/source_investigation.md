# INSP source-discovery investigation

## Investigation performed

On 2026-09-06, EbolaLens made a small number of sequential, read-only requests to `insp.cd` with a descriptive user agent, 5-second connection and 15-second total timeouts, redirects enabled, and response-size limits. No access control, rate limit, robots rule, or anti-bot measure was bypassed.

The following official mechanisms were tested:

- `https://insp.cd/` returned HTTP 200 and linked to the SitRep category, individual SitRep posts, and the WordPress REST API.
- `https://insp.cd/wp-json/` returned HTTP 200 with WordPress REST metadata.
- `https://insp.cd/wp-json/wp/v2/search?search=sitrep&per_page=10` returned HTTP 200 and ten SitRep post results. Search terms and ranking make this unsuitable as the sole durable index.
- `https://insp.cd/category/sitrep/feed/` returned HTTP 200 as RSS. Its items contained official post URLs and embedded PDF metadata. This is the only mechanism enabled for automatic candidate discovery in stage 01.
- `https://insp.cd/wp-sitemap.xml` returned HTTP 404.
- `https://insp.cd/robots.txt` returned HTTP 200, allowed general access, and declared `https://insp.cd/sitemap.xml`; the declared sitemap also returned HTTP 404.

The investigation also observed relevant official homepage links including the SitRep category and individual SitRep pages. It did not use general web search as a production discovery mechanism.

## Evidence and implementation boundary

The official RSS feed provides a simple, bounded, machine-readable index and exposes candidate post and embedded PDF URLs. The live checker therefore reads that feed and records discovered candidate URLs. It does not automatically assert document identity or infer report metadata from filenames. WordPress REST remains documented evidence but is not queried automatically because the RSS feed is simpler and sufficient for a narrow first implementation.

Generated state preserves a cumulative registry keyed by each exact discovered URL. It records first and last observation, the originating publisher and endpoint, and whether the URL appeared in the latest successful response. New URLs are highlighted for review. URLs absent from a later successful feed remain in history, while retrieval or XML failures leave the previous presence state intact and visibly report the endpoint error. Candidates are not automatically fetched or registered.

Offline fixture state and live operational state use separate default manifests: `data/generated/offline_source_manifest.json` and `data/generated/source_manifest.json`, respectively. This prevents synthetic payload hashes and candidate observations from contaminating live history. Either path can be explicitly overridden for controlled testing or operations.

RSS is not guaranteed to contain complete history, and its continued availability is outside this project's control. The sitemap endpoints tested during this run were unavailable. WHO pages are registered and checked, but stage 01 deliberately includes no broad WHO scraper.

## Manual fallback

When an official document is absent from the feed, add a record to `data/sources.json` using the exact official URL. Assign a stable internal ID, retain every observed alias, and enter report number, reporting date, or publication date only when explicitly known; otherwise use `null`. Never construct speculative sequential URLs or use a filename as identity. Run the offline check first, then a live check when network access is safe. Changed bytes become a new SHA-256 version, while identical bytes at another URL extend the payload's observed URL list.

A successful retrieval or candidate observation establishes availability or URL discovery only. It does not validate or interpret epidemiological contents.

## Registry semantics

The manifest deliberately separates logical documents from byte-level payload versions. A reviewed ID is the stable logical identity; its canonical and alternative URLs remain attached to that record. Every distinct raw payload is stored once by SHA-256 and can collect URLs from more than one document. A changed hash adds a version to the logical record rather than replacing history. Records also state whether they were explicit seeds or reviewed discoveries and retain the originating endpoint when it is known.

The offline fixture's one candidate is the sole URL exposed by its synthetic RSS feed. Its three payloads come from the three explicit seed documents in `sources.json`; candidates are neither downloaded nor counted as payloads. These independent counts are therefore expected.

Raw-byte equality is a deduplication signal, not proof of logical-document identity. Conversely, raw-byte differences can result from a technical repackaging that does not change report content. EbolaLens is a research and public-data auditing aid, not a source of clinical decisions or a system for independent outbreak management.
