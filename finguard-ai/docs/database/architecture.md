# FinGuard AI Database Architecture Documentation

This document describes the structure, lifecycle, and patterns used for database operations in FinGuard AI.

---

## 1. Connection Lifecycle
The MongoDB connection is managed asynchronously using the **Motor** library. The connection is tied directly to the lifecycle of the FastAPI application via ASGI event hooks.

- **Startup (`@app.on_event("startup")`)**:
  - The FastAPI app initializes the `DatabaseManager` singleton.
  - The client warmups connection pools.
  - An administrative `ping` command is executed to verify credentials and endpoint routes.
  - If the database is offline, the system logs the warning and starts in a **degraded** mode, allowing health checks and base metadata queries to function.
- **Shutdown (`@app.on_event("shutdown")`)**:
  - The connection pool closes gracefully.

---

## 2. Connection Flow
```
[ FastAPI App Startup ]
         |
         v
[ Settings Config Loader ] ---> reads MONGODB_URI & DATABASE_NAME
         |
         v
[ DatabaseManager.connect_to_database() ]
         |
         +---> Instantiates AsyncIOMotorClient
         +---> Executes admin.command("ping")
         |
    [ Connected? ]
     /        \
   Yes         No
   /            \
  v              v
Pool Ready   Log Alert & degredation status active
```

---

## 3. Singleton Database Manager
The database client connection pools are stored in the singleton wrapper class `DatabaseManager` (exposed in `app.db.connection.db_manager`). This ensures that only one database connection pool is active during the application lifetime, preventing connection leaks.

---

## 4. Repository Pattern
To maintain Clean Architecture principles, database interaction is mediated by the Repository pattern:
- **[BaseRepository](file:///c:/Users/satya/OneDrive/Documents/Desktop/LLM_Fraud/finguard-ai/backend/app/repositories/base.py)**: Houses generic CRUD actions (`insert_one`, `find_one`, `find_many`, `update_one`, `delete_one`, `count_documents`).
- **Domain Repositories** (future modules) inherit from `BaseRepository`, overriding target collection mappings and adding custom aggregate queries.

---

## 5. Dependency Injection (DI)
FastAPI routes do not import the DB connection manager singleton directly. Instead, they rely on FastAPI's Dependency Injection system:
- **`get_mongo_client`**: Injects the active Motor client.
- **`get_mongo_db`**: Injects the active database context.

This makes it easy to mock the database during unit testing by overriding the route dependencies.

---

## 6. Collection Registry
Collection names are standardized in **`CollectionsRegistry`** (exposed in `app.db.collections.collections`):
- `users`
- `transactions`
- `fraud_predictions`
- `audit_logs`
- `notifications`
