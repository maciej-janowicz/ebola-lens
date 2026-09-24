# EbolaLens

EbolaLens is a lightweight, reproducible tool for processing official reports about an ongoing Bundibugyo virus disease outbreak.

> **Early-stage warning:** This project is at a very early stage. It is not an official information source and does not provide clinical advice.

## Requirements

- Python 3.11 or newer

## Development setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the tests:

```bash
pytest
```

Display the package version:

```bash
python -m ebolalens --version
```

List and check official sources:

```bash
python -m ebolalens sources list
python -m ebolalens sources check --offline
python -m ebolalens sources check --live
python -m ebolalens documents list --manifest data/generated/offline_source_manifest.json
python -m ebolalens documents list --manifest data/generated/offline_source_manifest.json --json
```

The offline command is deterministic and uses small synthetic fixtures. It writes `data/generated/offline_source_manifest.json` by default. The live command performs bounded, sequential HTTP checks and records per-source failures without discarding successful results; its default state is `data/generated/source_manifest.json`. Use `--manifest PATH` to override either default. Keeping these paths separate prevents synthetic fixture state from entering operational history.

Maintained registrations live in `data/sources.json`; generated manifests are written atomically and are not committed. Discovery finds candidate official URLs, registration records reviewed URLs, and checking detects byte-level versions. Candidate history is cumulative: manifests record first and last observation, current-feed presence, and newly seen URLs even when older candidates disappear from a later successful feed. Discovery failures preserve the last successful candidate state.

The document command only reads an existing manifest and never accesses the network. Its default output is a compact table; `--json` emits complete canonical document records in a stable order. A missing or malformed manifest is reported as a command-line error.

Epidemiological extraction is a separate future stage. Current automatic discovery is limited to the confirmed INSP SitRep RSS feed; it is not a claim of complete coverage. Candidates are never fetched or registered automatically and require human review. A successful HTTP check confirms availability and payload identity only—it does not validate epidemiological contents.

See the [project charter](docs/project_charter.md) for the intended scope and operating principles.

EbolaLens supports research and auditing of public epidemiological data. It must not be used for clinical decisions or independent outbreak management.

The licensing policy will be decided before the first public release.
