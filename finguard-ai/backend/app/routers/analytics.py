from fastapi import APIRouter
from app.db.connection import db_manager
from app.db.collections import collections
from datetime import datetime, timedelta
from pathlib import Path
import json

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)


@router.get("/dashboard")
async def dashboard():
    db = db_manager.get_db()

    total_transactions = await db[collections.TRANSACTIONS].count_documents({})

    now = datetime.utcnow()
    last_30_days = now - timedelta(days=30)
    previous_30_days = now - timedelta(days=60)
    current_transactions = await db[collections.TRANSACTIONS].count_documents(
        {
            "created_at": {"$gte": last_30_days}
        }
    )

    previous_transactions = await db[collections.TRANSACTIONS].count_documents(
        {
            "created_at": {
                "$gte": previous_30_days,
                "$lt": last_30_days
            }
        }
    )

    if previous_transactions == 0:
        transaction_change = 0
    else:
        transaction_change = round(
            ((current_transactions - previous_transactions)
            / previous_transactions) * 100,
            2
        )

    fraud_transactions = await db[collections.TRANSACTIONS].count_documents(
        {"prediction": "FRAUD"}
    )

    current_fraud = await db[collections.TRANSACTIONS].count_documents(
        {
            "prediction": "FRAUD",
            "created_at": {"$gte": last_30_days}
        }
    )

    previous_fraud = await db[collections.TRANSACTIONS].count_documents(
        {
            "prediction": "FRAUD",
            "created_at": {
                "$gte": previous_30_days,
                "$lt": last_30_days
            }
        }
    )

    if previous_fraud == 0:
        fraud_transaction_change = 0
    else:
        fraud_transaction_change = round(
            ((current_fraud - previous_fraud) / previous_fraud) * 100,
            2
        )

    genuine_transactions = await db[collections.TRANSACTIONS].count_documents(
        {"prediction": "GENUINE"}
    )

    fraud_percentage = (
        round((fraud_transactions / total_transactions) * 100, 2)
        if total_transactions > 0
        else 0
    )

    current_fraud_percentage = (
        (current_fraud / current_transactions) * 100
        if current_transactions > 0
        else 0
    )

    previous_fraud_percentage = (
        (previous_fraud / previous_transactions) * 100
        if previous_transactions > 0
        else 0
    )

    fraud_percentage_change = round(
        current_fraud_percentage - previous_fraud_percentage,
        2
    )

    low_risk = await db[collections.TRANSACTIONS].count_documents(
        {"risk_level": "Low"}
    )

    medium_risk = await db[collections.TRANSACTIONS].count_documents(
        {"risk_level": "Medium"}
    )

    high_risk = await db[collections.TRANSACTIONS].count_documents(
        {"risk_level": "High"}
    )

    critical_risk = await db[collections.TRANSACTIONS].count_documents(
        {"risk_level": "Critical"}
    )

    pending_cases = await db[collections.TRANSACTIONS].count_documents(
        {
            "investigation_status": "PENDING_REVIEW"
        }
    )

    return {
        "total_transactions": total_transactions,
        "fraud_transactions": fraud_transactions,
        "fraud_transaction_change": fraud_transaction_change,
        "genuine_transactions": genuine_transactions,
        "fraud_percentage": fraud_percentage,
        "fraud_percentage_change": fraud_percentage_change,
        "pending_cases": pending_cases,
        "transaction_change": transaction_change,
        "risk_distribution": {
            "low": low_risk,
            "medium": medium_risk,
            "high": high_risk,
            "critical": critical_risk
        }
    }

@router.get("/fraud-trend")
async def fraud_trend():
    db = db_manager.get_db()

    start_date = datetime.utcnow() - timedelta(days=30)

    pipeline = [
        {
            "$match": {
                "transaction_time": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%m/%d",
                        "date": "$transaction_time"
                    }
                },
                "Total": {"$sum": 1},
                "Fraud": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$prediction", "FRAUD"]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    result = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(None)

    data = []

    for row in result:
        total = row["Total"]
        fraud = row["Fraud"]

        data.append({
            "date": row["_id"],
            "Total": total,
            "Fraud": fraud,
            "FraudRate": round((fraud / total) * 100, 2) if total else 0
        })

    return data

@router.get("/risk-trend")
async def risk_trend():
    db = db_manager.get_db()

    pipeline = [
        {
            "$match": {
                "transaction_time": {
                    "$ne": None
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": "$transaction_time"
                    }
                },
                "Low": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$risk_level", "Low"]},
                            1,
                            0
                        ]
                    }
                },
                "Medium": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$risk_level", "Medium"]},
                            1,
                            0
                        ]
                    }
                },
                "High": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$risk_level", "High"]},
                            1,
                            0
                        ]
                    }
                },
                "Critical": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$risk_level", "Critical"]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    result = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(None)

    return [
        {
            "month": row["_id"],
            "Low": row["Low"],
            "Medium": row["Medium"],
            "High": row["High"],
            "Critical": row["Critical"],
        }
        for row in result
    ]

