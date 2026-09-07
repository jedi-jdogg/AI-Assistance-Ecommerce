"""Shopify Admin API connector: GraphQL + ShopifyQL analytics.

Two access paths are implemented for sales history so the agent keeps working
even if the `shopifyqlQuery` field is unavailable on the shop's API version:
  1. ShopifyQL (preferred; also the only source for sessions / funnel data).
  2. Orders pagination (fallback for daily sales).
"""
from __future__ import annotations

import re
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Iterator

import httpx

from ..models import DailyFunnel, DailySales, Variant


class ShopifyError(RuntimeError):
    pass


class ShopifyClient:
    def __init__(self, shop: str, token: str, api_version: str = "2025-07", timeout: float = 60.0):
        if not shop or not token:
            raise ShopifyError("SHOPIFY_SHOP and SHOPIFY_ACCESS_TOKEN are required")
        self.url = f"https://{shop}/admin/api/{api_version}/graphql.json"
        self.headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
        self.http = httpx.Client(timeout=timeout)

    # --------------------------------------------------------------------- core
    def graphql(self, query: str, variables: dict[str, Any] | None = None, retries: int = 5) -> dict[str, Any]:
        payload = {"query": query, "variables": variables or {}}
        for attempt in range(retries):
            resp = self.http.post(self.url, json=payload, headers=self.headers)
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(min(2 ** attempt, 20))
                continue
            resp.raise_for_status()
            body = resp.json()
            errors = body.get("errors")
            if errors:
                if any("THROTTLED" in str(e.get("extensions", {}).get("code", "")) for e in errors):
                    time.sleep(min(2 ** attempt, 20))
                    continue
                raise ShopifyError(str(errors))
            return body["data"]
        raise ShopifyError("Shopify GraphQL: retries exhausted")

    # ---------------------------------------------------------------- ShopifyQL
    def shopifyql(self, query: str) -> tuple[list[str], list[list[Any]]]:
        gql = """
        query($q: String!) {
          shopifyqlQuery(query: $q) {
            __typename
            ... on TableResponse {
              tableData { columns { name dataType } rowData }
            }
            parseErrors { code message }
          }
        }"""
        data = self.graphql(gql, {"q": query})["shopifyqlQuery"]
        if data.get("parseErrors"):
            raise ShopifyError(f"ShopifyQL parse error: {data['parseErrors']}")
        table = data.get("tableData") or {}
        cols = [c["name"] for c in table.get("columns", [])]
        return cols, table.get("rowData", [])

    def daily_sales(self, days: int) -> list[DailySales]:
        try:
            return self._daily_sales_shopifyql(days)
        except ShopifyError:
            return self._daily_sales_from_orders(days)

    def _daily_sales_shopifyql(self, days: int) -> list[DailySales]:
        cols, rows = self.shopifyql(
            "FROM sales SHOW orders, gross_sales, discounts, sales_reversals, net_sales, total_sales, "
            f"average_order_value TIMESERIES day SINCE -{days}d UNTIL today"
        )
        idx = {c: i for i, c in enumerate(cols)}
        out: list[DailySales] = []
        for r in rows:
            out.append(
                DailySales(
                    day=date.fromisoformat(str(r[idx["day"]])[:10]),
                    orders=int(float(r[idx["orders"]] or 0)),
                    gross_sales=float(r[idx["gross_sales"]] or 0),
                    discounts=abs(float(r[idx["discounts"]] or 0)),
                    reversals=abs(float(r[idx["sales_reversals"]] or 0)),
                    net_sales=float(r[idx["net_sales"]] or 0),
                    total_sales=float(r[idx["total_sales"]] or 0),
                    aov=float(r[idx["average_order_value"]] or 0),
                )
            )
        return out

    def _daily_sales_from_orders(self, days: int) -> list[DailySales]:
        since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        buckets: dict[date, DailySales] = {}
        for o in self.iter_orders(f"created_at:>={since} status:any"):
            d = date.fromisoformat(o["createdAt"][:10])
            b = buckets.setdefault(d, DailySales(day=d, orders=0, total_sales=0.0, net_sales=0.0))
            total = float(o["currentTotalPriceSet"]["shopMoney"]["amount"])
            subtotal = float(o["currentSubtotalPriceSet"]["shopMoney"]["amount"])
            disc = float(o["currentTotalDiscountsSet"]["shopMoney"]["amount"])
            refunded = float(o["totalRefundedSet"]["shopMoney"]["amount"])
            b.orders += 1
            b.total_sales += total
            b.gross_sales += subtotal + disc
            b.discounts += disc
            b.reversals += refunded
            b.net_sales += subtotal - refunded
        for b in buckets.values():
            b.aov = b.total_sales / b.orders if b.orders else 0.0
        return [buckets[k] for k in sorted(buckets)]

    def daily_funnel(self, days: int) -> list[DailyFunnel]:
        cols, rows = self.shopifyql(
            "FROM sessions SHOW sessions, sessions_with_cart_additions, sessions_that_reached_checkout, "
            f"sessions_that_completed_checkout TIMESERIES day SINCE -{days}d UNTIL today"
        )
        idx = {c: i for i, c in enumerate(cols)}
        return [
            DailyFunnel(
                day=date.fromisoformat(str(r[idx["day"]])[:10]),
                sessions=int(float(r[idx["sessions"]] or 0)),
                atc_sessions=int(float(r[idx["sessions_with_cart_additions"]] or 0)),
                checkout_sessions=int(float(r[idx["sessions_that_reached_checkout"]] or 0)),
                completed_sessions=int(float(r[idx["sessions_that_completed_checkout"]] or 0)),
            )
            for r in rows
        ]

    def variant_sales(self, days: int) -> dict[str, dict[str, float]]:
        """Net sales + units by variant over a window, keyed by product_variant_id when available.

        ShopifyQL exposes product_variant_id / product_variant_sku dimensions; we key on
        SKU first (stable across re-created variants) and fall back to title matching.
        """
        cols, rows = self.shopifyql(
            "FROM sales SHOW net_sales, net_items_sold GROUP BY product_variant_id, product_variant_sku, "
            f"product_title, product_variant_title SINCE -{days}d UNTIL today ORDER BY net_sales DESC LIMIT 5000"
        )
        idx = {c: i for i, c in enumerate(cols)}
        out: dict[str, dict[str, float]] = {}
        for r in rows:
            vid = str(r[idx["product_variant_id"]] or "")
            sku = str(r[idx["product_variant_sku"]] or "")
            key = vid or sku or f"{r[idx['product_title']]}|{r[idx['product_variant_title']]}"
            out[key] = {
                "net_sales": float(r[idx["net_sales"]] or 0),
                "units": float(r[idx["net_items_sold"]] or 0),
                "sku": sku,
                "title": f"{r[idx['product_title']]}|{r[idx['product_variant_title']]}",
            }
        return out

    # ------------------------------------------------------------------ catalog
    VARIANT_QUERY = """
    query($first: Int!, $after: String) {
      productVariants(first: $first, after: $after, query: "product_status:active") {
        pageInfo { hasNextPage endCursor }
        edges { node {
          id sku title price compareAtPrice inventoryQuantity inventoryPolicy
          inventoryItem { tracked unitCost { amount } }
          product { id title vendor status tags }
        } }
      }
    }"""

    def iter_variants(self, page_size: int = 250) -> Iterator[Variant]:
        after = None
        while True:
            data = self.graphql(self.VARIANT_QUERY, {"first": page_size, "after": after})["productVariants"]
            for edge in data["edges"]:
                n = edge["node"]
                p = n["product"]
                cost = (n.get("inventoryItem") or {}).get("unitCost")
                yield Variant(
                    variant_id=n["id"],
                    product_id=p["id"],
                    product_title=p["title"],
                    variant_title=n.get("title") or "",
                    sku=n.get("sku") or "",
                    vendor=p.get("vendor") or "",
                    price=float(n["price"]),
                    compare_at_price=float(n["compareAtPrice"]) if n.get("compareAtPrice") else None,
                    unit_cost=float(cost["amount"]) if cost and cost.get("amount") else None,
                    inventory_quantity=int(n.get("inventoryQuantity") or 0),
                    inventory_policy=n.get("inventoryPolicy") or "DENY",
                    tracked=bool((n.get("inventoryItem") or {}).get("tracked", True)),
                    tags=list(p.get("tags") or []),
                    status=p.get("status") or "ACTIVE",
                )
            if not data["pageInfo"]["hasNextPage"]:
                break
            after = data["pageInfo"]["endCursor"]

    ORDERS_QUERY = """
    query($first: Int!, $after: String, $q: String!) {
      orders(first: $first, after: $after, query: $q, sortKey: CREATED_AT) {
        pageInfo { hasNextPage endCursor }
        edges { node {
          id name createdAt
          currentTotalPriceSet { shopMoney { amount } }
          currentSubtotalPriceSet { shopMoney { amount } }
          currentTotalDiscountsSet { shopMoney { amount } }
          totalRefundedSet { shopMoney { amount } }
        } }
      }
    }"""

    def iter_orders(self, query: str, page_size: int = 250) -> Iterator[dict[str, Any]]:
        after = None
        while True:
            data = self.graphql(self.ORDERS_QUERY, {"first": page_size, "after": after, "q": query})["orders"]
            for edge in data["edges"]:
                yield edge["node"]
            if not data["pageInfo"]["hasNextPage"]:
                break
            after = data["pageInfo"]["endCursor"]

    # ------------------------------------------------------------------ writes
    def set_inventory_policy(self, product_id: str, variant_ids: list[str], policy: str) -> None:
        gql = """
        mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            userErrors { field message }
          }
        }"""
        variants = [{"id": v, "inventoryPolicy": policy} for v in variant_ids]
        res = self.graphql(gql, {"productId": product_id, "variants": variants})["productVariantsBulkUpdate"]
        if res["userErrors"]:
            raise ShopifyError(str(res["userErrors"]))

    def set_variant_price(self, product_id: str, variant_id: str, price: float, compare_at: float | None) -> None:
        gql = """
        mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
          productVariantsBulkUpdate(productId: $productId, variants: $variants) {
            userErrors { field message }
          }
        }"""
        v: dict[str, Any] = {"id": variant_id, "price": f"{price:.2f}"}
        if compare_at is not None:
            v["compareAtPrice"] = f"{compare_at:.2f}"
        res = self.graphql(gql, {"productId": product_id, "variants": [v]})["productVariantsBulkUpdate"]
        if res["userErrors"]:
            raise ShopifyError(str(res["userErrors"]))

    def add_tags(self, resource_id: str, tags: list[str]) -> None:
        gql = """
        mutation($id: ID!, $tags: [String!]!) {
          tagsAdd(id: $id, tags: $tags) { userErrors { field message } }
        }"""
        res = self.graphql(gql, {"id": resource_id, "tags": tags})["tagsAdd"]
        if res["userErrors"]:
            raise ShopifyError(str(res["userErrors"]))

    def remove_tags(self, resource_id: str, tags: list[str]) -> None:
        gql = """
        mutation($id: ID!, $tags: [String!]!) {
          tagsRemove(id: $id, tags: $tags) { userErrors { field message } }
        }"""
        res = self.graphql(gql, {"id": resource_id, "tags": tags})["tagsRemove"]
        if res["userErrors"]:
            raise ShopifyError(str(res["userErrors"]))


