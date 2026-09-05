"""Deterministic tests for source checking and manifest state."""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

import ebolalens.__main__ as cli
from ebolalens.sources import (
    ConfigurationError,
    FetchResult,
    TransportError,
    check_registry,
    discover_rss_urls,
    load_config,
    summarize,
    write_manifest_atomic,
)


def config_for(*documents: tuple[str, str]) -> dict:
    return {
        "schema_version": 1,
        "source_pages": [],
        "discovery_endpoints": [],
        "documents": [
            {
                "id": document_id,
                "publisher": "INSP",
                "source_type": "official_report",
                "canonical_url": url,
                "aliases": [],
                "report_number": None,
                "reporting_date": None,
                "publication_date": None,
                "discovery_method": "test_fixture",
            }
            for document_id, url in documents
        ],
    }


def fixed_fetch(payloads: dict[str, bytes]):
    def fetch(url: str, _etag: str | None, _modified: str | None) -> FetchResult:
        return FetchResult(200, url, payloads[url], "application/pdf", '"fixture"')

    return fetch


def discovery_config() -> dict:
    return {
        "schema_version": 1,
        "source_pages": [],
        "discovery_endpoints": [
            {
                "id": "feed",
                "publisher": "INSP",
                "source_type": "rss_feed",
                "canonical_url": "https://example.test/feed/",
                "discovery_method": "test_fixture",
            }
        ],
        "documents": [],
    }


def rss_fetch(*urls: str):
    items = "".join(f"<item><link>{url}</link></item>" for url in urls)
    body = f"<rss><channel>{items}</channel></rss>".encode()

    def fetch(url: str, _etag: str | None, _modified: str | None) -> FetchResult:
        return FetchResult(200, url, body, "application/rss+xml")

    return fetch


def test_configuration_loading_and_validation(tmp_path: Path) -> None:
    valid = config_for(("document-1", "https://example.test/report.pdf"))
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(valid), encoding="utf-8")
    assert load_config(path) == valid

    valid["documents"][0]["canonical_url"] = "http://example.test/report.pdf"
    path.write_text(json.dumps(valid), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="HTTPS"):
        load_config(path)


def test_rss_discovery_extracts_post_and_embedded_pdf_urls() -> None:
    metadata = base64.urlsafe_b64encode(
        json.dumps({"url": "https://insp.cd/uploads/report.pdf"}).encode()
    ).decode().rstrip("=")
    feed = f"""<?xml version="1.0"?>
    <rss><channel><item><link>https://insp.cd/sitrep-post/</link>
    <description><![CDATA[<iframe src="https://insp.cd/?pdfemb-data={metadata}"></iframe>]]>
    </description></item></channel></rss>""".encode()

    assert discover_rss_urls(feed) == [
        "https://insp.cd/sitrep-post/",
        "https://insp.cd/uploads/report.pdf",
    ]


def test_candidate_history_first_and_unchanged_discovery() -> None:
    url = "https://example.test/report-a.pdf"
    first = check_registry(discovery_config(), None, rss_fetch(url), "2026-01-01T00:00:00Z")
    assert first["candidates"] == [
        {
            "url": url,
            "publisher": "INSP",
            "discovery_endpoint": "feed",
            "first_seen": "2026-01-01T00:00:00Z",
            "last_seen": "2026-01-01T00:00:00Z",
            "present_in_current_response": True,
            "newly_discovered": True,
        }
    ]

    second = check_registry(
        discovery_config(), first, rss_fetch(url), "2026-01-02T00:00:00Z"
    )
    assert second["candidates"][0]["first_seen"] == "2026-01-01T00:00:00Z"
    assert second["candidates"][0]["last_seen"] == "2026-01-02T00:00:00Z"
    assert second["candidates"][0]["newly_discovered"] is False
    assert "newly discovered candidates: 0" in summarize(second)


