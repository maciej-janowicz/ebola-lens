# Data

`sources.json` is the maintained registry of official source pages, confirmed discovery endpoints, and known documents. Small files under `fixtures/` are synthetic, clearly labeled inputs for deterministic offline checks; they are not downloaded reports.

Source discovery finds candidate URLs. Manual registration records reviewed candidates and explicit metadata. Checking records HTTP outcomes and identifies payloads by SHA-256. Epidemiological extraction is not implemented and remains a separate future step. In particular, a successful HTTP check does not validate epidemiological contents.

Checks atomically write generated state. Live checks default to `generated/source_manifest.json`; offline fixture checks default to the isolated `generated/offline_source_manifest.json`. Both are ignored by Git because retrieval state and timestamps are run-specific. An explicit `--manifest PATH` overrides the relevant default.

The manifest's cumulative `candidates` registry identifies candidates by exact URL and retains their publisher, discovery endpoint, first-seen and last-seen timestamps, and current-feed presence. A successful later feed can mark an older candidate absent without deleting it. A failed retrieval or parse preserves the last successful presence state. Newly observed candidate URLs are printed for human review; they are not automatically downloaded or registered.

Current discovery is limited to the confirmed official INSP SitRep RSS feed and may be incomplete. If the feed misses a document, add its official URL and explicitly known metadata to `sources.json`; never guess a filename or replace prior history. Candidate status and successful HTTP retrieval do not validate epidemiological content.
