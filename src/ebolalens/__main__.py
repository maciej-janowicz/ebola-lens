"""Command-line entry point for EbolaLens."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from ebolalens import __version__
from ebolalens.sources import (
    ConfigurationError,
    OFFLINE_TIMESTAMP,
    check_registry,
    live_transport,
    load_config,
    load_manifest,
    offline_transport,
    summarize,
    write_manifest_atomic,
)

DEFAULT_CONFIG = Path("data/sources.json")
DEFAULT_LIVE_MANIFEST = Path("data/generated/source_manifest.json")
DEFAULT_OFFLINE_MANIFEST = Path("data/generated/offline_source_manifest.json")


def _manifest_path(explicit_path: Path | None, live: bool) -> Path:
    """Select isolated mode-specific state unless the user overrides it."""
    if explicit_path is not None:
        return explicit_path
    return DEFAULT_LIVE_MANIFEST if live else DEFAULT_OFFLINE_MANIFEST


def _list_sources(config_path: Path) -> int:
    config = load_config(config_path)
    for heading, group in (
        ("Source pages", "source_pages"),
        ("Discovery endpoints", "discovery_endpoints"),
        ("Known documents", "documents"),
    ):
        print(f"{heading}:")
        for entry in config[group]:
            print(f"  {entry['id']} [{entry['publisher']}]: {entry['canonical_url']}")
    return 0


def _check_sources(config_path: Path, manifest_path: Path, live: bool) -> int:
    config = load_config(config_path)
    prior = load_manifest(manifest_path)
    if live:
        fetch = live_transport
        checked_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    else:
        fetch = offline_transport(config, config_path)
        checked_at = OFFLINE_TIMESTAMP
    manifest = check_registry(config, prior, fetch, checked_at)
    write_manifest_atomic(manifest_path, manifest)
    print(summarize(manifest))
    return 0


def _document_rows(manifest: dict) -> list[dict]:
    """Return canonical document records in stable order."""
    documents = manifest.get("documents")
    payloads = manifest.get("payloads")
    if not isinstance(documents, list) or not isinstance(payloads, list):
        raise ConfigurationError("manifest must contain documents and payloads lists")
    if not all(isinstance(item, dict) and isinstance(item.get("id"), str) for item in documents):
        raise ConfigurationError("manifest contains an invalid document record")
    return sorted(documents, key=lambda item: item["id"])


def _list_documents(manifest_path: Path, as_json: bool) -> int:
    """Display an existing manifest without performing retrieval."""
    manifest = load_manifest(manifest_path)
    if manifest is None:
        raise ConfigurationError(f"manifest does not exist: {manifest_path}")
    documents = _document_rows(manifest)
    if as_json:
        print(json.dumps(documents, indent=2, sort_keys=True))
        return 0

    headings = ("ID", "DATE", "TITLE / NAME", "URLS", "STATUS", "SHA-256")
    rows = []
    for document in documents:
        date = document.get("reporting_date") or document.get("publication_date") or "-"
        title = document.get("title") or document["id"]
        urls = document.get("all_urls") or [
            document.get("canonical_url"), *document.get("aliases", [])
        ]
        rows.append((
            document["id"],
            date,
            str(title)[:32],
            str(len({url for url in urls if url})),
            str(document.get("status") or "-"),
            str(document.get("sha256") or "-")[:12],
        ))
    widths = [max(len(headings[i]), *(len(row[i]) for row in rows)) for i in range(len(headings))]
    print("  ".join(value.ljust(widths[i]) for i, value in enumerate(headings)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))
    return 0


def main() -> int:
    """Run the EbolaLens command-line interface."""
    parser = argparse.ArgumentParser(prog="ebolalens")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    sources_parser = subparsers.add_parser("sources", help="manage official sources")
    sources_subparsers = sources_parser.add_subparsers(dest="sources_command", required=True)

    list_parser = sources_subparsers.add_parser("list", help="list registered sources")
    list_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)

    check_parser = sources_subparsers.add_parser("check", help="check registered sources")
    mode = check_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline", action="store_true", help="use committed fixtures")
    mode.add_argument("--live", action="store_true", help="retrieve registered live URLs")
    check_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    check_parser.add_argument("--manifest", type=Path)

    documents_parser = subparsers.add_parser("documents", help="inspect canonical documents")
    documents_subparsers = documents_parser.add_subparsers(
        dest="documents_command", required=True
    )
    documents_list_parser = documents_subparsers.add_parser(
        "list", help="list documents from an existing manifest"
    )
    documents_list_parser.add_argument("--manifest", type=Path, required=True)
    documents_list_parser.add_argument("--json", action="store_true", help="emit JSON")

    args = parser.parse_args()
    try:
        if args.command == "sources" and args.sources_command == "list":
            return _list_sources(args.config)
        if args.command == "sources" and args.sources_command == "check":
            return _check_sources(
                args.config,
                _manifest_path(args.manifest, args.live),
                args.live,
            )
        if args.command == "documents" and args.documents_command == "list":
            return _list_documents(args.manifest, args.json)
    except (ConfigurationError, OSError) as exc:
        parser.error(str(exc))
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