def test_new_candidate_on_later_run_is_reported() -> None:
    first_url = "https://example.test/report-a.pdf"
    new_url = "https://example.test/report-b.pdf"
    first = check_registry(
        discovery_config(), None, rss_fetch(first_url), "2026-01-01T00:00:00Z"
    )
    second = check_registry(
        discovery_config(),
        first,
        rss_fetch(first_url, new_url),
        "2026-01-02T00:00:00Z",
    )

    assert [item["url"] for item in second["candidates"]] == [first_url, new_url]
    assert [item["url"] for item in second["candidates"] if item["newly_discovered"]] == [
        new_url
    ]
    assert new_url in summarize(second)


def test_disappearing_candidate_is_retained_but_not_present() -> None:
    first_url = "https://example.test/report-a.pdf"
    second_url = "https://example.test/report-b.pdf"
    first = check_registry(
        discovery_config(),
        None,
        rss_fetch(first_url, second_url),
        "2026-01-01T00:00:00Z",
    )
    second = check_registry(
        discovery_config(), first, rss_fetch(second_url), "2026-01-02T00:00:00Z"
    )

    assert len(second["candidates"]) == 2
    assert second["candidates"][0]["url"] == first_url
    assert second["candidates"][0]["present_in_current_response"] is False
    assert second["candidates"][0]["last_seen"] == "2026-01-01T00:00:00Z"


@pytest.mark.parametrize("failure", ["transport", "xml"])
def test_discovery_failure_preserves_candidate_history(failure: str) -> None:
    url = "https://example.test/report-a.pdf"
    first = check_registry(discovery_config(), None, rss_fetch(url), "2026-01-01T00:00:00Z")

    def failed_fetch(feed_url: str, _etag: str | None, _modified: str | None) -> FetchResult:
        if failure == "transport":
            raise TransportError("feed unavailable")
        return FetchResult(200, feed_url, b"not xml", "application/rss+xml")

    second = check_registry(discovery_config(), first, failed_fetch, "2026-01-02T00:00:00Z")
    assert second["candidates"][0]["url"] == url
    assert second["candidates"][0]["present_in_current_response"] is True
    assert second["candidates"][0]["last_seen"] == "2026-01-01T00:00:00Z"
    assert second["discovery_endpoints"][0]["status"] == "error"
    assert second["discovery_endpoints"][0]["error"]
    assert second["discovery_endpoints"][0]["discovered_urls"] == [url]
    assert second["discovery_endpoints"][0]["error"] in summarize(second)


def test_unchanged_content_at_same_url() -> None:
    url = "https://example.test/report.pdf"
    config = config_for(("document-1", url))
    first = check_registry(config, None, fixed_fetch({url: b"same"}), "2026-01-01T00:00:00Z")
    second = check_registry(config, first, fixed_fetch({url: b"same"}), "2026-01-02T00:00:00Z")

    assert len(second["payloads"]) == 1
    assert second["documents"][0]["status"] == "unchanged"
    assert len(second["documents"][0]["versions"]) == 1


def test_304_retains_conditional_metadata_for_future_checks() -> None:
    url = "https://example.test/report.pdf"
    config = config_for(("document-1", url))
    calls: list[tuple[str | None, str | None]] = []

    def fetch(_url: str, etag: str | None, modified: str | None) -> FetchResult:
        calls.append((etag, modified))
        if len(calls) == 1:
            return FetchResult(
                200,
                url,
                b"same",
                "application/pdf",
                '"etag-1"',
                "Wed, 01 Jan 2026 00:00:00 GMT",
            )
        return FetchResult(304, url, b"")

    first = check_registry(config, None, fetch, "2026-01-01T00:00:00Z")
    second = check_registry(config, first, fetch, "2026-01-02T00:00:00Z")
    third = check_registry(config, second, fetch, "2026-01-03T00:00:00Z")

    expected = ('"etag-1"', "Wed, 01 Jan 2026 00:00:00 GMT")
    assert calls == [(None, None), expected, expected]
    assert third["documents"][0]["status"] == "unchanged"


