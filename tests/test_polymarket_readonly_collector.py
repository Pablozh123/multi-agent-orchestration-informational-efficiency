from __future__ import annotations

import json
from pathlib import Path

import httpx
import pandas as pd

from operations.collectors.polymarket_readonly import (
    CLOB_BASE_URL,
    DATA_API_BASE_URL,
    GAMMA_BASE_URL,
    build_market_snapshot_rows,
    build_wallet_activity_rows,
    build_watchlist_from_curated_watchlist,
    build_watchlist_from_gamma_markets,
    collect_readonly_polymarket_inputs,
    main,
    mock_gamma_markets,
    mock_midpoints_for_watchlist,
    mock_trade_rows,
)
from operations.collectors.polymarket_watchlist import CURATED_WATCHLIST_COLUMNS


COLLECTED_AT = "2026-05-22T12:07:30Z"


def test_build_watchlist_filters_politics_geo_markets() -> None:
    watchlist = build_watchlist_from_gamma_markets(
        mock_gamma_markets(),
        collected_at=pd.Timestamp(COLLECTED_AT).to_pydatetime(),
        bucket_minutes=5,
        max_markets=5,
    )

    assert len(watchlist) == 1
    assert tuple(watchlist.columns) == (
        "collector_received_at_utc",
        "source_timestamp_utc",
        "bucket_start_utc",
        "bucket_end_utc",
        "timestamp_source",
        "bucket_status",
        "source_class",
        "source_name",
        "watch_id",
        "market_id",
        "condition_id",
        "token_ids",
        "question",
        "category",
        "subcategory",
        "status",
    )
    assert watchlist.iloc[0]["source_class"] == "market_discovery"
    assert watchlist.iloc[0]["bucket_end_utc"] == "2026-05-22T12:05:00Z"


def test_build_watchlist_from_curated_watchlist_uses_accepted_rows_only(
    tmp_path: Path,
) -> None:
    curated_path = _curated_watchlist_path(tmp_path)

    watchlist = build_watchlist_from_curated_watchlist(
        curated_path,
        collected_at=pd.Timestamp(COLLECTED_AT).to_pydatetime(),
        bucket_minutes=5,
        max_markets=5,
    )

    assert len(watchlist) == 1
    assert watchlist.iloc[0]["watch_id"] == "accepted_001"
    assert watchlist.iloc[0]["source_name"] == "polymarket_curated_watchlist"
    assert watchlist.iloc[0]["status"] == "active"


def test_watchlist_filter_excludes_sports_only_markets() -> None:
    markets = [
        {
            "id": "sports_iran",
            "question": "Will Iran win the 2026 FIFA World Cup?",
            "conditionId": "0x" + "c" * 64,
            "slug": "iran-fifa-world-cup",
            "category": "politics",
            "active": True,
            "closed": False,
            "archived": False,
            "clobTokenIds": json.dumps(["555", "666"]),
        },
        {
            "id": "geo_taiwan",
            "question": "Will China invade Taiwan before the end of 2026?",
            "conditionId": "0x" + "d" * 64,
            "slug": "china-invade-taiwan",
            "category": "politics",
            "active": True,
            "closed": False,
            "archived": False,
            "clobTokenIds": json.dumps(["777", "888"]),
        },
    ]

    watchlist = build_watchlist_from_gamma_markets(
        markets,
        collected_at=pd.Timestamp(COLLECTED_AT).to_pydatetime(),
        bucket_minutes=5,
        max_markets=5,
    )

    assert len(watchlist) == 1
    assert "China invade Taiwan" in watchlist.iloc[0]["question"]


def test_watchlist_filter_does_not_accept_category_only_politics() -> None:
    markets = [
        {
            "id": "category_only",
            "question": "New Rihanna Album before GTA VI?",
            "conditionId": "0x" + "e" * 64,
            "slug": "new-rihanna-album-before-gta-vi",
            "category": "politics",
            "active": True,
            "closed": False,
            "archived": False,
            "clobTokenIds": json.dumps(["999", "1000"]),
        }
    ]

    watchlist = build_watchlist_from_gamma_markets(
        markets,
        collected_at=pd.Timestamp(COLLECTED_AT).to_pydatetime(),
        bucket_minutes=5,
        max_markets=5,
    )

    assert watchlist.empty


def test_watchlist_filter_does_not_accept_tag_only_politics() -> None:
    markets = [
        {
            "id": "tag_only",
            "question": "Will Harvey Weinstein be sentenced to no prison time?",
            "conditionId": "0x" + "f" * 64,
            "slug": "harvey-weinstein-sentence",
            "category": "politics",
            "tags": [{"label": "Politics"}],
            "active": True,
            "closed": False,
            "archived": False,
            "clobTokenIds": json.dumps(["1001", "1002"]),
        }
    ]

    watchlist = build_watchlist_from_gamma_markets(
        markets,
        collected_at=pd.Timestamp(COLLECTED_AT).to_pydatetime(),
        bucket_minutes=5,
        max_markets=5,
    )

    assert watchlist.empty


