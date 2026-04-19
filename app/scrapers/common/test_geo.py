"""Tests for the hybrid geocoder (gazetteer + Nominatim fallback)."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

try:
    from app.scrapers.common.geo import infer_geo, infer_geo_async, GAZETTEER, UNKNOWN_GEO, _nominatim_cache
except ImportError:
    from geo import infer_geo, infer_geo_async, GAZETTEER, UNKNOWN_GEO, _nominatim_cache


@pytest.fixture(autouse=True)
def clear_nominatim_cache():
    """Clear the Nominatim cache before each test for isolation."""
    _nominatim_cache.clear()
    yield
    _nominatim_cache.clear()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FAKE_NOMINATIM_RESPONSE = [
    {
        "lat": "36.1699",
        "lon": "-115.1398",
        "display_name": "Las Vegas, Clark County, Nevada, United States",
        "address": {
            "city": "Las Vegas",
            "state": "Nevada",
            "country": "United States",
        },
    }
]


def _mock_nominatim_response(json_data=None, status_code=200):
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else []
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


# ---------------------------------------------------------------------------
# Sync tests (gazetteer + sync Nominatim fallback)
# ---------------------------------------------------------------------------


class TestInferGeoSync:
    def test_gazetteer_hit_from_hint(self):
        """Hint match on 'Sudan' should return Sudan with boosted confidence."""
        result = infer_geo(["Sudan"], "")
        assert result["name"] == "Sudan"
        assert result["country"] == "Sudan"
        assert result["lat"] == pytest.approx(15.5007, abs=0.01)
        # Hint match should boost confidence above the base 0.7
        assert result["confidence"] > GAZETTEER["sudan"]["confidence"]

    def test_gazetteer_hit_from_text(self):
        """Text containing 'Khartoum' should resolve to that city."""
        result = infer_geo([], "fighting in Khartoum")
        assert result["name"] == "Khartoum"
        assert result["country"] == "Sudan"
        assert result["resolution"] == "city"
        # Text-only match should still have reasonable confidence
        assert result["confidence"] > 0.4

    def test_gazetteer_miss_falls_back_to_nominatim(self):
        """Location not in the gazetteer should fall back to Nominatim (sync)."""
        mock_resp = _mock_nominatim_response(FAKE_NOMINATIM_RESPONSE)

        with patch("httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_resp
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = infer_geo(["Las Vegas"], "")
            assert result["lat"] == pytest.approx(36.1699, abs=0.01)
            assert "Las Vegas" in result["name"]
            mock_client.get.assert_called_once()

    def test_sync_nominatim_failure_returns_unknown(self):
        """When sync Nominatim fails, should return UNKNOWN_GEO."""
        with patch("httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.get.side_effect = Exception("connection refused")
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = infer_geo(["Nonexistentville"], "")
            assert result["name"] == UNKNOWN_GEO["name"]

    def test_confidence_hint_higher_than_text(self):
        """A hint match should produce higher confidence than a text-only match
        for the same gazetteer entry."""
        hint_result = infer_geo(["Khartoum"], "")
        text_result = infer_geo([], "fighting in Khartoum yesterday")
        assert hint_result["confidence"] > text_result["confidence"]


# ---------------------------------------------------------------------------
# Async / Nominatim fallback tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestInferGeoAsync:
    async def test_async_gazetteer_hit_skips_nominatim(self):
        """When the gazetteer resolves the hint, Nominatim should never be called."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await infer_geo_async(["Sudan"], "")

            assert result["name"] == "Sudan"
            assert result["country"] == "Sudan"
            # httpx should not have been used at all
            mock_client.get.assert_not_called()

    async def test_async_nominatim_fallback(self):
        """Gazetteer miss should fall back to Nominatim and return coordinates."""
        mock_resp = _mock_nominatim_response(FAKE_NOMINATIM_RESPONSE)

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await infer_geo_async(["Las Vegas"], "")

            assert result["lat"] == pytest.approx(36.1699, abs=0.01)
            assert result["lon"] == pytest.approx(-115.1398, abs=0.01)
            assert "Las Vegas" in result["name"]
            mock_client.get.assert_called_once()

    async def test_async_nominatim_failure_returns_unknown(self):
        """When Nominatim returns empty results or errors, should return UNKNOWN_GEO."""
        # Case 1: empty results list
        mock_resp = _mock_nominatim_response(json_data=[])

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await infer_geo_async(["Nonexistentville"], "")
            assert result["name"] == UNKNOWN_GEO["name"]
            assert result["confidence"] == UNKNOWN_GEO["confidence"]

    async def test_async_nominatim_http_error_returns_unknown(self):
        """When Nominatim HTTP call raises, should return UNKNOWN_GEO."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("connection refused")
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await infer_geo_async(["Nonexistentville"], "")
            assert result["name"] == UNKNOWN_GEO["name"]

    async def test_async_cache_prevents_duplicate_calls(self):
        """Second call with same input should use cache, not call Nominatim again."""
        mock_resp = _mock_nominatim_response(FAKE_NOMINATIM_RESPONSE)

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result1 = await infer_geo_async(["Las Vegas"], "")
            result2 = await infer_geo_async(["Las Vegas"], "")

            # Both calls should return the same data
            assert result1["lat"] == result2["lat"]
            assert result1["lon"] == result2["lon"]
            # httpx.get should only have been called once (second was cached)
            assert mock_client.get.call_count == 1

    async def test_nominatim_confidence_value(self):
        """Nominatim-sourced results should have confidence around 0.65."""
        mock_resp = _mock_nominatim_response(FAKE_NOMINATIM_RESPONSE)

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await infer_geo_async(["Las Vegas"], "")

            # Nominatim confidence should be moderate — around 0.65 +/- 0.15
            assert 0.50 <= result["confidence"] <= 0.80
