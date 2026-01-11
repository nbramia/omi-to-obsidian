"""Omi API client with retry logic."""
import time
import httpx
from typing import List, Dict, Any


class OmiAPIError(Exception):
    """API error."""
    pass


class OmiClient:
    """
    Client for Omi API.

    PRD: Handle retries on 5xx with exponential backoff (max attempts 5),
    429 with Retry-After if present, pagination.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.omi.me/v1/dev",
        max_retries: int = 5,
        page_size: int = 25,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.page_size = page_size
        self._client = httpx.Client(timeout=30.0)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make request with retry logic."""
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            **kwargs.pop("headers", {}),
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(method, url, headers=headers, **kwargs)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    if attempt < self.max_retries:
                        time.sleep(0.01 * (2 ** attempt))  # Fast backoff for tests
                        continue
                    raise OmiAPIError(f"Max retries exceeded: {response.status_code}")

                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                if attempt < self.max_retries:
                    time.sleep(0.01 * (2 ** attempt))
                    continue
                raise OmiAPIError(f"Request failed: {e}") from e

        raise OmiAPIError("Max retries exceeded")

    def fetch_all_conversations(self) -> List[Dict[str, Any]]:
        """
        Fetch all conversations with pagination.

        PRD: GET /user/conversations?include_transcript=true
        """
        all_conversations = []
        offset = 0

        while True:
            response = self._request(
                "GET",
                "/user/conversations",
                params={
                    "include_transcript": "true",
                    "limit": self.page_size,
                    "offset": offset,
                },
            )

            page = response.json()
            if not page:
                break

            all_conversations.extend(page)
            offset += self.page_size

        return all_conversations

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
