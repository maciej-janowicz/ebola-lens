"""Official-source registry, safe retrieval, and version tracking."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

USER_AGENT = "EbolaLens/0.0.0 source-registry (+https://github.com/)"
MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 15
OFFLINE_TIMESTAMP = "2000-01-01T00:00:00Z"


class ConfigurationError(ValueError):
    """Raised when the maintained source registry is unusable."""


class TransportError(RuntimeError):
    """Raised when a URL cannot be retrieved safely."""


@dataclass(frozen=True)
class FetchResult:
    """A bounded retrieval result from the transport boundary."""

    status: int
    resolved_url: str
    body: bytes
    media_type: str | None = None
    etag: str | None = None
    last_modified: str | None = None


Transport = Callable[[str, str | None, str | None], FetchResult]


def load_config(path: Path) -> dict[str, Any]:
    """Load and validate maintained JSON configuration."""
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"cannot load {path}: {exc}") from exc

    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise ConfigurationError("configuration schema_version must be 1")

    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for group in ("source_pages", "discovery_endpoints", "documents"):
        entries = config.get(group)
        if not isinstance(entries, list):
            raise ConfigurationError(f"{group} must be a list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ConfigurationError(f"every {group} entry must be an object")
            missing = {
                "id",
                "publisher",
                "source_type",
                "canonical_url",
                "discovery_method",
            } - entry.keys()
            if missing:
                raise ConfigurationError(
                    f"{group} entry is missing: {', '.join(sorted(missing))}"
                )
            if entry["id"] in seen_ids:
                raise ConfigurationError(f"duplicate id: {entry['id']}")
            seen_ids.add(entry["id"])
            parsed = urlparse(entry["canonical_url"])
            if parsed.scheme != "https" or not parsed.netloc:
                raise ConfigurationError(
                    f"canonical_url must be an absolute HTTPS URL: {entry['id']}"
                )
            if entry["canonical_url"] in seen_urls:
                raise ConfigurationError(f"duplicate canonical_url: {entry['canonical_url']}")
            seen_urls.add(entry["canonical_url"])
            if group == "documents":
                required_nullable = {"aliases", "report_number", "reporting_date", "publication_date"}
                if not required_nullable <= entry.keys() or not isinstance(entry["aliases"], list):
                    raise ConfigurationError(f"invalid document metadata: {entry['id']}")
    return config


def load_manifest(path: Path) -> dict[str, Any] | None:
    """Load prior generated state, if present."""
    if not path.exists():
        return None
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"cannot load prior manifest {path}: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ConfigurationError("manifest schema_version must be 1")
    return manifest


def write_manifest_atomic(path: Path, manifest: dict[str, Any]) -> None:
    """Write deterministic JSON and atomically replace the prior manifest."""
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def live_transport(
    url: str, etag: str | None = None, last_modified: str | None = None
) -> FetchResult:
    """Retrieve one URL with conditional headers, timeouts, and a size bound."""
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    request = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return FetchResult(304, exc.geturl(), b"", exc.headers.get_content_type())
        return FetchResult(exc.code, exc.geturl(), b"", exc.headers.get_content_type())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TransportError(str(exc)) from exc

    with response:
        declared_length = response.headers.get("Content-Length")
        if declared_length and int(declared_length) > MAX_DOWNLOAD_BYTES:
            raise TransportError(f"payload exceeds {MAX_DOWNLOAD_BYTES} byte limit")
        body = response.read(MAX_DOWNLOAD_BYTES + 1)
        if len(body) > MAX_DOWNLOAD_BYTES:
            raise TransportError(f"payload exceeds {MAX_DOWNLOAD_BYTES} byte limit")
        return FetchResult(
            response.status,
            response.geturl(),
            body,
            response.headers.get("Content-Type"),
            response.headers.get("ETag"),
            response.headers.get("Last-Modified"),
        )


def offline_transport(config: dict[str, Any], config_path: Path) -> Transport:
    """Build a deterministic transport backed by committed synthetic fixtures."""
    fixtures: dict[str, tuple[Path, str | None]] = {}
    for group in ("source_pages", "discovery_endpoints", "documents"):
        for entry in config[group]:
            fixture = entry.get("offline_fixture")
            if fixture:
                fixtures[entry["canonical_url"]] = (
                    config_path.parent / fixture,
                    entry.get("offline_media_type"),
                )

    def fetch(url: str, _etag: str | None = None, _modified: str | None = None) -> FetchResult:
        try:
            fixture_path, media_type = fixtures[url]
            body = fixture_path.read_bytes()
        except (KeyError, OSError) as exc:
            raise TransportError(f"offline fixture unavailable for {url}: {exc}") from exc
        return FetchResult(200, url, body, media_type)

    return fetch


def discover_rss_urls(body: bytes) -> list[str]:
    """Extract item and directly embedded PDF URLs from a confirmed RSS feed."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise TransportError(f"invalid RSS XML: {exc}") from exc
    urls = {
        element.text.strip()
        for element in root.findall("./channel/item/link")
        if element.text and element.text.strip().startswith("https://")
    }
    text = " ".join(root.itertext())
    for token in re.findall(r"pdfemb-data=([A-Za-z0-9_-]+)", text):
        try:
            padding = "=" * (-len(token) % 4)
            payload = json.loads(base64.urlsafe_b64decode(token + padding))
            embedded_url = payload.get("url")
            if isinstance(embedded_url, str) and embedded_url.startswith("https://"):
                urls.add(embedded_url)
        except (ValueError, json.JSONDecodeError):
            continue
    return sorted(urls)