def test_build_market_and_wallet_rows_are_validator_ready() -> None:
    collected_at = pd.Timestamp(COLLECTED_AT).to_pydatetime()
    watchlist = build_watchlist_from_gamma_markets(
        mock_gamma_markets(),
        collected_at=collected_at,
        bucket_minutes=5,
        max_markets=5,
    )
    market = build_market_snapshot_rows(
        watchlist,
        mock_midpoints_for_watchlist(watchlist),
        collected_at=collected_at,
        bucket_minutes=5,
        source_name="mock_clob",
    )
    wallets = build_wallet_activity_rows(
        watchlist,
        mock_trade_rows(watchlist, collected_at=collected_at),
        collected_at=collected_at,
        bucket_minutes=5,
        source_name="mock_data_api",
    )

    assert len(market) == 2
    assert len(wallets) == 1
    assert set(wallets["tier"]) == {"all_tiers"}
    assert int(wallets.iloc[0]["active_wallets"]) == 2
    assert int(wallets.iloc[0]["trade_count"]) == 2
    assert "wallet_address" not in wallets.columns


def test_collect_mock_outputs_write_validated_files(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    result = collect_readonly_polymarket_inputs(
        source="mock",
        collected_at_utc=COLLECTED_AT,
        **paths,
    )

    watchlist = pd.read_csv(paths["watchlist_path"])
    market = pd.read_csv(paths["market_snapshots_path"])
    wallets = pd.read_csv(paths["wallet_tier_snapshots_path"])
    events = pd.read_csv(paths["event_candidates_path"])
    report = json.loads(paths["validation_report_path"].read_text(encoding="utf-8"))
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    assert result.watchlist_row_count == len(watchlist)
    assert result.market_snapshot_row_count == len(market)
    assert result.wallet_tier_snapshot_row_count == len(wallets)
    assert result.event_candidate_row_count == len(events) == 0
    assert report["status"] == "pass"
    assert metadata["method"]["read_only"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["event_candidate_row_count"] == 0
    assert metadata["limitations"]["does_not_send_orders"] is True
    for frame in (watchlist, market, wallets, events):
        assert "wallet_address" not in frame.columns


def test_collect_mock_append_keeps_history_without_duplicate_watchlist(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    collect_readonly_polymarket_inputs(
        source="mock",
        collected_at_utc=COLLECTED_AT,
        **paths,
    )
    result = collect_readonly_polymarket_inputs(
        source="mock",
        collected_at_utc="2026-05-22T12:12:30Z",
        append=True,
        **paths,
    )

    watchlist = pd.read_csv(paths["watchlist_path"])
    market = pd.read_csv(paths["market_snapshots_path"])
    wallets = pd.read_csv(paths["wallet_tier_snapshots_path"])
    assert result.watchlist_row_count == 1
    assert len(watchlist) == 1
    assert len(market) == 4
    assert len(wallets) == 2


def test_collect_mock_append_deduplicates_same_bucket_token_ids(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    collect_readonly_polymarket_inputs(
        source="mock",
        collected_at_utc=COLLECTED_AT,
        **paths,
    )
    result = collect_readonly_polymarket_inputs(
        source="mock",
        collected_at_utc=COLLECTED_AT,
        append=True,
        **paths,
    )

    market = pd.read_csv(paths["market_snapshots_path"])
    wallets = pd.read_csv(paths["wallet_tier_snapshots_path"])
    assert result.market_snapshot_row_count == 2
    assert result.wallet_tier_snapshot_row_count == 1
    assert len(market) == 2
    assert len(wallets) == 1


def test_collect_live_with_mock_transport_uses_public_read_endpoints(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    requested_urls: list[str] = []
    collected_at = pd.Timestamp(COLLECTED_AT).to_pydatetime()

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{GAMMA_BASE_URL}/markets"):
            return httpx.Response(200, json=mock_gamma_markets())
        if str(request.url).startswith(f"{CLOB_BASE_URL}/midpoint"):
            return httpx.Response(200, json={"mid_price": "0.55"})
        if str(request.url).startswith(f"{DATA_API_BASE_URL}/trades"):
            return httpx.Response(200, json=mock_trade_rows(_watchlist(collected_at), collected_at=collected_at))
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_readonly_polymarket_inputs(
            source="live",
            client=client,
            collected_at_utc=COLLECTED_AT,
            **paths,
        )

    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    assert result.watchlist_row_count == 1
    assert result.market_snapshot_row_count == 2
    assert result.wallet_tier_snapshot_row_count == 1
    assert result.event_candidate_row_count == 0
    assert metadata["method"]["uses_public_gamma_markets"] is True
    assert any(url.startswith(f"{GAMMA_BASE_URL}/markets") for url in requested_urls)
    assert any(url.startswith(f"{CLOB_BASE_URL}/midpoint") for url in requested_urls)
    assert any(url.startswith(f"{DATA_API_BASE_URL}/trades") for url in requested_urls)


def test_collect_live_with_curated_watchlist_skips_gamma_discovery(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    curated_path = _curated_watchlist_path(tmp_path)
    requested_urls: list[str] = []
    collected_at = pd.Timestamp(COLLECTED_AT).to_pydatetime()

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{CLOB_BASE_URL}/midpoint"):
            return httpx.Response(200, json={"mid_price": "0.55"})
        if str(request.url).startswith(f"{DATA_API_BASE_URL}/trades"):
            return httpx.Response(
                200,
                json=mock_trade_rows(
                    _curated_live_watchlist(curated_path, collected_at),
                    collected_at=collected_at,
                ),
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_readonly_polymarket_inputs(
            source="live",
            client=client,
            collected_at_utc=COLLECTED_AT,
            curated_watchlist_path=curated_path,
            **paths,
        )

    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    watchlist = pd.read_csv(paths["watchlist_path"])
    assert result.watchlist_row_count == 1
    assert len(watchlist) == 1
    assert watchlist.iloc[0]["watch_id"] == "accepted_001"
    assert metadata["method"]["uses_curated_watchlist"] is True
    assert metadata["method"]["uses_public_gamma_markets"] is False
    assert not any(url.startswith(f"{GAMMA_BASE_URL}/markets") for url in requested_urls)
    assert any(url.startswith(f"{CLOB_BASE_URL}/midpoint") for url in requested_urls)
    assert any(url.startswith(f"{DATA_API_BASE_URL}/trades") for url in requested_urls)


def test_cli_mock_source_writes_outputs(tmp_path: Path, capsys) -> None:
    paths = _paths(tmp_path)

    exit_code = main(
        [
            "--source",
            "mock",
            "--watchlist-output",
            str(paths["watchlist_path"]),
            "--market-snapshots-output",
            str(paths["market_snapshots_path"]),
            "--wallet-tier-snapshots-output",
            str(paths["wallet_tier_snapshots_path"]),
            "--event-candidates-output",
            str(paths["event_candidates_path"]),
            "--validation-report-output",
            str(paths["validation_report_path"]),
            "--metadata-output",
            str(paths["metadata_path"]),
            "--collected-at-utc",
            COLLECTED_AT,
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "watchlist_row_count" in captured.out
    assert paths["metadata_path"].exists()


def _watchlist(collected_at) -> pd.DataFrame:
    return build_watchlist_from_gamma_markets(
        mock_gamma_markets(),
        collected_at=collected_at,
        bucket_minutes=5,
        max_markets=5,
    )


def _curated_live_watchlist(path: Path, collected_at) -> pd.DataFrame:
    return build_watchlist_from_curated_watchlist(
        path,
        collected_at=collected_at,
        bucket_minutes=5,
        max_markets=5,
    )


def _curated_watchlist_path(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "curated_watchlist.csv"
    rows = [
        {
            "watch_id": "accepted_001",
            "market_id": "0x" + "a" * 64,
            "condition_id": "0x" + "a" * 64,
            "token_ids": "111,222",
            "question": "Will a major election market resolve yes?",
            "category": "politics",
            "subcategory": "major-election-market",
            "monitoring_scope": "election",
            "review_status": "accepted",
            "source_url": "https://gamma-api.polymarket.com/markets?id=accepted_001",
            "inclusion_reason": "official_gamma_active_us_election_market",
            "exclusion_reason": "",
            "reviewed_by": "codex_test",
            "reviewed_at_utc": "2026-05-22T12:00:00Z",
            "notes": "fixture",
        },
        {
            "watch_id": "candidate_001",
            "market_id": "0x" + "b" * 64,
            "condition_id": "0x" + "b" * 64,
            "token_ids": "333,444",
            "question": "Will an unchecked candidate market resolve yes?",
            "category": "politics",
            "subcategory": "unchecked-market",
            "monitoring_scope": "election",
            "review_status": "candidate",
            "source_url": "",
            "inclusion_reason": "",
            "exclusion_reason": "",
            "reviewed_by": "",
            "reviewed_at_utc": "",
            "notes": "not monitor ready",
        },
    ]
    pd.DataFrame(rows, columns=CURATED_WATCHLIST_COLUMNS).to_csv(path, index=False)
    return path


def _paths(root: Path) -> dict[str, Path]:
    return {
        "watchlist_path": root / "watchlist.csv",
        "market_snapshots_path": root / "market.csv",
        "wallet_tier_snapshots_path": root / "wallet.csv",
        "event_candidates_path": root / "events.csv",
        "validation_report_path": root / "report.json",
        "metadata_path": root / "metadata.json",
    }
