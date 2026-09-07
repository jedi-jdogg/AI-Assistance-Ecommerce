"""Klaviyo read connector: flows, campaigns, list growth. Used for the lifecycle audit."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

REVISION = "2025-07-15"


class KlaviyoClient:
    def __init__(self, api_key: str, timeout: float = 30.0):
        self.enabled = bool(api_key)
        self.http = httpx.Client(
            base_url="https://a.klaviyo.com/api",
            headers={"Authorization": f"Klaviyo-API-Key {api_key}", "revision": REVISION, "accept": "application/json"},
            timeout=timeout,
        )

    def _get_all(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        url: str | None = path
        first = True
        while url:
            resp = self.http.get(url, params=params if first else None)
            first = False
            resp.raise_for_status()
            body = resp.json()
            out.extend(body.get("data", []))
            url = (body.get("links") or {}).get("next")
            if url and url.startswith("https://a.klaviyo.com/api"):
                url = url[len("https://a.klaviyo.com/api"):]
        return out

    def flows(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        rows = self._get_all("/flows", {"fields[flow]": "name,status,trigger_type,archived", "filter": "equals(archived,false)"})
        return [{"id": r["id"], **r["attributes"]} for r in rows]

    def campaigns_sent(self, days: int, channel: str = "email") -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = self._get_all(
            "/campaigns",
            {
                "filter": f"and(equals(messages.channel,'{channel}'),greater-or-equal(scheduled_at,{since}))",
                "fields[campaign]": "name,status,send_time,scheduled_at",
            },
        )
        return [{"id": r["id"], **r["attributes"]} for r in rows if r["attributes"].get("status") in ("Sent", "Sending")]
