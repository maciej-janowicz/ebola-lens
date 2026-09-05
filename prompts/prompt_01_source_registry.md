# Prompt 01 — official-source registry and change detection

You are working in the public Git repository **EbolaLens**. Stage 00 is committed and the worktree must be clean before you begin.

EbolaLens is a lightweight, reproducible operational tool for processing official reports about the ongoing outbreak of Ebola disease caused by Bundibugyo virus. It must run on an ordinary laptop without HPC, paid cloud services, a database server, or a heavy frontend.

Project motto:

> Public quickly. Correct carefully. Revise transparently.

## Goal of this stage

Implement the smallest reliable foundation for:

1. registering official sources and known official documents;
2. checking registered URLs safely;
3. detecting a previously unseen document version or a changed payload at an existing URL;
4. producing a deterministic, machine-readable manifest and a concise human-readable report.

Do **not** parse epidemiological tables yet. Do not implement forecasting, PDF text extraction, a dashboard, GitHub Pages, or GitHub Actions.

## Important source finding

INSP/COUSP PDF filenames are not governed by a stable naming convention. Observed official filenames contain inconsistent variants such as `Draft`, `Final`, `Revised`, different encodings of `N°`, and different date formats. Therefore:

- never discover reports by guessing sequential filenames or constructing speculative URLs;
- never treat a filename as the report identity;
- distinguish the canonical source URL, final resolved URL, content hash, report number when known, reporting date when known, publication date when known, and retrieval time;
- treat identical content reached through different URLs as the same payload while retaining all observed URLs;
- treat changed bytes at an existing URL as a new document version, never as an overwrite of history.

## Official starting points

Record these official pages as source-page candidates:

- INSP: `https://insp.cd/`
- WHO outbreak page: `https://www.who.int/emergencies/situations/ebola-outbreak---drc-2026`
- WHO Disease Outbreak News: `https://www.who.int/emergencies/disease-outbreak-news`

Use at least these confirmed official INSP documents as reproducible fixtures or seed records:

- `https://insp.cd/wp-content/uploads/2026/05/Draft-MVE-Ituri-ActuelB-1.pdf`
- `https://insp.cd/wp-content/uploads/2026/07/Draft_SitRep_MVE_RDC_N%C2%B0055_08_07_2026.pdf`
- `https://insp.cd/wp-content/uploads/2026/07/SitRep_MVE_RDC_N%C2%B0_68_21-07-2026.pdf`

Do not infer that these are the newest documents.

## Discovery investigation

Before implementing live discovery, perform a short, polite, read-only investigation of official INSP mechanisms, including where reachable:

- relevant links on official INSP pages;
- WordPress REST endpoints exposed by `insp.cd`;
- official sitemaps;
- official feeds.

Use explicit timeouts, a descriptive EbolaLens user agent, few requests, and no concurrency against INSP. Do not bypass access controls, robots restrictions, rate limits, or anti-bot measures. Do not use general web-search results as the production discovery mechanism.

Document exactly which official discovery mechanisms were tested, which worked, and which did not. Implement automatic discovery only for mechanisms confirmed during this run. If no reliable official index is available, say so clearly and implement a seed/manual-registration workflow plus URL change detection. A truthful partial capability is preferable to fabricated automation.

WHO monitoring may be represented in the registry at this stage, but do not build a broad WHO content scraper unless it is both simple and testable.

## Data model

Use a simple, documented JSON representation based only on Python's standard library unless a new dependency is clearly justified. Include fields sufficient to represent:

- stable internal document/version identifiers;
- publisher and source type;
- canonical and resolved URLs;
- all known aliases;
- retrieval timestamp in UTC;
- HTTP status;
- media type;
- byte length;
- SHA-256 digest;
- ETag and Last-Modified when supplied;
- report number and dates when explicitly known, otherwise `null`;
- discovery method;
- first-seen and last-checked timestamps;
- status and error information without silently dropping failed checks.

Separate maintained configuration from generated state. Generated output must be deterministic apart from explicitly documented retrieval timestamps. Use atomic file replacement so an interrupted run cannot corrupt the manifest.

## Command-line interface

Add a minimal CLI while preserving:

```bash
python -m ebolalens --version
```

Provide clear commands equivalent to:

```bash
python -m ebolalens sources list
python -m ebolalens sources check --offline
python -m ebolalens sources check --live
```

Exact internal organization is your decision, but avoid a framework and premature abstraction.

- `list` displays registered source pages and known documents.
- `check --offline` runs deterministically against committed fixtures and requires no network.
- `check --live` performs polite checks of registered live URLs and any confirmed official discovery endpoint.

Exit nonzero for an unusable configuration or internal processing failure. Individual unreachable sources should be recorded and reported without discarding successful results from other sources.

## Storage and safety

- Do not commit downloaded live PDFs in this stage.
- Commit only small, clearly identified test fixtures. Prefer minimal synthetic byte fixtures where real PDFs are unnecessary.
- Never log tokens, cookies, credentials, complete request headers, or environment contents.
- Do not execute active content from retrieved pages.
- Apply bounded download sizes and reject unexpected oversized payloads safely.
- Use connection and read timeouts.
- Use conditional requests when ETag or Last-Modified is available, but SHA-256 remains the content identity.
- Preserve provenance for every result.

## Tests

Add deterministic tests, with no network access, covering at least:

1. configuration loading and validation;
2. unchanged content at the same URL;
3. changed bytes at the same URL creating a new version;
4. identical bytes reached through a second URL creating an alias rather than duplicate content;
5. HTTP or transport failure being recorded without corrupting prior state;
6. atomic manifest writing;
7. offline CLI behavior and exit status;
8. the existing version command.

Mock or fake transport at a narrow boundary. Tests must not call INSP or WHO.

## Documentation

Update `README.md` and `data/README.md` with:

- the new commands;
- the distinction between discovery, registration, checking, and epidemiological extraction;
- limitations of the current discovery mechanism;
- where maintained configuration and generated manifests live;
- a clear statement that a successful HTTP check does not validate epidemiological contents.

Add a short technical note under `docs/` describing the source investigation, evidence, limitations, and fallback manual-registration procedure. Do not include unverified epidemiological numbers.

## Verification

After implementation:

1. install the project in the existing `.venv` in editable development mode;
2. run the complete test suite;
3. run the version command;
4. run all offline source commands;
5. run the live check only if it is safe and reachable; a network failure must be reported honestly, not hidden;
6. run syntax/compile checks appropriate to the implementation;
7. inspect all changes for secrets and accidental downloaded files;
8. run `git diff --check`;
9. show `git status --short`.

Do not run `git add`, `git commit`, `git push`, create releases, or modify GitHub settings.

## Control artifacts

Create:

- `stage01_sources_report.log` — concise summary of investigation, implementation, exact commands, test results, live-check outcome, limitations, and assumptions;
- `stage01_sources_changes.diff` — readable unified diff of all changes and new files, excluding the diff file itself to avoid recursion.

Do not modify the Stage 00 report or diff. At the end, print a concise summary, exact test result, live-check status, limitations, and `git status --short`.