def _prior_record(records: list[dict[str, Any]], record_id: str) -> dict[str, Any] | None:
    return next((record for record in records if record.get("id") == record_id), None)


def _conditional_metadata(
    record: dict[str, Any] | None, payloads: list[dict[str, Any]]
) -> tuple[str | None, str | None]:
    if not record or not record.get("versions"):
        return None, None
    version_id = record["versions"][-1]
    payload = next((item for item in payloads if item["version_id"] == version_id), None)
    if not payload:
        return None, None
    return payload.get("etag"), payload.get("last_modified")


def check_registry(
    config: dict[str, Any],
    prior: dict[str, Any] | None,
    fetch: Transport,
    checked_at: str,
) -> dict[str, Any]:
    """Check every registered URL while retaining successes and failures."""
    old = prior or {
        "source_pages": [],
        "discovery_endpoints": [],
        "documents": [],
        "payloads": [],
        "candidates": [],
    }
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": checked_at,
        "source_pages": [],
        "discovery_endpoints": [],
        "documents": [],
        "payloads": copy.deepcopy(old.get("payloads", [])),
        "candidates": copy.deepcopy(old.get("candidates", [])),
    }
    for candidate in manifest["candidates"]:
        candidate["newly_discovered"] = False

    for group in ("source_pages", "discovery_endpoints"):
        for entry in config[group]:
            previous = _prior_record(old.get(group, []), entry["id"])
            record = copy.deepcopy(previous) if previous else {
                "id": entry["id"],
                "first_seen": checked_at,
            }
            record.update(
                publisher=entry["publisher"],
                source_type=entry["source_type"],
                canonical_url=entry["canonical_url"],
                discovery_method=entry["discovery_method"],
                last_checked=checked_at,
                status="error",
                error=None,
            )
            try:
                result = fetch(entry["canonical_url"], None, None)
                record.update(
                    resolved_url=result.resolved_url,
                    http_status=result.status,
                    media_type=result.media_type,
                    byte_length=len(result.body),
                    etag=result.etag,
                    last_modified=result.last_modified,
                )
                if 200 <= result.status < 300:
                    record["status"] = "ok"
                    if group == "discovery_endpoints" and entry["source_type"] == "rss_feed":
                        discovered_urls = discover_rss_urls(result.body)
                        record["discovered_urls"] = discovered_urls
                        for candidate in manifest["candidates"]:
                            if candidate["discovery_endpoint"] == entry["id"]:
                                candidate["present_in_current_response"] = False
                        for url in discovered_urls:
                            candidate = next(
                                (item for item in manifest["candidates"] if item["url"] == url),
                                None,
                            )
                            if candidate is None:
                                candidate = {
                                    "url": url,
                                    "publisher": entry["publisher"],
                                    "discovery_endpoint": entry["id"],
                                    "first_seen": checked_at,
                                    "last_seen": checked_at,
                                    "present_in_current_response": True,
                                    "newly_discovered": True,
                                }
                                manifest["candidates"].append(candidate)
                            else:
                                candidate["last_seen"] = checked_at
                                candidate["present_in_current_response"] = True
                else:
                    record["status"] = "http_error"
                    record["error"] = f"HTTP {result.status}"
            except (TransportError, ValueError) as exc:
                record["status"] = "error"
                record["error"] = str(exc)
            manifest[group].append(record)

    for entry in config["documents"]:
        previous = _prior_record(old.get("documents", []), entry["id"])
        record = copy.deepcopy(previous) if previous else {
            "id": entry["id"],
            "first_seen": checked_at,
            "versions": [],
        }
        record.update(
            publisher=entry["publisher"],
            source_type=entry["source_type"],
            canonical_url=entry["canonical_url"],
            aliases=sorted(set(entry["aliases"])),
            report_number=entry["report_number"],
            reporting_date=entry["reporting_date"],
            publication_date=entry["publication_date"],
            discovery_method=entry["discovery_method"],
            last_checked=checked_at,
            status="error",
            error=None,
        )
        etag, modified = _conditional_metadata(previous, manifest["payloads"])
        try:
            result = fetch(entry["canonical_url"], etag, modified)
            record.update(
                resolved_url=result.resolved_url,
                http_status=result.status,
                media_type=result.media_type,
                etag=result.etag,
                last_modified=result.last_modified,
            )
            if result.status == 304 and record["versions"]:
                record["status"] = "unchanged"
            elif 200 <= result.status < 300:
                if len(result.body) > MAX_DOWNLOAD_BYTES:
                    raise TransportError(f"payload exceeds {MAX_DOWNLOAD_BYTES} byte limit")
                digest = hashlib.sha256(result.body).hexdigest()
                version_id = f"sha256:{digest}"
                payload = next(
                    (item for item in manifest["payloads"] if item["version_id"] == version_id),
                    None,
                )
                observed = sorted({entry["canonical_url"], result.resolved_url, *entry["aliases"]})
                if payload:
                    payload["observed_urls"] = sorted(set(payload["observed_urls"]) | set(observed))
                    payload["last_checked"] = checked_at
                    record["status"] = "unchanged" if version_id in record["versions"] else "alias"
                else:
                    payload = {
                        "version_id": version_id,
                        "sha256": digest,
                        "observed_urls": observed,
                        "retrieval_timestamp": checked_at,
                        "first_seen": checked_at,
                        "last_checked": checked_at,
                        "http_status": result.status,
                        "media_type": result.media_type,
                        "byte_length": len(result.body),
                        "etag": result.etag,
                        "last_modified": result.last_modified,
                    }
                    manifest["payloads"].append(payload)
                    record["status"] = "new_version"
                if version_id not in record["versions"]:
                    record["versions"].append(version_id)
                record["byte_length"] = len(result.body)
                record["sha256"] = digest
            else:
                record["status"] = "http_error"
                record["error"] = f"HTTP {result.status}"
        except (TransportError, ValueError) as exc:
            record["error"] = str(exc)
        manifest["documents"].append(record)

    manifest["payloads"].sort(key=lambda item: item["version_id"])
    manifest["candidates"].sort(key=lambda item: item["url"])
    return manifest


def summarize(manifest: dict[str, Any]) -> str:
    """Return a concise deterministic human-readable check report."""
    records = [
        *manifest["source_pages"],
        *manifest["discovery_endpoints"],
        *manifest["documents"],
    ]
    lines = [f"checked {len(records)} registered URLs at {manifest['generated_at']}"]
    for record in records:
        detail = f": {record['error']}" if record.get("error") else ""
        lines.append(f"{record['id']}: {record['status']}{detail}")
    candidates = manifest.get("candidates", [])
    new_candidates = [item for item in candidates if item["newly_discovered"]]
    present_candidates = [item for item in candidates if item["present_in_current_response"]]
    lines.append(f"total known candidates: {len(candidates)}")
    lines.append(f"newly discovered candidates: {len(new_candidates)}")
    lines.append(f"candidates present in current feed: {len(present_candidates)}")
    if new_candidates:
        lines.append("new candidate URLs:")
        lines.extend(f"  {item['url']}" for item in new_candidates)
    lines.append(f"unique document payloads: {len(manifest['payloads'])}")
    return "\n".join(lines)
