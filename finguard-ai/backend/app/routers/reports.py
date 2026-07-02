from fastapi import APIRouter, HTTPException
from app.db.connection import db_manager
from app.db.collections import collections
from app.services.gemini_service import test_gemini
from app.services.report_service import build_ai_executive_report
from datetime import datetime, timedelta

REPORT_CACHE = {
    "data": None,
    "generated_at": None
}

CACHE_DURATION = timedelta(minutes=10)

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["AI Reports"]
)


@router.get("/health")
async def reports_health():
    return {
        "status": "ok",
        "service": "AI Reports"
    }

def build_investigation_report(transaction: dict):

    shap = transaction.get("shap_summary", {})

    report = {
        "summary": "",
        "risk_assessment": {},
        "positive_drivers": [],
        "mitigating_factors": [],
        "recommendation": ""
    }

    prediction = transaction.get("prediction", "UNKNOWN")
    risk_level = transaction.get("risk_level", "Unknown")
    risk_score = transaction.get("risk_score", 0)
    confidence = transaction.get("confidence_score", 0)

    report["summary"] = (
        f"Transaction was classified as {prediction} "
        f"with {round(confidence * 100, 2)}% confidence."
    )

    report["risk_assessment"] = {
        "risk_level": risk_level,
        "risk_score": risk_score
    }

    report["positive_drivers"] = shap.get(
        "narrative_risk_drivers",
        []
    )

    report["mitigating_factors"] = shap.get(
        "narrative_mitigating_factors",
        []
    )

    if prediction == "FRAUD":
        report["recommendation"] = (
            "Block transaction and initiate manual investigation."
        )
    elif risk_level in ["High", "Critical"]:
        report["recommendation"] = (
            "Escalate transaction for analyst review."
        )
    else:
        report["recommendation"] = (
            "Approve transaction. No manual investigation required."
        )

    return report

def build_executive_report(
    total_transactions: int,
    fraud_transactions: int,
    high_risk_transactions: list,
    top_merchants: list
):

    fraud_rate = (
        round((fraud_transactions / total_transactions) * 100, 2)
        if total_transactions > 0
        else 0
    )

    if fraud_rate < 2:
        overall_risk = "LOW"
    elif fraud_rate < 5:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "HIGH"

    summary = (
        f"The system analyzed {total_transactions} transactions. "
        f"{fraud_transactions} were classified as fraudulent "
        f"({fraud_rate}% fraud rate). "
        f"The current operational risk level is {overall_risk}."
    )

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "overall_risk": overall_risk,
        "fraud_rate": fraud_rate,
        "executive_summary": summary,
        "recommendations": [
            "Continue monitoring high-risk transactions.",
            "Review transactions marked High or Critical.",
            "Perform manual investigation for suspicious activity."
        ]
    }

@router.get("/transaction/{transaction_id}")
async def transaction_report(transaction_id: str):

    db = db_manager.get_db()

    transaction = await db[collections.TRANSACTIONS].find_one(
        {
            "transaction_id": transaction_id
        }
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    investigation = build_investigation_report(transaction)
    return {
        "transaction_id": transaction["transaction_id"],
        "prediction": transaction.get("prediction"),
        "risk_score": transaction.get("risk_score"),
        "risk_level": transaction.get("risk_level"),
        "confidence_score": transaction.get("confidence_score"),
        "merchant": transaction.get("merchant_name"),
        "amount": transaction.get("amount"),
        "country": transaction.get("country"),
        "payment_method": transaction.get("payment_method"),
        "shap_summary": transaction.get("shap_summary"),
        "investigation_report": investigation
    }

@router.get("/executive")
async def executive_report():
    now = datetime.utcnow()

    if (
        REPORT_CACHE["data"] is not None
        and REPORT_CACHE["generated_at"] is not None
        and now - REPORT_CACHE["generated_at"] < CACHE_DURATION
    ):
        return REPORT_CACHE["data"]

    db = db_manager.get_db()

    total_transactions = await db[collections.TRANSACTIONS].count_documents({})

    fraud_transactions = await db[collections.TRANSACTIONS].count_documents(
        {
            "prediction": "FRAUD"
        }
    )

    high_risk_transactions = await db[
        collections.TRANSACTIONS
    ].find(
        {
            "risk_level": {
                "$in": ["High", "Critical"]
            }
        },
        {
            "_id": 0,
            "transaction_id": 1,
            "merchant_name": 1,
            "amount": 1,
            "risk_level": 1,
            "risk_score": 1
        }
    ).limit(10).to_list(10)

    pipeline = [
        {
            "$group": {
                "_id": "$merchant_name",
                "transactions": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "transactions": -1
            }
        },
        {
            "$limit": 5
        }
    ]

    merchants = await db[
        collections.TRANSACTIONS
    ].aggregate(pipeline).to_list(5)

    top_merchants = [
        {
            "merchant": m["_id"],
            "transactions": m["transactions"]
        }
        for m in merchants
    ]

    report = build_executive_report(
        total_transactions,
        fraud_transactions,
        high_risk_transactions,
        top_merchants
    )

    ai_report = await build_ai_executive_report({
        **report,
        "total_transactions": total_transactions,
        "fraud_transactions": fraud_transactions,
        "high_risk_transactions": high_risk_transactions,
        "top_merchants": top_merchants
    })


    response = {
        **report,
        "ai_report": ai_report,
        "total_transactions": total_transactions,
        "fraud_transactions": fraud_transactions,
        "high_risk_transactions": high_risk_transactions,
        "top_merchants": top_merchants
    }

    REPORT_CACHE["data"] = response
    REPORT_CACHE["generated_at"] = now

    return response

@router.get("/gemini/test")
async def gemini_test():

    response = await test_gemini()

    return {
        "response": response
    }