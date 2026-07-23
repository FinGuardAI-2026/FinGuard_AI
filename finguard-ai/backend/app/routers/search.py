"""
backend/app/routers/search.py
──────────────────────────────
Command Palette search API endpoint.

Provides real-time, prefix-filtered, and ranked search across:
  - Users (investigators)
  - Transactions
  - Predictions
  - Reports
  - Merchants
  - Countries
"""
import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_user
from app.db.connection import db_manager
from app.db.collections import collections

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search"],
)

# ── Relevancy Ranking Helpers ──────────────────────────────────────────────────

def rank_string_match(target: str, query: str) -> int:
    """
    Computes matching weight:
      0 = Exact match
      1 = Starts with
      2 = Contains
      3 = No match
    """
    t_low = target.lower()
    q_low = query.lower()
    if not q_low or not t_low:
        return 3
    if t_low == q_low:
        return 0
    if t_low.startswith(q_low):
        return 1
    if q_low in t_low:
        return 2
    return 3


def sort_by_rank(items: List[Dict[str, Any]], rank_fn) -> List[Dict[str, Any]]:
    """Sorts items in-place by rank value ascending (lowest rank first)."""
    return sorted(items, key=rank_fn)


# ── Search Route Handler ────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="Command Palette Search",
    description=(
        "Executes dynamic scoped search with support for filter prefixes "
        "(user:, merchant:, country:, risk:) and sorts results by match ranking. "
        "Also accepts explicit filter query params: ?user=, ?merchant=, ?country=, ?risk="
    ),
)
async def global_search(
    q: str = Query(""),
    user: Optional[str] = Query(None),
    merchant: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    db = db_manager.get_db()

    # 1. Determine active category filter and search term.
    # Explicit query params take precedence over inline colon-prefix syntax.
    category_filter: Optional[str] = None
    clean_q = q.strip()

    if user:
        category_filter = "user"
        clean_q = user.strip() or clean_q
    elif merchant:
        category_filter = "merchant"
        clean_q = merchant.strip() or clean_q
    elif country:
        category_filter = "country"
        clean_q = country.strip() or clean_q
    elif risk:
        category_filter = "risk"
        clean_q = risk.strip() or clean_q
    elif ":" in clean_q:
        # Inline colon-prefix fallback (e.g.  "user:alice")
        parts = clean_q.split(":", 1)
        prefix = parts[0].lower().strip()
        val = parts[1].strip()
        if prefix in ("user", "merchant", "country", "risk"):
            category_filter = prefix
            clean_q = val

    if not clean_q:
        return {
            "users": [],
            "transactions": [],
            "predictions": [],
            "reports": [],
            "merchants": [],
            "countries": [],
        }


    # Helper: Convert BSON object ID to string for responses
    def serialize_doc(doc):
        out = dict(doc)
        if "_id" in out:
            out["id"] = str(out.pop("_id"))
        return out

    # ── Task Definitions ──

    async def search_users() -> List[Dict[str, Any]]:
        if category_filter and category_filter != "user":
            return []
        query = {
            "$or": [
                {"full_name": {"$regex": clean_q, "$options": "i"}},
                {"email": {"$regex": clean_q, "$options": "i"}},
            ]
        }
        cursor = db[collections.USERS].find(query).limit(10)
        docs = [serialize_doc(d) for d in await cursor.to_list(length=10)]
        
        # Rank sorting
        def rank_fn(u):
            return min(
                rank_string_match(u.get("full_name", ""), clean_q),
                rank_string_match(u.get("email", ""), clean_q),
            )
        return sort_by_rank(docs, rank_fn)

    async def search_transactions() -> List[Dict[str, Any]]:
        # Filter exclusions
        if category_filter and category_filter not in ("merchant", "country"):
            return []
            
        or_conditions = [
            {"transaction_id": {"$regex": clean_q, "$options": "i"}},
            {"merchant_name": {"$regex": clean_q, "$options": "i"}},
            {"merchant_category": {"$regex": clean_q, "$options": "i"}},
            {"payment_method": {"$regex": clean_q, "$options": "i"}},
        ]
        
        # Scoped overrides
        if category_filter == "merchant":
            or_conditions = [{"merchant_name": {"$regex": clean_q, "$options": "i"}}]
        elif category_filter == "country":
            or_conditions = [{"country": {"$regex": f"^{clean_q}", "$options": "i"}}]

        try:
            val = float(clean_q)
            or_conditions.append({"amount": val})
        except ValueError:
            pass

        query = {"$or": or_conditions}
        cursor = db[collections.TRANSACTIONS].find(query).limit(15)
        docs = [serialize_doc(d) for d in await cursor.to_list(length=15)]

        def rank_fn(t):
            return min(
                rank_string_match(t.get("transaction_id", ""), clean_q),
                rank_string_match(t.get("merchant_name", ""), clean_q),
            )
        return sort_by_rank(docs, rank_fn)

    async def search_predictions() -> List[Dict[str, Any]]:
        if category_filter and category_filter != "risk":
            return []
            
        query: Dict[str, Any] = {}
        if category_filter == "risk":
            query = {"risk_level": {"$regex": f"^{clean_q}", "$options": "i"}}
        else:
            query = {
                "$or": [
                    {"prediction": {"$regex": f"^{clean_q}", "$options": "i"}},
                    {"risk_level": {"$regex": f"^{clean_q}", "$options": "i"}},
                    {"transaction_id": {"$regex": clean_q, "$options": "i"}},
                ]
            }

        cursor = db[collections.TRANSACTIONS].find(query).limit(10)
        docs = [serialize_doc(d) for d in await cursor.to_list(length=10)]

        def rank_fn(p):
            return min(
                rank_string_match(p.get("prediction", ""), clean_q),
                rank_string_match(p.get("risk_level", ""), clean_q),
                rank_string_match(p.get("transaction_id", ""), clean_q),
            )
        return sort_by_rank(docs, rank_fn)

    async def search_reports() -> List[Dict[str, Any]]:
        # Reports are built dynamically from transactions.
        # Find transactions matching ID with an existing LLM report cache or shap summary.
        if category_filter and category_filter not in ("merchant", "country"):
            return []

        query = {
            "llm_report": {"$exists": True, "$ne": None},
            "$or": [
                {"transaction_id": {"$regex": clean_q, "$options": "i"}},
                {"merchant_name": {"$regex": clean_q, "$options": "i"}},
            ],
        }
        cursor = db[collections.TRANSACTIONS].find(query).limit(10)
        docs = [serialize_doc(d) for d in await cursor.to_list(length=10)]

        def rank_fn(r):
            return min(
                rank_string_match(r.get("transaction_id", ""), clean_q),
                rank_string_match(r.get("merchant_name", ""), clean_q),
            )
        return sort_by_rank(docs, rank_fn)

    async def search_merchants() -> List[Dict[str, Any]]:
        if category_filter and category_filter != "merchant":
            return []
            
        pipeline = [
            {"$match": {"merchant_name": {"$regex": clean_q, "$options": "i"}}},
            {
                "$group": {
                    "_id": "$merchant_name",
                    "category": {"$first": "$merchant_category"},
                    "transaction_count": {"$sum": 1},
                    "total_volume": {"$sum": "$amount"},
                }
            },
            {"$limit": 5},
        ]
        results = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(5)
        
        # Format results
        out = []
        for r in results:
            out.append({
                "name": r["_id"],
                "category": r.get("category", "General"),
                "transaction_count": r.get("transaction_count", 0),
                "total_volume": round(r.get("total_volume", 0.0), 2),
            })

        def rank_fn(m):
            return rank_string_match(m["name"], clean_q)
        return sort_by_rank(out, rank_fn)

    async def search_countries() -> List[Dict[str, Any]]:
        if category_filter and category_filter != "country":
            return []

        pipeline = [
            {"$match": {"country": {"$regex": f"^{clean_q}", "$options": "i"}}},
            {
                "$group": {
                    "_id": "$country",
                    "transaction_count": {"$sum": 1},
                    "total_volume": {"$sum": "$amount"},
                }
            },
            {"$limit": 5},
        ]
        results = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(5)
        
        out = []
        for r in results:
            out.append({
                "code": r["_id"],
                "transaction_count": r.get("transaction_count", 0),
                "total_volume": round(r.get("total_volume", 0.0), 2),
            })

        def rank_fn(c):
            return rank_string_match(c["code"], clean_q)
        return sort_by_rank(out, rank_fn)

    # ── Gather Parallel Execution ──
    results = await asyncio.gather(
        search_users(),
        search_transactions(),
        search_predictions(),
        search_reports(),
        search_merchants(),
        search_countries(),
    )

    return {
        "users": results[0],
        "transactions": results[1],
        "predictions": results[2],
        "reports": results[3],
        "merchants": results[4],
        "countries": results[5],
    }
