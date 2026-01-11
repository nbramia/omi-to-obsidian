"""Tests for Omi API client."""
import pytest
import json
from omi_sync.api_client import OmiClient, OmiAPIError


class TestOmiClient:
    def test_fetch_conversations_with_pagination(self, httpx_mock, fixtures_dir):
        """Client handles pagination correctly."""
        with open(fixtures_dir / "conversations_page1.json") as f:
            page1 = json.load(f)
        with open(fixtures_dir / "conversations_page2.json") as f:
            page2 = json.load(f)

        httpx_mock.add_response(
            url="https://api.omi.me/v1/dev/user/conversations?include_transcript=true&limit=25&offset=0",
            json=page1,
        )
        httpx_mock.add_response(
            url="https://api.omi.me/v1/dev/user/conversations?include_transcript=true&limit=25&offset=25",
            json=page2,
        )
        httpx_mock.add_response(
            url="https://api.omi.me/v1/dev/user/conversations?include_transcript=true&limit=25&offset=50",
            json=[],
        )

        client = OmiClient(api_key="test-key", base_url="https://api.omi.me/v1/dev")
        conversations = client.fetch_all_conversations()

        assert len(conversations) == 5

    def test_authorization_header(self, httpx_mock):
        """Client sends correct authorization header."""
        httpx_mock.add_response(json=[])

        client = OmiClient(api_key="secret-key", base_url="https://api.omi.me/v1/dev")
        client.fetch_all_conversations()

        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == "Bearer secret-key"

    def test_retry_on_5xx(self, httpx_mock):
        """Client retries on 5xx errors."""
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(json=[])

        client = OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev")
        conversations = client.fetch_all_conversations()

        assert len(httpx_mock.get_requests()) == 3
        assert conversations == []

    def test_rate_limit_429_with_retry_after(self, httpx_mock):
        """Client respects Retry-After header on 429."""
        httpx_mock.add_response(
            status_code=429,
            headers={"Retry-After": "0"},
        )
        httpx_mock.add_response(json=[])

        client = OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev")
        conversations = client.fetch_all_conversations()

        assert len(httpx_mock.get_requests()) == 2

    def test_max_retries_exceeded_raises(self, httpx_mock):
        """Client raises after max retries exceeded."""
        for _ in range(6):
            httpx_mock.add_response(status_code=503)

        client = OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev")

        with pytest.raises(OmiAPIError, match="Max retries"):
            client.fetch_all_conversations()

    def test_empty_response_stops_pagination(self, httpx_mock):
        """Empty response stops pagination loop."""
        httpx_mock.add_response(json=[])

        client = OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev")
        conversations = client.fetch_all_conversations()

        assert conversations == []
        assert len(httpx_mock.get_requests()) == 1

    def test_context_manager(self, httpx_mock):
        """Client works as context manager."""
        httpx_mock.add_response(json=[])

        with OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev") as client:
            conversations = client.fetch_all_conversations()

        assert conversations == []