def attach_sales_to_variants(variants: list[Variant], sales_90: dict, sales_30: dict, sales_14: dict, sales_prev_14: dict) -> None:
    """Join ShopifyQL variant sales onto catalog variants (by GID, then SKU, then title)."""
    def lookup(table: dict, v: Variant) -> dict | None:
        numeric_id = v.variant_id.rsplit("/", 1)[-1]
        for key in (v.variant_id, numeric_id, v.sku, f"{v.product_title}|{v.variant_title}"):
            if key and key in table:
                return table[key]
        return None

    by_sku = defaultdict(dict)
    for tbl_name, tbl in (("90", sales_90), ("30", sales_30), ("14", sales_14), ("p14", sales_prev_14)):
        for k, row in tbl.items():
            if row.get("sku"):
                by_sku[tbl_name][row["sku"]] = row

    for v in variants:
        r90 = lookup(sales_90, v) or by_sku["90"].get(v.sku)
        r30 = lookup(sales_30, v) or by_sku["30"].get(v.sku)
        r14 = lookup(sales_14, v) or by_sku["14"].get(v.sku)
        rp14 = lookup(sales_prev_14, v) or by_sku["p14"].get(v.sku)
        v.net_sales_90d = float(r90["net_sales"]) if r90 else 0.0
        v.units_90d = int(r90["units"]) if r90 else 0
        v.units_30d = int(r30["units"]) if r30 else 0
        v.units_14d = int(r14["units"]) if r14 else 0
        v.units_prev_14d = int(rp14["units"]) if rp14 else 0


_GID = re.compile(r"gid://shopify/\w+/(\d+)")


def gid_to_id(gid: str) -> str:
    m = _GID.match(gid)
    return m.group(1) if m else gid