def test_changed_bytes_create_new_version() -> None:
    url = "https://example.test/report.pdf"
    config = config_for(("document-1", url))
    first = check_registry(config, None, fixed_fetch({url: b"before"}), "2026-01-01T00:00:00Z")
    second = check_registry(config, first, fixed_fetch({url: b"after"}), "2026-01-02T00:00:00Z")

    assert len(second["payloads"]) == 2
    assert len(second["documents"][0]["versions"]) == 2
    assert second["documents"][0]["status"] == "new_version"


def test_identical_bytes_at_second_url_are_alias() -> None:
    first_url = "https://example.test/first.pdf"
    second_url = "https://example.test/second.pdf"
    config = config_for(("document-1", first_url), ("document-2", second_url))
    manifest = check_registry(
        config,
        None,
        fixed_fetch({first_url: b"identical", second_url: b"identical"}),
        "2026-01-01T00:00:00Z",
    )

    assert len(manifest["payloads"]) == 1
    assert manifest["payloads"][0]["observed_urls"] == [first_url, second_url]
    assert manifest["documents"][1]["status"] == "alias"


def test_transport_failure_preserves_prior_state() -> None:
    url = "https://example.test/report.pdf"
    config = config_for(("document-1", url))
    first = check_registry(config, None, fixed_fetch({url: b"retained"}), "2026-01-01T00:00:00Z")

    def failing_fetch(_url: str, _etag: str | None, _modified: str | None) -> FetchResult:
        raise TransportError("timed out")

    second = check_registry(config, first, failing_fetch, "2026-01-02T00:00:00Z")
    assert second["payloads"] == first["payloads"]
    assert second["documents"][0]["versions"] == first["documents"][0]["versions"]
    assert second["documents"][0]["status"] == "error"
    assert second["documents"][0]["error"] == "timed out"


def test_atomic_manifest_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "generated" / "manifest.json"
    replacements: list[tuple[str, Path]] = []
    real_replace = __import__("os").replace

    def recording_replace(source: str, destination: Path) -> None:
        assert Path(source).parent == target.parent
        replacements.append((source, destination))
        real_replace(source, destination)

    monkeypatch.setattr("ebolalens.sources.os.replace", recording_replace)
    manifest = {"schema_version": 1, "payloads": []}
    write_manifest_atomic(target, manifest)

    assert json.loads(target.read_text(encoding="utf-8")) == manifest
    assert len(replacements) == 1
    assert not list(target.parent.glob(f".{target.name}.*"))


def test_offline_cli(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ebolalens",
            "sources",
            "check",
            "--offline",
            "--manifest",
            str(manifest),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "checked 7 registered URLs" in result.stdout
    assert len(json.loads(manifest.read_text(encoding="utf-8"))["payloads"]) == 3


def test_cli_uses_isolated_default_manifests_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected: list[tuple[Path, bool]] = []

    def fake_check(_config: Path, manifest: Path, live: bool) -> int:
        selected.append((manifest, live))
        return 0

    monkeypatch.setattr(cli, "_check_sources", fake_check)
    monkeypatch.setattr(sys, "argv", ["ebolalens", "sources", "check", "--offline"])
    assert cli.main() == 0
    monkeypatch.setattr(sys, "argv", ["ebolalens", "sources", "check", "--live"])
    assert cli.main() == 0
    override = Path("custom.json")
    monkeypatch.setattr(
        sys,
        "argv",
        ["ebolalens", "sources", "check", "--offline", "--manifest", str(override)],
    )
    assert cli.main() == 0

    assert selected[0] == (cli.DEFAULT_OFFLINE_MANIFEST, False)
    assert selected[1] == (cli.DEFAULT_LIVE_MANIFEST, True)
    assert selected[0][0] != selected[1][0]
    assert selected[2] == (override, False)
