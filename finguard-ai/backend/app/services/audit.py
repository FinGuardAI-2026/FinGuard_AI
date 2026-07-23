from datetime import datetime
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.collections import collections

async def log_audit_action(
    db: AsyncIOMotorDatabase,
    action: str,
    performed_by: str,
    ip_address: str,
    browser: str,
    endpoint: str,
    request_id: str,
    status: str,
    details: Optional[str] = None
) -> str:
    """
    Writes an audit log entry tracking administrative or sensitive operations.
    Saves metadata including client IP, Browser, API Endpoint, and unique Request ID.
    """
    entry = {
        "action": action,
        "performed_by": performed_by,
        "ip_address": ip_address,
        "browser": browser,
        "endpoint": endpoint,
        "request_id": request_id,
        "timestamp": datetime.utcnow(),
        "status": status,  # "SUCCESS" or "FAILED"
        "details": details
    }
    print("========== AUDIT ENTRY ==========")
    print(entry)
    result = await db[collections.AUDIT_LOGS].insert_one(entry)
    print("Inserted Audit ID:", result.inserted_id)
    return str(result.inserted_id)
