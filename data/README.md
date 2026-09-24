# Data

`sources.json` is the maintained registry of official source pages, confirmed discovery endpoints, and known documents. Small files under `fixtures/` are synthetic, clearly labeled inputs for deterministic offline checks; they are not downloaded reports.

Source discovery finds candidate URLs. Manual registration records reviewed candidates and explicit metadata. Checking records HTTP outcomes and identifies payloads by SHA-256. Epidemiological extraction is not implemented and remains a separate future step. In particular, a successful HTTP check does not validate epidemiological contents.

Checks atomically write generated state. Live checks default to `generated/source_manifest.json`; offline fixture checks default to the isolated `generated/offline_source_manifest.json`. Both are ignored by Git because retrieval state and timestamps are run-specific. An explicit `--manifest PATH` overrides the relevant default.

The manifest's cumulative `candidates` registry identifies candidates by exact URL and retains their publisher, discovery endpoint, first-seen and last-seen timestamps, and current-feed presence. A successful later feed can mark an older candidate absent without deleting it. A failed retrieval or parse preserves the last successful presence state. Newly observed candidate URLs are printed for human review; they are not automatically downloaded or registered.

Current discovery is limited to the confirmed official INSP SitRep RSS feed and may be incomplete. If the feed misses a document, add its official URL and explicitly known metadata to `sources.json`; never guess a filename or replace prior history. Candidate status and successful HTTP retrieval do not validate epidemiological content.

## Canonical document registry

A registered source or registered URL is a maintained entry in `sources.json`: a source page, discovery endpoint, or document. A candidate is only an exact URL observed in a supported discovery response; `present_in_current_response` says it appeared in the most recent successful response. Candidates are not fetched automatically and are not documents until reviewed and registered. A document payload is one retrieved raw byte sequence, identified by SHA-256; `unique document payloads` counts distinct hashes across registered documents and all retained versions. Consequently, the offline fixture correctly has one RSS candidate and three unique payloads from three separately registered seed documents.

Each canonical document record has a stable maintained `id`, `canonical_url`, sorted `aliases` and `all_urls`, nullable `title`, reporting and publication dates, `last_checked`, media type, byte length, current SHA-256, and its ordered payload-version IDs. `origin` distinguishes `seed` from `discovery`, while nullable `discovered_from` names the discovery endpoint when known. Statuses are `new` on the first successful retrieval, `unchanged` for known bytes, `changed` when a known logical document gains a different payload, and `unavailable` on a failed retrieval. Unavailable records retain prior version history.

Logical identity comes from the reviewed document ID, not a filename or hash. Payloads are deduplicated globally by the SHA-256 of their raw bytes and retain every observed URL. Thus two logical records may share one payload without losing either URL, while one logical record may refer to several versions. Identical bytes do not necessarily prove that two publications are the same logical document, and differing bytes may reflect only PDF/HTML packaging changes. Lists and JSON serialization are sorted for deterministic output.

Generate isolated fixture state with `python -m ebolalens sources check --offline`. Generate operational state—which performs network requests—with `python -m ebolalens sources check --live`. Inspect either existing manifest without network access with:

```bash
python -m ebolalens documents list --manifest data/generated/offline_source_manifest.json
python -m ebolalens documents list --manifest data/generated/offline_source_manifest.json --json
```

This tool is for research and control of public epidemiological data, not clinical decisions or independent outbreak management.