@router.get("/country-distribution")
async def country_distribution():
    db = db_manager.get_db()

    pipeline = [
        {
            "$match": {
                "country": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$country",
                "transactions": {"$sum": 1},
                "fraud": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$prediction", "FRAUD"]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$sort": {
                "transactions": -1
            }
        }
    ]

    result = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(None)

    return [
        {
            "country": row["_id"],
            "transactions": row["transactions"],
            "fraudRate": round(
                (row["fraud"] / row["transactions"]) * 100,
                2
            ) if row["transactions"] else 0
        }
        for row in result
    ]

@router.get("/payment-methods")
async def payment_methods():
    db = db_manager.get_db()

    pipeline = [
        {
            "$group": {
                "_id": "$payment_method",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "count": -1
            }
        }
    ]

    result = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(None)

    total = sum(x["count"] for x in result)

    colors = {
        "CREDIT_CARD": "#06b6d4",
        "DEBIT_CARD": "#3b82f6",
        "APPLE_PAY": "#10b981",
        "GOOGLE_PAY": "#22c55e",
        "CRYPTO": "#f59e0b",
        "ACH": "#8b5cf6",
        "WIRE": "#ef4444",
        "UPI": "#ec4899"
    }

    return [
        {
            "name": item["_id"],
            "count": item["count"],
            "value": round(item["count"] * 100 / total, 2) if total else 0,
            "color": colors.get(item["_id"], "#64748b")
        }
        for item in result
    ]

@router.get("/merchant-categories")
async def merchant_categories():
    db = db_manager.get_db()

    pipeline = [
        {
            "$group": {
                "_id": "$merchant_category",
                "genuine": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$prediction", "GENUINE"]},
                            1,
                            0
                        ]
                    }
                },
                "fraud": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$prediction", "FRAUD"]},
                            1,
                            0
                        ]
                    }
                }
            }
        },
        {
            "$sort": {
                "genuine": -1
            }
        }
    ]

    result = await db[collections.TRANSACTIONS].aggregate(pipeline).to_list(None)

    return [
        {
            "category": row["_id"],
            "genuine": row["genuine"],
            "fraud": row["fraud"]
        }
        for row in result
    ]

@router.get("/live-alerts")
async def live_alerts():
    db = db_manager.get_db()

    alerts = await db[collections.TRANSACTIONS].find(
        {
            "risk_score": {"$gte": 1}
        },
        {
            "_id": 0,
            "transaction_id": 1,
            "merchant_name": 1,
            "amount": 1,
            "risk_score": 1,
            "risk_level": 1,
            "prediction": 1,
            "transaction_time": 1
        }
    ).sort("transaction_time", -1).limit(10).to_list(10)

    return alerts

@router.get("/shap/global")
async def shap_global():
    db = db_manager.get_db()

    docs = await db[collections.TRANSACTIONS].find(
        {
            "shap_summary": {"$ne": None}
        },
        {
            "_id": 0,
            "shap_summary": 1
        }
    ).to_list(None)

    feature_scores = {}

    for doc in docs:

        shap = doc["shap_summary"]

        drivers = (
            shap["positive_drivers"] +
            shap["negative_drivers"]
        )

        for driver in drivers:

            feature = driver["feature"]
            impact = abs(driver["impact"])

            feature_scores.setdefault(feature, [])
            feature_scores[feature].append(impact)

    result = []

    for feature, impacts in feature_scores.items():

        avg_impact = sum(impacts) / len(impacts)

        result.append({
            "feature": feature,
            "importance": round(avg_impact, 6)
        })

    result.sort(
        key=lambda x: x["importance"],
        reverse=True
    )

    return result[:10]

@router.get("/model-performance")
async def model_performance():

    leaderboard_path = (
        Path(__file__).resolve().parents[3]
        / "ml_pipeline"
        / "reports"
        / "leaderboard.json"
    )
        
    print("Current Working Directory:", Path.cwd())
    print("Looking for:", leaderboard_path.resolve())
    print("Exists:", leaderboard_path.exists())


    if not leaderboard_path.exists():
        return []

    with open(leaderboard_path, "r") as f:
        data = json.load(f)

    return data