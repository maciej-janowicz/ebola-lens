# Prompt 01a — isolate offline state and preserve discovery history

You are continuing Stage 01 of EbolaLens. Do not redesign the source subsystem and do not add new product features. Correct two operational defects identified during review.

Read the existing Stage 01 implementation, tests, documentation, report, and prompt before editing.

## Defect 1: offline/live manifest contamination

The `--offline` and `--live` modes currently default to the same generated manifest path. An offline run writes synthetic fixture payloads into the same state later used by a live run. This can contaminate real operational history.

Requirements:

- live mode must continue to default to `data/generated/source_manifest.json`;
- offline mode must default to a distinct path such as `data/generated/offline_source_manifest.json`;
- an explicit `--manifest PATH` must override the mode-specific default;
- selecting the default manifest must occur after argument parsing and must be clear and testable;
- update `.gitignore` and documentation if necessary;
- add a CLI test proving that default offline and live paths cannot coincide, without making a network request.

## Defect 2: RSS candidates have no durable history

The current manifest records only the candidates present in the latest RSS response. It does not identify newly discovered URLs, preserve candidates that later disappear from the feed, or retain history when RSS retrieval fails. Consequently, the tool cannot yet answer its core operational question: “Did a new report candidate appear?”

Requirements:

- preserve a cumulative candidate registry in generated state;
- identify candidates by exact discovered URL at this stage; do not infer report identity from filenames;
- for every candidate retain at least:
  - URL,
  - publisher/discovery endpoint,
  - first-seen UTC timestamp,
  - last-seen UTC timestamp,
  - whether it is present in the current successful discovery response;
- classify and report candidates newly observed in the current run;
- retain previously observed candidates that are absent from a later successful feed response, marking them not currently present rather than deleting them;
- if RSS retrieval or parsing fails, preserve prior candidate history and do not falsely mark all candidates absent;
- do not automatically register or fetch candidate URLs;
- ensure deterministic ordering;
- make the human-readable summary show counts for total known candidates, newly discovered candidates, and candidates present in the current feed;
- when new candidates exist, print their URLs so a human can review and register them;
- add network-free tests covering:
  1. first discovery;
  2. a second unchanged discovery run;
  3. a new candidate on a later run;
  4. a previously seen candidate disappearing from a successful feed;
  5. discovery transport or XML failure preserving prior history.

## Audit details

Also verify the following while making the narrow correction:

- a `304 Not Modified` document response retains effective conditional metadata for future checks;
- source or discovery errors remain visible in the summary without destroying prior successful state;
- tests never access the network.

Fix a confirmed problem in these details if found, but do not broaden scope.

## Documentation and verification

Update `README.md`, `data/README.md`, and `docs/source_investigation.md` only as needed to describe:

- separate offline and live state;
- durable candidate history;
- the fact that candidates still require human review and are not epidemiologically validated.

Run:

- editable development installation;
- complete pytest suite;
- version command;
- source listing;
- offline check twice, demonstrating the second run has zero new candidates;
- compile checks;
- `git diff --check`;
- `git status --short`.

Do not run `git add`, `git commit`, `git push`, live network checks, releases, or GitHub configuration changes.

Update `stage01_sources_report.log` with a clearly labeled review-correction section and final test results. Regenerate `stage01_sources_changes.diff` so it represents the complete final Stage 01 change set from the current `HEAD`, excluding the diff file itself. Do not modify Stage 00 artifacts.

At the end, print a concise summary, exact test result, demonstration of isolated default manifests, candidate-history behavior, and `git status --short`.
