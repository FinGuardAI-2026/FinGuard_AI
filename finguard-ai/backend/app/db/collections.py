class CollectionsRegistry:
    """Centralized definition of MongoDB collections used across the FinGuard AI workspace."""
    
    USERS = "users"
    TRANSACTIONS = "transactions"
    FRAUD_PREDICTIONS = "fraud_predictions"
    AUDIT_LOGS = "audit_logs"
    NOTIFICATIONS = "notifications"

# Instantiate helper registry
collections = CollectionsRegistry()
