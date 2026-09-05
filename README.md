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

See the [project charter](docs/project_charter.md) for the intended scope and operating principles.

The licensing policy will be decided before the first public release.
